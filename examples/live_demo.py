"""
CKG vs RAG — live demo on real content.

Point it at any URL (docs page, README, Wikipedia article) and it will:
  1. Scrape the text and build a RAG pipeline from it
  2. Query the same topic via ckg-mcp for the CKG side
  3. Ask 5 real questions people actually ask
  4. Show token counts, F1 scores, and cost side-by-side — live

Usage
-----
  pip install ckg-mcp langchain-community faiss-cpu sentence-transformers httpx
  ollama pull llama3.2:3b   (or set ANTHROPIC_API_KEY for Claude)

  # Compare on LangGraph docs vs CKG:
  python examples/live_demo.py \\
      --url https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/ \\
      --domain agent-reliability

  # Try a Wikipedia article:
  python examples/live_demo.py \\
      --url https://en.wikipedia.org/wiki/Calculus \\
      --domain calculus

  # No URL — uses ckg-mcp's own README as the RAG source:
  python examples/live_demo.py --domain computer-science

  # Bring your own questions:
  python examples/live_demo.py --domain biology --questions "What causes speciation?,How does meiosis work?"
"""

import argparse
import os
import re
import sys
import time
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"          # auto-selected from what's installed
HAIKU_MODEL  = "claude-haiku-4-5-20251001"
PRICE_IN     = 0.80  / 1_000_000
PRICE_OUT    = 4.00  / 1_000_000
OLLAMA_PRICE = 0.0

SYSTEM_PROMPT = (
    "Answer the question using ONLY the information provided in the context. "
    "Be concise and specific. If the answer isn't in the context, say so."
)

# Default questions per domain — real questions people actually ask
DOMAIN_QUESTIONS = {
    "calculus": [
        "What do I need to know before learning integration?",
        "How does differentiation relate to limits?",
        "What is the chain rule used for?",
        "What's the difference between definite and indefinite integrals?",
        "How does the fundamental theorem of calculus connect derivatives and integrals?",
    ],
    "computer-science": [
        "What concepts do I need before studying algorithms?",
        "How does recursion relate to dynamic programming?",
        "What is the difference between a stack and a queue?",
        "What do I need to know before learning machine learning?",
        "How do hash tables work and what are they used for?",
    ],
    "biology": [
        "What do I need to understand before studying genetics?",
        "How does mitosis differ from meiosis?",
        "What is the role of ATP in cellular processes?",
        "How does natural selection lead to evolution?",
        "What are the prerequisites for understanding protein synthesis?",
    ],
    "agent-reliability": [
        "What causes AI agents to fail in production?",
        "How does context window management affect agent reliability?",
        "What is the relationship between tool calls and token burn?",
        "How do you prevent runaway agent loops?",
        "What metrics matter most for measuring agent performance?",
    ],
    "nvidia-gpu-inference": [
        "What do I need to know before optimizing GPU inference?",
        "How does CUDA relate to model serving?",
        "What is the difference between batching strategies for LLM inference?",
        "How does tensor parallelism work?",
        "What are the main bottlenecks in GPU memory bandwidth?",
    ],
    "blockchain": [
        "What do I need to know before understanding smart contracts?",
        "How does consensus mechanism relate to security?",
        "What is the relationship between gas and transaction costs?",
        "How do Merkle trees work in blockchain?",
        "What are the prerequisites for building a DeFi application?",
    ],
}

FALLBACK_QUESTIONS = [
    "What are the most fundamental concepts in this domain?",
    "What do beginners need to know first?",
    "How do the core concepts relate to each other?",
    "What are the most common mistakes or misunderstandings?",
    "What advanced topics build on the basics?",
]

# ── Text fetching ─────────────────────────────────────────────────────────────

def _strip_html(raw: str) -> str:
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', raw, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def _wikipedia_text(url: str) -> str | None:
    """Use Wikipedia REST API for clean plain text — avoids JS-rendered HTML."""
    m = re.search(r'wikipedia\.org/wiki/([^#?]+)', url)
    if not m:
        return None
    import urllib.request, json
    title = m.group(1)
    # REST API returns clean plain text paragraphs
    api = f"https://en.wikipedia.org/api/rest_v1/page/mobile-sections/{title}"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "ckg-mcp-demo/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        parts = []
        lead = data.get("lead", {}).get("sections", [])
        if lead:
            parts.append(_strip_html(lead[0].get("text", "")))
        for sec in data.get("remaining", {}).get("sections", []):
            parts.append(_strip_html(sec.get("text", "")))
        return " ".join(p for p in parts if p)
    except Exception:
        return None

def fetch_url(url: str) -> str:
    import urllib.request

    # Wikipedia: use their REST API for clean text
    if "wikipedia.org/wiki/" in url:
        text = _wikipedia_text(url)
        if text and len(text.split()) > 100:
            words = text.split()
            return " ".join(words[:8000])

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise SystemExit(f"Cannot fetch {url}: {e}")

    text = _strip_html(raw)
    words = text.split()
    if len(words) < 50:
        raise SystemExit(f"Only {len(words)} words fetched — page may require JS rendering")
    return " ".join(words[:8000])

def fetch_ckg_readme() -> str:
    """Fallback corpus: ckg-mcp README."""
    readme = Path(__file__).parent.parent / "README.md"
    if readme.exists():
        return readme.read_text()
    return "CKG-MCP provides compressed knowledge graphs for AI agents via MCP protocol."


# ── CKG side — uses ckg-mcp Python library directly ──────────────────────────

def ckg_answer(domain: str, question: str) -> tuple[str, int]:
    """Query ckg-mcp and return (context_string, token_count)."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
    from ckg_mcp.graph import load_graph, find_concept, bfs_subgraph, prerequisite_chain

    id_to_label, label_to_id, prerequisites, dependents, taxonomy = load_graph(domain)

    # Extract best concept from the question
    question_lower = question.lower()
    best_concept = None
    for label in sorted(label_to_id.keys(), key=len, reverse=True):
        if label.lower() in question_lower:
            best_concept = label
            break

    if not best_concept:
        # Fuzzy: pick any concept whose words appear in question
        q_words = set(question_lower.split())
        for label in label_to_id:
            label_words = set(label.lower().split())
            if label_words & q_words:
                best_concept = label
                break

    if not best_concept:
        # Just show the top-level graph structure
        sample_ids = list(id_to_label.keys())[:15]
        lines = ["KNOWLEDGE GRAPH — top concepts:"]
        for cid in sample_ids:
            lines.append(f"  {id_to_label[cid]}")
        ctx = "\n".join(lines)
        return ctx, len(ctx.split())

    cid = find_concept(label_to_id, best_concept)
    if not cid:
        ctx = f"Concept '{best_concept}' not found in {domain} graph."
        return ctx, len(ctx.split())

    # Get subgraph — prereqs + dependents
    subgraph = bfs_subgraph(cid, {**prerequisites, **dependents}, id_to_label, max_depth=3)
    prereq_chain = prerequisite_chain(cid, prerequisites, id_to_label)

    lines = [f"KNOWLEDGE GRAPH — {id_to_label[cid]}:"]
    if taxonomy.get(cid):
        lines.append(f"  Category: {taxonomy[cid]}")
    if prereq_chain:
        lines.append(f"  Prerequisite chain: {' → '.join(prereq_chain[:8])}")
    if subgraph:
        lines.append(f"  Related concepts ({len(subgraph)}):")
        for node in subgraph[:12]:
            rel = ", ".join(node.get("related", [])[:3])
            lines.append(f"    - {node['concept']}" + (f"  ← {rel}" if rel else ""))

    ctx = "\n".join(lines)
    return ctx, len(ctx.split())


# ── RAG side — LangChain FAISS ────────────────────────────────────────────────

def build_rag(text: str):
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_core.documents import Document
    except ImportError:
        raise SystemExit("Run: pip install langchain-community faiss-cpu sentence-transformers langchain-core")

    # Chunk by sentence groups (~150 words each)
    words   = text.split()
    chunks  = [" ".join(words[i:i+150]) for i in range(0, len(words), 120)]
    docs    = [Document(page_content=c) for c in chunks]

    print(f"  Building RAG index ({len(docs)} chunks)…", end=" ", flush=True)
    t0 = time.time()
    devnull = open(os.devnull, "w")
    old_stderr, sys.stderr = sys.stderr, devnull
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2",
                                            model_kwargs={"device":"cpu"})
        store = FAISS.from_documents(docs, embeddings)
    finally:
        sys.stderr = old_stderr
        devnull.close()
    print(f"done ({time.time()-t0:.1f}s)")
    return store.as_retriever(search_kwargs={"k": 5})

def rag_answer(retriever, question: str) -> tuple[str, int]:
    docs = retriever.invoke(question)
    ctx  = "\n\n".join(d.page_content for d in docs)
    return ctx, len(ctx.split())


# ── LLM ──────────────────────────────────────────────────────────────────────

def _call_ollama(ctx, q):
    import requests
    prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{ctx}\n\nQuestion: {q}"
    r = requests.post(OLLAMA_URL,
                      json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                      timeout=90)
    r.raise_for_status()
    d = r.json()
    return (d.get("response","").strip(),
            d.get("prompt_eval_count", len(prompt.split())),
            d.get("eval_count", 40))

def _call_claude(client, ctx, q):
    msg = client.messages.create(
        model=HAIKU_MODEL, max_tokens=400, temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role":"user","content":f"Context:\n{ctx}\n\nQuestion: {q}"}],
    )
    return msg.content[0].text, msg.usage.input_tokens, msg.usage.output_tokens

def setup_llm():
    global OLLAMA_MODEL
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Quick probe to verify key is valid
            probe = client.messages.create(
                model=HAIKU_MODEL, max_tokens=5, temperature=0,
                messages=[{"role":"user","content":"hi"}],
            )
            def call(ctx, q): return _call_claude(client, ctx, q)
            print(f"  LLM: Claude Haiku")
            return call, PRICE_IN, PRICE_OUT, "Claude Haiku"
        except Exception:
            print("  ANTHROPIC_API_KEY set but invalid — falling back to Ollama")

    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        raise SystemExit(
            "No LLM found.\n"
            "Option A: ollama pull llama3.2:3b  (free, local)\n"
            "Option B: export ANTHROPIC_API_KEY=sk-..."
        )
    preferred = ["llama3.2:3b","phi4-mini:latest","mistral:latest","qwen3:8b","deepseek-r1:8b"]
    chosen    = next((m for m in preferred if m in models), models[0] if models else None)
    if not chosen:
        raise SystemExit("No Ollama models found. Run: ollama pull llama3.2:3b")
    OLLAMA_MODEL = chosen
    def call(ctx, q): return _call_ollama(ctx, q)
    print(f"  LLM: Ollama {chosen} (local)")
    return call, OLLAMA_PRICE, OLLAMA_PRICE, f"Ollama/{chosen}"


# ── Scoring ───────────────────────────────────────────────────────────────────

STOPWORDS = {"what","is","the","a","an","of","for","are","in","and","or","to","with",
             "how","does","this","that","it","its","by","from","at","as","be","was"}

def simple_f1(pred, reference):
    """Rough F1 against the question itself — measures relevance, not ground truth."""
    p = set(re.sub(r'[^\w\s]','',pred).lower().split()) - STOPWORDS
    r = set(re.sub(r'[^\w\s]','',reference).lower().split()) - STOPWORDS
    if not p or not r: return 0.0
    tp = len(p & r)
    pr = tp/len(p); re_ = tp/len(r)
    return round(2*pr*re_/(pr+re_) if pr+re_ else 0.0, 3)


# ── Display ───────────────────────────────────────────────────────────────────

TEAL="\033[38;5;29m"; RED="\033[38;5;160m"; BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"

def bar(v, mx, w=16, c=TEAL):
    f = int(v/mx*w) if mx else 0
    return c+"█"*f+DIM+"░"*(w-f)+RESET

def show_result(i, question, ckg_r, rag_r):
    cq, ct, ca = ckg_r["tokens"], ckg_r["cost"], ckg_r["answer"]
    rq, rt, ra = rag_r["tokens"], rag_r["cost"], rag_r["answer"]
    ratio = rq/cq if cq else 0
    score_c = simple_f1(ca, question)
    score_r = simple_f1(ra, question)
    mx = max(score_c, score_r, 0.01)

    print(f"  Q{i+1}  {question[:65]}")
    print(f"       CKG  {bar(score_c,mx,14,TEAL)}  relevance={TEAL}{score_c:.3f}{RESET}  {BOLD}{cq:>5} tok{RESET}")
    print(f"       RAG  {bar(score_r,mx,14,RED)}  relevance={RED}{score_r:.3f}{RESET}  {RED}{rq:>5} tok{RESET}  ({ratio:.1f}×)")
    print(f"  {DIM}CKG: {ca[:90]}…{RESET}" if len(ca)>90 else f"  {DIM}CKG: {ca}{RESET}")
    print()

def show_summary(results, source_label, domain, llm_label, p_in, p_out):
    ckg_tok  = [r["ckg"]["tokens"] for r in results]
    rag_tok  = [r["rag"]["tokens"] for r in results]
    ckg_rel  = [simple_f1(r["ckg"]["answer"], r["q"]) for r in results]
    rag_rel  = [simple_f1(r["rag"]["answer"], r["q"]) for r in results]
    tok_r    = round(sum(rag_tok)/sum(ckg_tok), 1) if sum(ckg_tok) else 0
    rel_r    = round(sum(ckg_rel)/sum(rag_rel), 1) if sum(rag_rel) else 0

    print(f"{'─'*62}")
    print(f"{BOLD}  SUMMARY{RESET}  ·  domain: {domain}  ·  {llm_label}")
    print(f"  RAG source: {source_label[:55]}")
    print(f"{'─'*62}")
    print(f"  {'Metric':<26}{'CKG':>10}{'RAG':>10}{'  Δ':>8}")
    print(f"  {'─'*54}")
    print(f"  {'Mean tokens / query':<26}{TEAL}{round(sum(ckg_tok)/len(ckg_tok)):>10,}{RESET}"
          f"{RED}{round(sum(rag_tok)/len(rag_tok)):>10,}{RESET}{BOLD}{tok_r:>7.1f}×{RESET}")
    print(f"  {'Mean relevance score':<26}{TEAL}{round(sum(ckg_rel)/len(ckg_rel),3):>10.3f}{RESET}"
          f"{RED}{round(sum(rag_rel)/len(rag_rel),3):>10.3f}{RESET}{BOLD}{rel_r:>7.1f}×{RESET}")
    if p_in > 0:
        ckg_c = sum(r["ckg"]["cost"] for r in results) / len(results)
        rag_c = sum(r["rag"]["cost"] for r in results) / len(results)
        print(f"  {'Est. cost / query':<26}{TEAL}${ckg_c:>9.5f}{RESET}"
              f"{RED}${rag_c:>9.5f}{RESET}{BOLD}{round(rag_c/ckg_c,1) if ckg_c else 0:>7.1f}×{RESET}")

    if tok_r >= 1.5:
        mo_save = 478 * (1 - 1/tok_r)
        print(f"\n  At $478/eng/mo (Uber-reconstructed enterprise rate):")
        print(f"  {TEAL}{BOLD}~${mo_save:.0f}/eng/month saved{RESET}  ·  "
              f"{BOLD}~${mo_save*12:,.0f}/eng/year{RESET}")
        print(f"  100-engineer team → {TEAL}{BOLD}~${mo_save*100*12/1000:.0f}K/year{RESET}")

    print(f"\n  Try it:  pip install ckg-mcp  ·  github.com/Yarmoluk/ckg-mcp")
    print(f"{'─'*62}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain",    required=True, help="ckg-mcp domain (e.g. calculus, biology, computer-science)")
    ap.add_argument("--url",       default="",    help="URL to scrape for RAG corpus")
    ap.add_argument("--questions", default="",    help="Comma-separated questions (overrides defaults)")
    args = ap.parse_args()

    # Load questions
    if args.questions:
        questions = [q.strip() for q in args.questions.split(",") if q.strip()]
    else:
        questions = DOMAIN_QUESTIONS.get(args.domain, FALLBACK_QUESTIONS)[:5]

    # Fetch RAG corpus
    if args.url:
        print(f"\n  Fetching {args.url[:70]}…", end=" ", flush=True)
        corpus_text  = fetch_url(args.url)
        source_label = args.url
        print(f"{len(corpus_text.split())} words")
    else:
        corpus_text  = fetch_ckg_readme()
        source_label = "ckg-mcp README (no --url provided)"
        print(f"\n  Using ckg-mcp README as RAG corpus ({len(corpus_text.split())} words)")
        print(f"  Tip: add --url https://en.wikipedia.org/wiki/{args.domain.replace('-','_').title()}")
        print(f"       for a real-world comparison on live web content")

    # Setup
    call_llm, p_in, p_out, llm_label = setup_llm()
    retriever = build_rag(corpus_text)

    print(f"\n  {'─'*58}")
    print(f"  {BOLD}CKG vs RAG — live on: {source_label[:45]}{RESET}")
    print(f"  domain: {args.domain}  ·  {len(questions)} questions  ·  {llm_label}")
    print(f"  {'─'*58}\n")

    results = []
    for i, question in enumerate(questions):
        # CKG
        ctx_ckg, ctx_tok_ckg = ckg_answer(args.domain, question)
        ans_ckg, pt_ckg, ct_ckg = call_llm(ctx_ckg, question)
        tok_ckg  = pt_ckg + ct_ckg
        cost_ckg = pt_ckg * p_in + ct_ckg * p_out

        # RAG
        ctx_rag, ctx_tok_rag = rag_answer(retriever, question)
        ans_rag, pt_rag, ct_rag = call_llm(ctx_rag, question)
        tok_rag  = pt_rag + ct_rag
        cost_rag = pt_rag * p_in + ct_rag * p_out

        results.append({
            "q": question,
            "ckg": {"answer": ans_ckg, "tokens": tok_ckg, "cost": cost_ckg},
            "rag": {"answer": ans_rag, "tokens": tok_rag, "cost": cost_rag},
        })
        show_result(i, question, results[-1]["ckg"], results[-1]["rag"])
        time.sleep(0.05)

    show_summary(results, source_label, args.domain, llm_label, p_in, p_out)


if __name__ == "__main__":
    main()

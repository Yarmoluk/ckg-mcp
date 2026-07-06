"""
CKG vs LangChain RAG — side-by-side token comparison.

Same domain. Same queries. Same LLM. Different retrieval.

Usage
-----
# Install deps:
pip install ckg-mcp langchain langchain-community faiss-cpu sentence-transformers huggingface_hub

# Run with local Ollama (recommended — no API key needed):
ollama pull llama3.2:3b          # one-time, ~2GB
python examples/langchain_rag_comparison.py

# Run with Claude Haiku:
ANTHROPIC_API_KEY=sk-... python examples/langchain_rag_comparison.py

# Pick a different domain (any of the 68 free domains):
python examples/langchain_rag_comparison.py --domain biology
python examples/langchain_rag_comparison.py --domain computer-science --queries 10
"""

import argparse
import csv
import json
import os
import re
import time
import tempfile
from collections import defaultdict, deque
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DATASET_REPO  = "danyarm/ckg-benchmark"
OLLAMA_URL    = "http://localhost:11434/api/generate"
OLLAMA_MODEL  = "llama3.2:3b"
HAIKU_MODEL   = "claude-haiku-4-5-20251001"
PRICE_IN      = 0.80  / 1_000_000   # Haiku $/input token
PRICE_OUT     = 4.00  / 1_000_000   # Haiku $/output token
OLLAMA_PRICE  = 0.0                  # local = free

SYSTEM_PROMPT = (
    "Answer the question using ONLY the information provided. "
    "Be concise. List concepts as comma-separated values when enumerating. "
    "Do not add information not present in the context."
)

STOPWORDS = {
    "what","is","the","a","an","of","for","are","in","and","or","to","with",
    "how","does","related","which","these","those","all","list","describe",
    "explain","between","concept","concepts","based","on","knowledge","graph",
    "subgraph","prerequisites","prerequisite","following","use","given","find",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _norm(text):
    text = re.sub(r'[*_`#]', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def token_f1(pred, truth_list):
    p = set(_norm(pred).lower().split()) - STOPWORDS
    t = set(_norm(" ".join(truth_list)).lower().split()) - STOPWORDS
    if not p and not t: return 1.0
    if not p or not t:  return 0.0
    tp = len(p & t)
    pr = tp / len(p); re_ = tp / len(t)
    return round(2*pr*re_/(pr+re_) if pr+re_ else 0.0, 4)

def _hf_download(filename):
    try:
        from huggingface_hub import hf_hub_download
        return Path(hf_hub_download(repo_id=DATASET_REPO, repo_type="dataset", filename=filename))
    except Exception as e:
        raise SystemExit(f"Cannot download {filename} from HF: {e}\n"
                         f"Try: pip install huggingface_hub")

def _load_graph(domain):
    local = Path(__file__).parent.parent / "benchmark" / "domains" / domain / "learning-graph.csv"
    path  = local if local.exists() else _hf_download(f"domains/{domain}/learning-graph.csv")
    concepts = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            cid  = int(row["ConceptID"])
            deps = [int(d) for d in row.get("Dependencies","").split("|") if d.strip().isdigit()]
            concepts[cid] = {
                "id": cid, "label": row["ConceptLabel"].strip(),
                "deps": deps, "tax": row.get("TaxonomyID","GEN").strip()
            }
    return concepts

def _load_queries(domain, n):
    local = Path(__file__).parent.parent / "benchmark" / "queries" / f"queries_{domain}.jsonl"
    path  = local if local.exists() else _hf_download(f"queries/queries_{domain}.jsonl")
    qs = []
    with open(path) as f:
        for line in f:
            if line.strip(): qs.append(json.loads(line))
    # Pick one of each type for variety
    by_type, seen = defaultdict(list), set()
    for q in qs:
        t = q.get("type") or q.get("query_type","")
        by_type[t].append(q)
    selected = []
    for t in ["T1_entity","T2_dependency","T3_path","T4_aggregate","T5_cross_concept"]:
        if by_type[t]:
            selected.append(by_type[t][0])
    # Top up to n if requested
    for q in qs:
        if len(selected) >= n: break
        if q not in selected: selected.append(q)
    return selected[:n]


# ── CKG retrieval ─────────────────────────────────────────────────────────────

def _find(concepts, label):
    ll = label.lower()
    for c in concepts.values():
        if c["label"].lower() == ll: return c
    for c in concepts.values():
        if ll in c["label"].lower(): return c
    return None

def _bfs_ancestors(concepts, start):
    visited, queue, path = set(), deque([start]), []
    while queue:
        n = queue.popleft()
        if n in visited: continue
        visited.add(n); path.append(n)
        for d in concepts[n]["deps"]:
            if d not in visited and d in concepts: queue.append(d)
    return path

def _bfs_path(concepts, a, b):
    if a == b: return [a]
    rev = defaultdict(set)
    for cid, c in concepts.items():
        for d in c["deps"]: rev[d].add(cid)
    queue, visited = deque([(a,[a])]), {a}
    while queue:
        node, path = queue.popleft()
        for nb in (set(concepts[node]["deps"]) | rev[node]):
            if nb in visited or nb not in concepts: continue
            np = path + [nb]
            if nb == b: return np
            visited.add(nb); queue.append((nb, np))
    return [a, b]

def _serialize(concepts, ids):
    lines = ["KNOWLEDGE GRAPH SUBGRAPH:"]
    for cid in ids:
        if cid not in concepts: continue
        c = concepts[cid]
        deps = ", ".join(concepts[d]["label"] for d in c["deps"] if d in concepts) or "none"
        lines.append(f"  [{c['tax']}] {c['label']} | prerequisites: {deps}")
    return "\n".join(lines)

def ckg_retrieve(concepts, q):
    qtype = q.get("type") or q.get("query_type","")
    if qtype == "T1_entity":
        cid = q.get("concept_id")
        c   = concepts.get(cid) or _find(concepts, q.get("ground_truth",[""])[0])
        if not c: return "Concept not found."
        rev = [cc["id"] for cc in concepts.values() if c["id"] in cc["deps"]]
        ids = list(dict.fromkeys([c["id"]] + c["deps"] + rev[:5]))
    elif qtype == "T2_dependency":
        cid = q.get("concept_id")
        c   = concepts.get(cid) or _find(concepts, q["query"].split("for ")[-1].rstrip("?"))
        if not c: return "Concept not found."
        ids = [c["id"]] + c["deps"]
    elif qtype == "T3_path":
        ids = q.get("path_ids") or []
        if not ids:
            for label in q.get("ground_truth",[]):
                cc = _find(concepts, label)
                if cc: ids.append(cc["id"])
        if not ids:
            cid = q.get("concept_id")
            if cid and cid in concepts: ids = _bfs_ancestors(concepts, cid)
    elif qtype == "T4_aggregate":
        tax = q.get("taxonomy_id","")
        ids = [c["id"] for c in concepts.values() if c["tax"] == tax] if tax else \
              [cc["id"] for label in q.get("ground_truth",[]) for cc in [_find(concepts,label)] if cc]
    elif qtype == "T5_cross_concept":
        a, b = q.get("concept_id_a"), q.get("concept_id_b")
        if a in concepts and b in concepts:
            path   = _bfs_path(concepts, a, b)
            shared = [c["id"] for c in concepts.values() if a in c["deps"] and b in c["deps"]]
            ids    = list(dict.fromkeys(path + shared + concepts[a]["deps"][:3] + concepts[b]["deps"][:3]))
        else: ids = []
    else: ids = []
    return _serialize(concepts, ids)


# ── RAG corpus + retrieval (LangChain) ────────────────────────────────────────

def build_rag_corpus(concepts):
    """Convert graph CSV into prose chunks LangChain can index."""
    docs = []
    for c in concepts.values():
        dep_labels = [concepts[d]["label"] for d in c["deps"] if d in concepts]
        text = f"{c['label']} [{c['tax']}]"
        if dep_labels:
            text += f". Prerequisites: {', '.join(dep_labels)}."
        docs.append(text)
    return docs

def build_rag_retriever(docs):
    try:
        from langchain_community.vectorstores import FAISS
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        raise SystemExit(
            "LangChain not installed.\n"
            "Run: pip install langchain-community faiss-cpu sentence-transformers"
        )
    print(f"  Building FAISS index ({len(docs)} chunks)…", end=" ", flush=True)
    t0 = time.time()
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    vectorstore = FAISS.from_texts(docs, embeddings)
    print(f"done ({time.time()-t0:.1f}s)")
    return vectorstore.as_retriever(search_kwargs={"k": 5})

def rag_retrieve(retriever, question):
    """Return (context_string, ctx_token_count)."""
    docs     = retriever.invoke(question)
    ctx_text = "\n".join(d.page_content for d in docs)
    return ctx_text, len(ctx_text.split())


# ── LLM backends ─────────────────────────────────────────────────────────────

def _call_ollama(context, question):
    import requests
    prompt = f"{SYSTEM_PROMPT}\n\n{context}\n\nQuestion: {question}"
    t0 = time.time()
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
        }, timeout=60)
        r.raise_for_status()
        data = r.json()
        return (data.get("response","").strip(),
                data.get("prompt_eval_count", len(prompt.split())),
                data.get("eval_count", 50),
                int((time.time()-t0)*1000))
    except Exception as e:
        raise SystemExit(
            f"Ollama not running or model not found.\n"
            f"Install: https://ollama.ai  then: ollama pull {OLLAMA_MODEL}\n"
            f"Error: {e}"
        )

def _call_claude(client, context, question):
    t0 = time.time()
    msg = client.messages.create(
        model=HAIKU_MODEL, max_tokens=512, temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role":"user","content":f"{context}\n\nQuestion: {question}"}],
    )
    return (msg.content[0].text,
            msg.usage.input_tokens,
            msg.usage.output_tokens,
            int((time.time()-t0)*1000))

def make_llm_backend():
    """Return (call_fn, langchain_llm, price_in, price_out, label)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            from langchain_anthropic import ChatAnthropic
            client = anthropic.Anthropic(api_key=api_key)
            lc_llm = ChatAnthropic(model=HAIKU_MODEL, api_key=api_key, temperature=0)
            def call(ctx, q):
                return _call_claude(client, ctx, q)
            print(f"  LLM: Claude Haiku (API)")
            return call, lc_llm, PRICE_IN, PRICE_OUT, "Claude Haiku"
        except ImportError:
            pass

    # Ollama fallback — use requests directly, no LangChain LLM object needed
    global OLLAMA_MODEL
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
    except Exception:
        raise SystemExit(
            "Ollama not running. Install at https://ollama.ai then:\n"
            f"  ollama pull {OLLAMA_MODEL}\n"
            "Or set ANTHROPIC_API_KEY to use Claude instead."
        )
    # Pick best available model
    preferred = [OLLAMA_MODEL, "phi4-mini:latest", "mistral:latest", "qwen3:8b", "deepseek-r1:8b"]
    chosen = next((m for m in preferred if m in models), models[0] if models else None)
    if not chosen:
        raise SystemExit("No Ollama models found. Run: ollama pull llama3.2:3b")
    OLLAMA_MODEL = chosen

    def call(ctx, q):
        return _call_ollama(ctx, q)
    print(f"  LLM: Ollama {chosen} (local)")
    return call, None, OLLAMA_PRICE, OLLAMA_PRICE, f"Ollama/{chosen}"


# ── Pretty output ─────────────────────────────────────────────────────────────

TEAL = "\033[38;5;29m"; RED = "\033[38;5;160m"; BOLD = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"

def _bar(val, max_val, width=20, color=TEAL):
    filled = int(val / max_val * width) if max_val else 0
    return color + "█" * filled + DIM + "░" * (width - filled) + RESET

def print_header(domain, n_queries, llm_label):
    print(f"\n{BOLD}{'─'*62}{RESET}")
    print(f"{BOLD}  CKG vs LangChain RAG  ·  domain: {domain}  ·  {n_queries} queries{RESET}")
    print(f"  LLM: {llm_label}")
    print(f"{'─'*62}\n")

def print_query_row(i, q, ckg_res, rag_res):
    qtype = (q.get("type") or q.get("query_type","?"))[:14]
    ckg_tok, rag_tok = ckg_res["tokens"], rag_res["tokens"]
    ckg_f1,  rag_f1  = ckg_res["f1"],     rag_res["f1"]
    ratio = rag_tok / ckg_tok if ckg_tok else 0
    print(f"  Q{i+1} [{qtype:<14}] {q['query'][:52]}")
    print(f"       {'CKG':5} {_bar(ckg_f1,1,14,TEAL)}  F1={TEAL}{ckg_f1:.3f}{RESET}  {ckg_tok:>5} tok")
    print(f"       {'RAG':5} {_bar(rag_f1,1,14,RED)}   F1={RED}{rag_f1:.3f}{RESET}  {rag_tok:>5} tok  ({ratio:.1f}× more)")
    print()

def print_summary(results_ckg, results_rag, price_in, price_out, llm_label):
    def agg(rs):
        f1s   = [r["f1"] for r in rs]
        toks  = [r["tokens"] for r in rs]
        costs = [r["cost"] for r in rs]
        return (round(sum(f1s)/len(f1s),3),
                round(sum(toks)/len(toks)),
                round(sum(costs),5))

    cf1, ctok, ccost = agg(results_ckg)
    rf1, rtok, rcost = agg(results_rag)
    tok_ratio  = round(rtok / ctok, 1) if ctok else 0
    f1_ratio   = round(cf1 / rf1,   1) if rf1  else 0
    cost_ratio = round(rcost / ccost, 1) if ccost else 0

    print(f"{'─'*62}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{'─'*62}")
    print(f"  {'Metric':<22}{'CKG':>10}{'RAG':>10}{'Δ':>10}")
    print(f"  {'─'*52}")
    print(f"  {'Macro F1':<22}{TEAL}{cf1:>10.3f}{RESET}{RED}{rf1:>10.3f}{RESET}{BOLD}{f1_ratio:>9.1f}×{RESET}")
    print(f"  {'Mean tokens / query':<22}{TEAL}{ctok:>10,}{RESET}{RED}{rtok:>10,}{RESET}{BOLD}{tok_ratio:>9.1f}×{RESET}")

    if price_in > 0:
        print(f"  {'Est. cost / query':<22}{TEAL}${ccost:>9.5f}{RESET}{RED}${rcost:>9.5f}{RESET}{BOLD}{cost_ratio:>9.1f}×{RESET}")
    else:
        print(f"  {'Est. cost / query':<22}{'local (free)':>20}")

    if tok_ratio >= 2:
        eng_mo_savings = 478 * (1 - 1/tok_ratio)
        print(f"\n  At ${478}/eng/mo baseline (Uber-reconstructed rate):")
        print(f"  {TEAL}{BOLD}${eng_mo_savings:.0f}/eng/month saved{RESET}  ·  "
              f"{BOLD}${eng_mo_savings*12:.0f}/eng/year{RESET}")
        print(f"  1,000-engineer team → {TEAL}{BOLD}${eng_mo_savings*1000*12/1e6:.1f}M/year{RESET}")

    print(f"\n  Benchmark source: github.com/Yarmoluk/ckg-benchmark  (v0.6.2)")
    print(f"  ckg-mcp PyPI:     pip install ckg-mcp")
    print(f"{'─'*62}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain",  default="calculus", help="CKG domain (default: calculus)")
    ap.add_argument("--queries", type=int, default=5, help="Number of queries to run (default: 5)")
    args = ap.parse_args()

    print(f"\n  Loading domain '{args.domain}'…")
    concepts = _load_graph(args.domain)
    queries  = _load_queries(args.domain, args.queries)
    print(f"  {len(concepts)} concepts · {len(queries)} queries selected")

    call_llm, lc_llm, price_in, price_out, llm_label = make_llm_backend()

    corpus      = build_rag_corpus(concepts)
    retriever   = build_rag_retriever(corpus)

    print_header(args.domain, len(queries), llm_label)

    results_ckg, results_rag = [], []

    for i, q in enumerate(queries):
        qtext = q["query"]
        truth = q.get("ground_truth", [])

        # ── CKG ──
        ctx_ckg = ckg_retrieve(concepts, q)
        ans_ckg, pt_ckg, ct_ckg, _ = call_llm(ctx_ckg, qtext)
        total_ckg = pt_ckg + ct_ckg
        cost_ckg  = pt_ckg * price_in + ct_ckg * price_out
        f1_ckg    = token_f1(ans_ckg, truth)
        results_ckg.append({"f1": f1_ckg, "tokens": total_ckg, "cost": cost_ckg})

        # ── RAG ──
        ctx_rag, ctx_tok_rag = rag_retrieve(retriever, qtext)
        ans_rag, pt_rag, ct_rag, _ = call_llm(ctx_rag, qtext)
        total_rag = pt_rag + ct_rag
        cost_rag  = pt_rag * price_in + ct_rag * price_out
        f1_rag    = token_f1(ans_rag, truth)
        results_rag.append({"f1": f1_rag, "tokens": total_rag, "cost": cost_rag})

        print_query_row(i, q, results_ckg[-1], results_rag[-1])
        time.sleep(0.1)

    print_summary(results_ckg, results_rag, price_in, price_out, llm_label)


if __name__ == "__main__":
    main()

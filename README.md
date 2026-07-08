<!-- mcp-name: io.github.Yarmoluk/ckg-mcp -->
# MCP — CKG

[![PyPI version](https://img.shields.io/pypi/v/ckg-mcp?color=0f6e56&label=PyPI)](https://pypi.org/project/ckg-mcp/)
[![Downloads](https://img.shields.io/pypi/dm/ckg-mcp?color=0f6e56&label=installs%2Fmo)](https://pypi.org/project/ckg-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/ckg-mcp?color=0f6e56)](https://pypi.org/project/ckg-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0f6e56)](LICENSE)
[![Domains](https://img.shields.io/badge/domains-97-0f6e56)](https://graphifymd.com)
[![Free](https://img.shields.io/badge/free-68_domains-0f6e56)](https://pypi.org/project/ckg-mcp/)
[![F1: 0.471 · 4× RAG](https://img.shields.io/badge/F1-0.471_%C2%B74%C3%97_RAG-0f6e56)](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
[![KRB v0.6.2](https://img.shields.io/badge/benchmark-KRB_v0.6.2-13201c)](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
[![Built by Graphify.md](https://img.shields.io/badge/built_by-Graphify.md-0f6e56)](https://graphifymd.com)

**MCP server — Compressed Knowledge Graph (CKG) catalog. 97 domains. 68 free.**

**4× F1 · 11× fewer tokens · deterministic traversal · model-agnostic.**

> **Read-only.** This MCP server never writes, mutates, or executes. Every response is a declared graph traversal — not inference, not retrieval, not generation.

---

## The problem every AI team hits

More agents. More retrieval. More context. And accuracy drops.

This is the **intelligence paradox**: the more AI you add, the more tokens you burn re-discovering structure your system already knows — or could know. Research finds 73% of enterprise tokens are redundant context. In multi-agent pipelines, context efficiency collapses from 18.2 in Q1 to 1.6 by Q4 — **91% degradation with no model change**.

The model is not the bottleneck. The context is.

Every time your agent retrieves an explanation of what FlashAttention-3 requires, or what HIPAA's minimum necessary standard means for a business associate, it spends ~2,982 tokens re-inferring a relationship that could be declared once and traversed in 269. That difference compounds across every query, every agent, every domain boundary.

**The fix is not a better model. It is structured context.**

---

## What this package does

A CKG is a **layer** — a fast, inexpensive way to convert a large volume of domain documentation into structured, agent-traversable knowledge. Instead of retrieval, the agent traverses. Instead of inference, it reads declared relationships.

`ckg-mcp` gives your agent **97 domains** — mathematics, GPU inference, healthcare, law, robotics, regulatory, AI tooling, and more — as its context layer. Each domain is a pre-compiled, typed graph of concepts and dependency chains. Load one, load ten, load the whole catalog.

**Layers stack. Context windows open.**

| Layer | What your agent gains |
|---|---|
| Domain knowledge (this package) | 97 structured graphs — declared relationships, not inferred |
| Your organization | Company knowledge, internal taxonomy, product relationships |
| Regulatory layer | Policy graphs, compliance chains, audit trails |
| Market layer | Competitive intelligence, pricing, positioning |

Each additional CKG layer costs your agent fewer tokens to operate, not more. Structured context is **model augmentation** — it does not replace what the model knows, it makes what it knows precise and auditable.

```
query_ckg(domain="nvidia-gpu-inference", concept="FlashAttention-3", depth=3)

→ FlashAttention-3 requires:
    SRAM Tiling → On-Chip Memory Budget → Warp Occupancy
    Transformer Attention → Scaled Dot-Product Attention → Softmax Stability
  FlashAttention-3 enables:
    Multi-Head Attention → KV Cache → Speculative Decoding
```

That traversal cost **269 tokens**. A RAG call over the same question costs ~2,982. The graph doesn't guess — it traverses.

---

## Explore the graph

Once installed, paste this into Claude, Cursor, or any MCP client and see what comes back:

```
You have access to the ckg MCP server — 97 domain graphs.

I want to understand the full dependency chain from foundational ML to a
production GPU inference deployment. Not the blog post version — the
actual prerequisite chain, including what breaks at scale.

Start with the learning path:
  get_prerequisites("Gradient Descent", "machine-learning-textbook")

Then cross into infrastructure:
  query_ckg("FlashAttention-3", "nvidia-gpu-inference", depth=3)

Then map the context cost:
  query_ckg("Context Transaction Cost", "context-as-a-service", depth=2)

Show the chain as a layered map — foundation at the bottom, production at
the top. Mark where each domain hands off to the next. Flag any prerequisite
that is shared across multiple domains.
```

The graph traverses three domains, surfaces cross-domain dependencies, and shows you exactly what a team needs to know before they scale — no hallucination, no guessing, just declared relationships.

---

## Quickstart

No global install needed — just run:

```bash
uvx ckg-mcp
```

Or install permanently:

```bash
pip install ckg-mcp    # Python ≥ 3.10
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ckg": { "command": "uvx", "args": ["ckg-mcp"] }
  }
}
```

### Claude Code

```bash
claude mcp add ckg -- uvx ckg-mcp
```

### Cursor / Cline / Windsurf / any MCP client

```json
{ "mcpServers": { "ckg": { "command": "uvx", "args": ["ckg-mcp"] } } }
```

### System prompt snippet

```
You have access to the ckg MCP server — a typed dependency graph catalog of 97 domains
(mathematics, GPU inference, healthcare, law, robotics, regulatory, AI tooling, and more).
When answering questions about any of these domains, call query_ckg() or get_prerequisites()
before responding. Do not guess dependency chains — traverse the graph instead.
```

---

## Accuracy model

Every edge was declared by a human reviewer. The graph is in active development — corrections arrive from the community weekly.

**Three-state confidence:**

| State | Meaning | How to use |
|---|---|---|
| `confidence: high` | Reviewed, cross-referenced with primary sources | Trust for planning |
| `confidence: null` | Plausible, not yet audited | Scaffold — verify before production |
| `confidence: low` | Flagged as uncertain | Treat as a hint, not a fact |

**Typed edges — semantic precision:**

| Type | Meaning | Agent use |
|---|---|---|
| `REQUIRES` | Hard prerequisite | Plan sequencing, gap detection |
| `ENABLES` | Unlocks a capability | Optimization paths |
| `RELATES_TO` | Conceptual proximity | Disambiguation, context |
| `IMPLEMENTS` | Concrete instantiation | Architecture mapping |
| `CONTRASTS_WITH` | Meaningful opposition | Disambiguation, tradeoff reasoning |

If an edge isn't declared, the traversal returns nothing rather than hallucinating a path. That silence is signal.

---

## Tools

All tools are read-only. No writes, no side effects, no API key required for free domains.

### `list_domains()`
Returns all 97 domains — free and Pro. **Start here** — domain slugs are required by every other tool.

### `search_concepts(domain, query)`
Find concepts by keyword within a domain.

```
search_concepts("nvidia-gpu-inference", "speculative decoding")
→ Speculative Decoding [Optimization]
   Draft Model [Component]
   KV Cache [Infrastructure]
```

### `query_ckg(domain, concept, depth=3)`
Traverse the graph from a concept — prerequisites and dependents, up to N hops.

```
query_ckg("calculus", "Taylor Series", 3)
→ Prerequisites: Function → Limit → Continuity → Derivative →
                 Higher-Order Derivatives → Convergence → Power Series
  Enables: Fourier Series → Signal Decomposition → FFT
```

### `get_prerequisites(domain, concept)`
Full ordered prerequisite chain — everything needed to understand or deploy first.

```
get_prerequisites("hipaa-compliance", "Business Associate Agreement")
→ Covered Entity → PHI Definition → Minimum Necessary Standard →
  Access Controls → Breach Notification Rule → BAA
```

### `list_agent_blueprints()`
Browse pre-built agent configurations by use case — domains, workflow steps, system prompt, LangGraph hint.

### `get_agent_blueprint(use_case)`
Full agent spec: which domains to load, step-by-step workflow, a ready-to-paste system prompt, and a LangGraph orchestration hint.

```
get_agent_blueprint("gpu-inference-optimizer")
→ Required domains: nvidia-gpu-inference, context-as-a-service
  Workflow: diagnose → trace prerequisites → identify optimization path → recommend
  Prompt template: [ready to paste]
  LangGraph hint: StateGraph with 4 nodes
```

---

## Domain library — 68 free · 29 Pro · 97 total

These are not summaries or embeddings. Each is a compiled, traversable graph of concepts and typed relationships. Call `list_domains()` to see them live.

**Mathematics**
`calculus` · `pre-calc` · `algebra-1` · `linear-algebra` · `geometry-course` · `statistics-course` · `functions` · `fft-benchmarking`

**Engineering & Computer Science**
`circuits` · `digital-electronics` · `computer-science` · `quantum-computing` · `signal-processing` · `intro-to-graph`

**Life Sciences**
`biology` · `bioinformatics` · `genetics` · `ecology` · `chemistry`

**Clinical & Health (free)**
`glp1-obesity` · `glp1-muscle-loss` · `dementia`

**Regulatory & Government**
`fda-drug-approval-chain` · `fda-adverse-event-chain` · `federal-procurement-chain` · `gao-oversight-chain`

**AI, ML & Data**
`machine-learning-textbook` · `data-science-course` · `conversational-ai` · `langchain-core` · `dbt-core` · `apache-iceberg`

**AI Tools (provider graphs)**
`claude-anthropic` · `claude-skills` · `cursor` · `deepseek` · `gemini-api` · `grok-xai` · `kimi-moonshot` · `midjourney` · `openai-platform` · `qwen` · `vercel-ai-sdk`

**Robotics & Physical AI**
`ros2-architecture` · `robot-motion-planning`

**Learning & Pedagogy**
`prompt-class` · `tracking-ai-course` · `automating-instructional-design` · `microsims` · `infographics` · `it-management-graph`

**Business & Society**
`economics-course` · `personal-finance` · `ethics-course` · `theory-of-knowledge` · `systems-thinking` · `digital-citizenship` · `blockchain` · `unicorns`

**Reference & Culture**
`art-of-war` · `laudato-si` · `learning-linux` · `us-geography` · `asl-book` · `reading-for-kindergarten` · `moss`

---

**Pro domains (29) — activate with one env var after purchase at [graphifymd.com/pro](https://graphifymd.com/pro):**

*Healthcare & clinical:* `hipaa-compliance` · `hipaa-ai` · `cpt-em-coding` · `icd10-metabolic` · `payer-formulary` · `drug-interactions` · `modeling-healthcare-data` · `clinical-decision-chain` · `medical-billing-chain`

*Enterprise data stack:* `databricks-unity` · `snowflake-horizon` · `postgresql` · `sql-dialect-portability` · `aws-data-catalog` · `azure-purview` · `google-dataplex` · `open-catalog-endpoints` · `openlineage` · `knowledge-layer-standards`

*AI infrastructure:* `nvidia-gpu-inference` · `context-as-a-service` · `agent-reliability` · `ai-governance` · `token-cost-crisis` · `organizational-analytics`

*Legal & compliance chains:* `legal-citation-chain` · `contract-law-elements` · `aml-kyc-chain` · `investment-risk-chain`

```bash
export CKG_API_KEY=cs_live_your_key_here
# restart your MCP client — all 97 domains appear in list_domains()
```

[Get Pro → graphifymd.com/pro](https://graphifymd.com/pro)

---

## Benchmark

Evaluated on [KRB Benchmark v0.6.2](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf) — open dataset, reproducible methodology, fixed baselines.

| System | Macro F1 | Tokens/query | Cost/1K queries |
|---|---|---|---|
| **CKG** | **0.471** | **269** | **$7.81** |
| RAG (text-embedding-3-small) | 0.123 | 2,982 | $76.23 |
| GraphRAG (MS global mode) | 0.120 | — | — |

4× F1 · 11× fewer tokens · 5-hop F1 **0.772** vs **0.170** · auditable by design

5-hop reasoning is where the gap compounds: retrieval degrades with each hop; graph traversal does not. At 100 queries a day across a team, the token difference is the infrastructure cost.

```
335 domain queries
= 1,000,000 tokens with RAG    ($76.23)
=    90,000 tokens with CKG    ($7.81)
```

---

## How the graph is built

Each domain is a DAG stored as typed edge CSV — human-authored and human-reviewed:

```
ConceptID, ConceptLabel,    Dependencies,                    TaxonomyID
1,         Taylor Series,   "",                              Analysis
2,         Power Series,    "",                              Analysis
3,         Convergence,     "2:REQUIRES",                    Analysis
4,         Higher-Order D., "5:REQUIRES",                    Calculus
5,         Derivative,      "6:REQUIRES",                    Calculus
6,         Continuity,      "7:REQUIRES",                    Calculus
7,         Limit,           "8:REQUIRES",                    Calculus
8,         Function,        "",                              Foundations
```

No embeddings. No vector index. No probabilistic retrieval. The graph is the compressed form — built once, reviewed once, traversed forever.

---

## Why context efficiency collapses — and how CKG reverses it

Liu et al. ([arXiv:2606.30986](https://arxiv.org/abs/2606.30986)) formally quantify **Context Transaction Cost (CTC)**: the compound tax paid every time context crosses an agent boundary. In multi-agent pipelines, CTC efficiency falls from 18.2 in Q1 to 1.6 by Q4 — 91% collapse with no model change.

CKG attacks all three root causes:

| CTC component | What it is | CKG's response |
|---|---|---|
| Token Latency Burden (τ) | Compute cost of transmitting context | 269 tokens instead of 2,982 |
| Handoff Cost (H) | Serialization loss at agent boundaries | `get_prerequisites()` replaces re-retrieval |
| Compression Loss (C) | Information destroyed when context is summarized | The graph *is* the compressed form — done once, offline |

Structured context doesn't consume your context window. It opens it.

---

## The alternative to fine-tuning

When task-specific data is scarce, fine-tuning is often the first instinct — and frequently the wrong one. Fine-tuning requires thousands of labeled examples, a training budget, and a retraining cycle every time your domain shifts. By the time a large enterprise model project completes, the knowledge it was trained on is often already stale.

CKG encodes domain knowledge once as a typed graph. When the knowledge changes — new regulations, new product, new market — you update the graph. Not the model.

> *Directional intelligence, deployed today, updatable tomorrow — at 11× lower token cost.*

**The commercial case in three parts:**

| | Fine-tuning | CKG |
|---|---|---|
| **Speed** | 6-month cycle before you see results | One session to deploy |
| **Adaptability** | Retrain when knowledge shifts | Update the graph, not the model |
| **Sustainability** | Expensive to run at scale | 269 tokens/query — 10,000 questions vs 1,000 |

**Enterprise risk coverage:**

| Risk | CKG response |
|---|---|
| Drift without version control | Typed, declared edges don't drift — every change is a graph update |
| Institutional knowledge lock-in | Human-readable, portable CSV — not vendor-locked |
| Provenance reconstruction failure | Every edge has a declared source and type — inherently auditable |
| New hire / auditor onboarding | CKG as runbook — traversable by anyone, not just the team that built it |

---

## Agent Blueprints

Blueprints are pre-built agent specifications: which domains to load, workflow steps, constraints, a ready-to-use system prompt, and a LangGraph orchestration hint. Use them as starting points for domain-specific agents without writing the context layer from scratch.

```
list_agent_blueprints()
→ gpu-inference-optimizer      — diagnose GPU bottlenecks, trace optimization paths
  context-as-a-service-advisor — design CKG-based retrieval pipelines

get_agent_blueprint("gpu-inference-optimizer")
→ Required domains: nvidia-gpu-inference, context-as-a-service
  Workflow: diagnose → trace prerequisites → identify optimization path → recommend
  Prompt template: [ready to paste into your agent]
  LangGraph hint: StateGraph with 4 nodes — diagnose, trace, optimize, report
```

---

## Free vs Pro

| | **Free** | **Pro — $99/mo** |
|---|---|---|
| Domains | 68 | 97 |
| Healthcare & clinical | — | HIPAA, CPT coding, ICD-10, payer formulary, drug interactions, clinical decision chain, medical billing |
| Enterprise data stack | — | Databricks Unity, Snowflake Horizon, PostgreSQL, AWS Data Catalog, Azure Purview, GCP Dataplex, OpenLineage |
| AI infrastructure | — | NVIDIA GPU inference, context-as-a-service, agent reliability, AI governance, token cost crisis |
| Legal & compliance | — | Legal citation chain, contract law elements, AML/KYC chain, investment risk chain |
| Agent blueprints | 2 | 2 + priority access to new use cases |
| License | MIT | Commercial |

[Get Pro → graphifymd.com/pro](https://graphifymd.com/pro)

---

## Corrections welcome

Spotted a wrong edge? A `RELATES_TO` that should be `REQUIRES`? A missing concept in any domain?

**Edge corrections are the highest-value contribution.** The graph gets more useful with every fix. Open an issue or PR on [GitHub](https://github.com/Yarmoluk/ckg-mcp).

---

## EVAL

```
benchmark: ckg-benchmark v0.6.2
dataset: huggingface.co/datasets/danyarm/ckg-benchmark
benchmarked: true
this_domain_f1: 0.471
queries_tested: 19
rag_baseline_f1: 0.123
graphrag_baseline_f1: 0.120
mean_tokens: 269
paper: github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf
```

---

## Want a CKG for your domain?

A CKG is a **knowledge layer** — the context optimization component of an agent stack. Instead of retrieval, your agent traverses declared relationships. Fast to build, inexpensive to run, updatable without retraining.

Turn your company documentation, internal APIs, competitive intelligence, or regulatory requirements into a CKG layer in a single session. Stack it with the 97 domains already here. Each layer opens more of your context window without adding token cost.

**[graphifymd.com](https://graphifymd.com)** — contact us for custom domain CKGs and enterprise solutions, including Sealed Appliance: a private CKG + query server deployed in your environment.

CKG Catalog · Context Optimization · Context Architecture · Token Efficiency · Accuracy

---

## Compatibility

Model-agnostic — the graph is plain text, readable by any LLM:

| LLM | Agent framework | MCP client |
|-----|-----------------|------------|
| Claude (all tiers) | LangChain / LangGraph | Claude Desktop |
| GPT-4o / GPT-4 | AutoGen | Claude Code |
| Gemini 2.0 / 2.5 | smolagents | Cursor |
| Llama 3.x | CrewAI | Cline |
| Mistral | Haystack | Windsurf |
| DeepSeek | OpenAI Agents SDK | Any MCP stdio client |

No graph database. No vector store. Python ≥ 3.10. Single dependency (`mcp`). stdio transport.

---

## Reproduce the benchmark

```bash
git clone https://github.com/Yarmoluk/ckg-benchmark && cd ckg-benchmark
pip install -r evaluation/requirements.txt
python evaluation/ckg_harness.py --domain calculus
python evaluation/analyze_results.py
```

[Full benchmark paper →](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

---

## Ecosystem

This package is part of the Graphify.md CKG stack.

| Package | What it does |
|---|---|
| **[ckg-mcp](https://pypi.org/project/ckg-mcp/)** | This repo — 97 domains: math, science, healthcare, law, GPU, robotics |
| **[ckg-nvidia-ai](https://pypi.org/project/ckg-nvidia-ai/)** | 20 NVIDIA AI domains, entirely free, MCP-native |
| **[agentmem-mcp](https://github.com/Yarmoluk/agent-memory-mcp)** | Cross-session agent memory, not vendor-locked |
| **[KRB Benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)** | Open benchmark dataset — reproduce the F1 numbers yourself |
| **[ckg-eval](https://github.com/Yarmoluk/ckg-eval)** | Path-Fidelity Score (PFS) — reasoning path correctness metric |

**[graphifymd.com/pro/](https://graphifymd.com/pro/)** — custom domain CKGs, sealed appliances, enterprise.

---

## Citation

```bibtex
@misc{yarmoluk2026ckg,
  title  = {Benchmarking Knowledge Retrieval Architectures Across Educational
            and Commercial Domains: RAG, GraphRAG, and Compressed Knowledge Graphs},
  author = {Yarmoluk, Daniel and McCreary, Dan},
  year   = {2026},
  note   = {v0.6.2. https://github.com/Yarmoluk/ckg-benchmark}
}
```

---

*Patent pending. 42× Token Intelligence — more intelligence per watt.*

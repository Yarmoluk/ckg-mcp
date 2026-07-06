# ckg-mcp

<!-- mcp-name: io.github.Yarmoluk/ckg-mcp -->

[![PyPI](https://img.shields.io/pypi/v/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![Downloads](https://static.pepy.tech/badge/ckg-mcp/month)](https://pepy.tech/project/ckg-mcp)
[![Python](https://img.shields.io/pypi/pyversions/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)
[![Benchmark](https://img.shields.io/badge/benchmark-open%20%26%20reproducible-orange)](https://github.com/Yarmoluk/ckg-benchmark)

If ckg-mcp is useful to you, a ⭐ on [GitHub](https://github.com/Yarmoluk/ckg-mcp) helps others find it.

---

## The problem you already have

You are building an agent — or just using Claude, GPT-4o, or any LLM — and you need it to reason deeply about a specific domain. Calculus. HIPAA. GPU inference. GLP-1 pharmacology. Drug interactions.

What do you do today?

- Paste in a document and hope the model picks out the right parts
- Write a long system prompt explaining the domain
- Set up RAG and spend days tuning retrieval
- Accept that the model will guess at relationships it doesn't actually know

Every one of those paths has the same failure mode: the model is working from text it is *inferring* from, not a structure it can *traverse*. It will hallucinate a dependency. Miss a prerequisite. Return a confident answer that is architecturally wrong.

---

## What ckg-mcp does differently

A **Compressed Knowledge Graph (CKG)** is a domain that has already been structured for you.

Not a document. Not a vector index. A pre-compiled graph of the concepts in a domain, their typed relationships, and their dependency chains — compressed to the minimum tokens that carry the maximum structure.

When you install `ckg-mcp`, you get **97 of these graphs** (68 free immediately, 29 more with Pro) served over MCP. Your agent does not have to understand calculus, or HIPAA, or how GPU memory bandwidth relates to FlashAttention. The graph already knows. The agent just traverses it.

**You go from prompting the domain into existence to asking questions inside it.**

That is the architectural shift. Everything else — the benchmark numbers, the token savings, the accuracy gains — follows from that one change.

---

## Install and first query (60 seconds)

No global install needed — just run:

```bash
uvx ckg-mcp
```

Or install permanently:

```bash
pip install ckg-mcp        # Python ≥ 3.10
```

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ckg": { "command": "uvx", "args": ["ckg-mcp"] }
  }
}
```

**Claude Code:**
```bash
claude mcp add ckg -- uvx ckg-mcp
```

**Cursor / Cline / Windsurf / any MCP client:**
```json
{ "mcpServers": { "ckg": { "command": "uvx", "args": ["ckg-mcp"] } } }
```

Restart your client. Then just ask:

> *"What do I need to understand before I can understand Taylor Series?"*

> *"Trace the dependency chain from Memory Bandwidth to Speculative Decoding in the GPU inference domain."*

> *"What HIPAA concepts are prerequisites for understanding a Business Associate Agreement?"*

You do not need to explain calculus. You do not need to explain GPU architecture. You do not need to paste anything. The graph is already there. Claude calls the tools automatically and returns a structured, traceable answer.

---

## What the output looks like

```
You: What do I need to know before FlashAttention-3?

Claude calls: get_prerequisites(domain="nvidia-gpu-inference", concept="FlashAttention-3")

→ Prerequisite chain for FlashAttention-3 (nvidia-gpu-inference):

  Memory Bandwidth
  └─ HBM3 Memory
     └─ GPU Memory Hierarchy
        └─ DRAM Latency
  Transformer Attention
  └─ Scaled Dot-Product Attention
     └─ Softmax Stability
  SRAM Tiling
  └─ On-Chip Memory Budget
     └─ Warp Occupancy

  Every edge above is declared in the graph.
  Nothing was inferred. Nothing was retrieved from text.
```

```
You: Walk me through what Taylor Series depends on.

Claude calls: get_prerequisites(domain="calculus", concept="Taylor Series")

→ Function → Limit → Continuity → Derivative → Higher-Order Derivatives
  → Convergence → Power Series → Taylor Series

  20 concepts. Ordered. Typed. Traversed in 269 tokens.
  A RAG system retrieving from a calculus textbook uses 2,982 tokens
  and misses the chain 53% of the time.
```

---

## The six tools

No database. No embeddings. No API key. Six tools, all deterministic.

| Tool | What it does |
|------|--------------|
| `list_domains()` | See every domain available. **Start here.** |
| `query_ckg(domain, concept, depth=3)` | Full subgraph around a concept — prerequisites + dependents, up to N hops |
| `get_prerequisites(domain, concept)` | Every concept that must be understood first, in dependency order |
| `search_concepts(domain, query)` | Find concepts by name — partial match, case-insensitive |
| `list_agent_blueprints()` | Browse pre-built agent configurations by use case |
| `get_agent_blueprint(use_case)` | Full agent spec: domains, workflow, constraints, system prompt, LangGraph hint |

---

## The full domain library (68 free · 29 Pro · 97 total)

These are not summaries or embeddings. Each is a compiled, traversable graph of concepts and typed relationships in that domain. Call `list_domains()` to see them live.

**Mathematics**
`calculus` · `pre-calc` · `algebra-1` · `linear-algebra` · `geometry-course` · `statistics-course` · `functions` · `fft-benchmarking`

**Engineering & Computer Science**
`circuits` · `digital-electronics` · `computer-science` · `quantum-computing` · `signal-processing` · `intro-to-graph`

**Life Sciences**
`biology` · `bioinformatics` · `genetics` · `ecology` · `chemistry`

**Clinical & Health (free)**
`glp1-obesity` · `glp1-muscle-loss` · `dementia`

**Regulatory & Government** *(new)*
`fda-drug-approval-chain` · `fda-adverse-event-chain` · `federal-procurement-chain` · `gao-oversight-chain`

**AI, ML & Data**
`machine-learning-textbook` · `data-science-course` · `conversational-ai` · `langchain-core` · `intro-to-physics-course` · `dbt-core` · `apache-iceberg`

**AI Tools (provider graphs)**
`claude-anthropic` · `claude-skills` · `cursor` · `deepseek` · `gemini-api` · `grok-xai` · `kimi-moonshot` · `glm-zhipu` · `midjourney` · `openai-platform` · `qwen` · `vercel-ai-sdk`

**Robotics & Physical AI** *(new)*
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

We ship new domains continuously. The library is designed for throughput — the more domains loaded, the more your agent reasons across without any prompting or context setup.

---

## At scale, this compounds

The token math is where this becomes a different class of tool:

```
335 domain queries
= 1,000,000 tokens with RAG       ($76.23)
=    90,000 tokens with CKG       ($7.81)
```

That is not a tuning difference. That is an architectural one. Every query your agent runs, it is either scanning retrieved text or traversing declared structure. At 100 queries a day, across a team, inside an enterprise stack — the gap becomes the infrastructure cost.

**Benchmark results** (open methodology, fully reproducible):

| | **CKG** | RAG | GraphRAG |
|---|---|---|---|
| Macro-F1 | **0.471** | 0.123 | 0.120 |
| Tokens / query | **269** | 2,982 | 3,450 |
| Cost / query | **$0.0010** | $0.0106 | — |
| F1 at 5 hops | **0.772** | 0.170 | — |
| Fabricated edges | **0 — by construction** | variable | variable |

- **3.8× the F1 of RAG** at **11× fewer tokens**
- **~42× higher Retrieval Density Score** — F1 per token
- **CKG accuracy rises with depth** (0.37 → 0.77 over 5 hops). RAG is flat. There is no retrieval mechanism for traversing a dependency chain — only a graph has that.
- **GraphRAG is not the answer** (0.120 vs 0.123 F1, *more* tokens). The word "graph" is not the win. A *pre-compiled, declared* graph is.

Independent validation: [arXiv:2603.14045](https://arxiv.org/abs/2603.14045) finds **73–84% of Graph-RAG errors are reasoning failures**, not retrieval failures — the exact failure mode CKGs solve by construction.

---

## Agent Blueprints

Blueprints are pre-built agent specifications: which domains to load, workflow steps, constraints, a ready-to-use system prompt, and a LangGraph orchestration hint. Use them as starting points for building domain-specific agents without writing the context layer from scratch.

```
list_agent_blueprints()
→ gpu-inference-optimizer    — diagnose GPU bottlenecks, trace optimization paths
  context-as-a-service-advisor — design CKG-based retrieval pipelines

get_agent_blueprint("gpu-inference-optimizer")
→ Required domains: nvidia-gpu-inference, context-as-a-service
  Workflow: diagnose → trace prerequisites → identify optimization path → recommend with citations
  Prompt template: [ready to paste into your agent]
  LangGraph hint: StateGraph with 4 nodes — diagnose, trace, optimize, report
```

---

## Free vs Pro

The free tier ships 68 domains under MIT. Pro unlocks the enterprise and clinical domain chains — healthcare compliance, the full enterprise data stack, legal/compliance chains, and AI infrastructure graphs — plus managed updates as those domains evolve.

| | **Free** | **Pro — $99/mo** |
|---|---|---|
| Domains | 68 | 97 |
| Healthcare & clinical | — | HIPAA, CPT coding, ICD-10 metabolic, payer formulary, drug interactions (clinical depth), modeling healthcare data, clinical decision chain, medical billing chain |
| Enterprise data stack | — | Databricks Unity, Snowflake Horizon, PostgreSQL, AWS Data Catalog, Azure Purview, GCP Dataplex, OpenLineage, open catalog endpoints |
| AI infrastructure | — | NVIDIA GPU inference, context-as-a-service, agent reliability, AI governance, token cost crisis, organizational analytics |
| Legal & compliance | — | Legal citation chain, contract law elements, AML/KYC chain, investment risk chain |
| Agent blueprints | 2 | 2 + priority access to new use cases |
| License | MIT | Commercial |

**Activate Pro** — one environment variable after purchase:

```bash
export CKG_API_KEY=cs_live_your_key_here
# restart your MCP client — all 97 domains appear in list_domains()
```

[Get Pro → graphifymd.com/pro](https://graphifymd.com/pro)

---

## Enterprise and custom domains

The free and Pro domains cover a broad library. Enterprise needs are different: your regulatory environment, your internal taxonomy, your product domain, your data stack configuration.

**[Graphify.md](https://graphifymd.com)** builds and maintains custom CKG domain graphs for enterprise teams — compressed, versioned, deployed over your MCP stack. If you are running agents at scale and the context layer is a cost or accuracy problem, that is the conversation to have.

Typical entry point: a pilot on your highest-value domain, delivered in one session, benchmarked against your existing retrieval setup.

---

## How it works (for the technically curious)

A CKG is a plain-text DAG — concepts, typed dependency edges, taxonomy tags. The MCP server runs deterministic BFS/DFS over declared edges and returns the exact subgraph the agent requested. There is no inference at query time. There is no embedding lookup. The server can only return edges that exist in the graph — which is what makes the fabrication rate zero by construction.

The LLM still writes the final answer in prose. What changes is the *knowledge* it reasons over: declared structure instead of retrieved text.

```
1M tokens · RAG   = 335 domain queries
1M tokens · CKG   = 3,717 domain queries
```

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

---

## License

MIT. Source learning graphs derive from the McCreary Intelligent Textbook Corpus.

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

**Links:** [Benchmark](https://github.com/Yarmoluk/ckg-benchmark) · [Paper](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf) · [Pro domains](https://graphifymd.com/pro) · [Enterprise](https://graphifymd.com) · [arXiv:2603.14045](https://arxiv.org/abs/2603.14045)

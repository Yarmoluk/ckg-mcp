<!-- mcp-name: io.github.Yarmoluk/ckg-mcp -->

<div align="center">

# Context as a Service

### The MCP server that gives your AI agent a structured brain — not a search bar.

**97 domain knowledge graphs · 68 free · deterministic traversal · model-agnostic**

[![PyPI version](https://img.shields.io/pypi/v/ckg-mcp?color=0f6e56&label=PyPI)](https://pypi.org/project/ckg-mcp/)
[![Downloads](https://img.shields.io/pypi/dm/ckg-mcp?color=0f6e56&label=installs%2Fmo)](https://pypi.org/project/ckg-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/ckg-mcp?color=0f6e56)](https://pypi.org/project/ckg-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0f6e56)](LICENSE)
[![Domains](https://img.shields.io/badge/domains-97-0f6e56)](https://graphifymd.com)
[![Free](https://img.shields.io/badge/free-68_domains-0f6e56)](https://pypi.org/project/ckg-mcp/)
[![F1: 0.471 · 4× RAG](https://img.shields.io/badge/F1-0.471_%C2%B74%C3%97_RAG-0f6e56)](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
[![KRB v0.6.2](https://img.shields.io/badge/benchmark-KRB_v0.6.2-13201c)](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)
[![Built by Graphify.md](https://img.shields.io/badge/built_by-Graphify.md-0f6e56)](https://graphifymd.com)

> **Read-only.** This server never writes, mutates, or executes.
> Every response is a declared graph traversal — not inference, not retrieval, not generation.

[**Get Pro →**](https://graphifymd.com/pro) · [**Benchmark Paper →**](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf) · [**graphifymd.com →**](https://graphifymd.com)

</div>

---

## The Problem

**Your agents are smart. Your context is not.**

Every time your agent needs to understand a domain — HIPAA compliance, GPU inference, calculus, contract law — it does one of three things:

| Approach | What happens |
|---|---|
| Paste in a document | Model picks out the wrong parts. 73% of tokens are redundant context. |
| Write a long system prompt | Decays immediately. Drifts with every model update. No structure. |
| Set up RAG | Weeks of tuning. Still misses multi-hop chains 53% of the time. |

This is the **intelligence paradox**: the more AI you add, the more tokens you burn re-discovering structure your system already knows.

In multi-agent pipelines it compounds: context efficiency collapses from 18.2 in Q1 to 1.6 by Q4 — **91% degradation with no model change** ([Liu et al., arXiv:2606.30986](https://arxiv.org/abs/2606.30986)).

The model is not the bottleneck. **The context is.**

---

## The Solution

**`ckg-mcp` is Context as a Service.**

A **Compressed Knowledge Graph (CKG)** is a domain that has already been structured for you — not a document, not a vector index, not a prompt template.

A pre-compiled graph of concepts, typed dependency relationships, and prerequisite chains — compressed to the minimum tokens that carry the maximum structure. Served over MCP. Traversed deterministically.

```
Your agent asks:    "What do I need before FlashAttention-3?"
ckg-mcp returns:    SRAM Tiling → On-Chip Memory → Warp Occupancy
                    Transformer Attention → Softmax Stability
                    (269 tokens · declared edges only · 0 hallucinations)

RAG would spend:    ~2,982 tokens · miss the chain 53% of the time
```

**You go from prompting the domain into existence to asking questions inside it.**

That is the architectural shift. Everything else — the benchmark numbers, the token savings, the accuracy gains — follows from that one change.

---

## How It Works

### Every domain is a traversable DAG

```
ConceptID, ConceptLabel,      Dependencies,         TaxonomyID
1,         Taylor Series,     "",                   Analysis
2,         Power Series,      "",                   Analysis
3,         Convergence,       "2:REQUIRES",         Analysis
4,         Higher-Order Der., "5:REQUIRES",         Calculus
5,         Derivative,        "6:REQUIRES",         Calculus
6,         Continuity,        "7:REQUIRES",         Calculus
7,         Limit,             "8:REQUIRES",         Calculus
8,         Function,          "",                   Foundations
```

No embeddings. No probabilistic retrieval. The graph is the compressed form — built once, reviewed once, **traversed forever**.

### Example traversal — cross-domain

```
You: "What does it actually take to deploy Riva ASR on Jetson Orin?"

ckg-mcp traverses: nvidia-riva · nvidia-tensorrt-triton · nvidia-jetson

→ L0 Silicon:        Jetson Orin NX
  L1 OS / Kernel:    JetPack SDK · Linux Kernel 6.8 · NGC Containers
  L2 CUDA Compute:   CUDA 13.0 ← single transitive gate for entire stack
  L3 Optimization:   TensorRT SDK ← must match Orin SM version exactly
  L4 Serving:        Triton Inference Server ← must be healthy before Riva starts
  L5 Speech Models:  Conformer-CTC · Acoustic Model · Language Model
  L6 Riva Runtime:   Riva Server · Riva Container · NIM
  L7 Application:    Voice Agent Pipeline

  ⚡ Cold-start blockers surfaced: fTPM not provisioned · NGC assets not bundled
  ⚠ Documented gaps: no INT8/FP16 on-device quant path for Riva on Jetson edge

  Total: 269 tokens · 3 domains · 8 layers · 0 guesses
```

<!-- Insert: layered CKG architecture diagram — silicon → application, three-domain dependency map -->

### Typed edges carry semantic meaning

| Edge type | Meaning | Agent use |
|---|---|---|
| `REQUIRES` | Hard prerequisite — must exist first | Sequencing, gap detection |
| `ENABLES` | Unlocks a downstream capability | Optimization paths |
| `RELATES_TO` | Conceptual proximity | Disambiguation, context |
| `IMPLEMENTS` | Concrete realization of an abstraction | Architecture mapping |
| `CONTRASTS_WITH` | Meaningful opposition | Tradeoff reasoning |

If an edge isn't declared, the traversal returns nothing rather than hallucinating a path. **That silence is signal.**

---

## Quickstart

```bash
uvx ckg-mcp          # no install — runs immediately
# or
pip install ckg-mcp  # Python ≥ 3.10
```

### Claude Desktop

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

### System prompt snippet (paste into your agent)

```
You have access to the ckg MCP server — a typed dependency graph catalog of 97 domains
(mathematics, GPU inference, healthcare, law, robotics, regulatory, AI tooling, and more).
When answering questions about any of these domains, call query_ckg() or get_prerequisites()
before responding. Do not guess dependency chains — traverse the graph instead.
```

Then just ask:

> *"What do I need to understand before Taylor Series?"*
> *"Trace the full prerequisite chain for a Business Associate Agreement under HIPAA."*
> *"What does TensorRT-LLM require to run on Hopper, and what does it enable?"*

The model calls the tools automatically. You get structured, traceable answers — without pasting a single document.

---

## Layered Architecture

<!-- Insert: CKG-as-layer diagram — user's domain stack: NVIDIA layer · company knowledge layer · regulatory layer · market layer, each as a horizontal band opening the context window -->

CKGs are designed to **stack**. Each domain you load costs your agent fewer tokens to operate, not more.

```
┌──────────────────────────────────────────────┐
│  Your domain (company knowledge, internal APIs)│  ← Custom CKG — graphifymd.com
├──────────────────────────────────────────────┤
│  Regulatory / compliance layer               │  ← HIPAA · contract-law · AML/KYC
├──────────────────────────────────────────────┤
│  Infrastructure layer                        │  ← nvidia-gpu-inference · databricks
├──────────────────────────────────────────────┤
│  Foundation layer (68 free domains)          │  ← calculus · ML · biology · law
└──────────────────────────────────────────────┘
         ↑ structured context opens the window ↑
```

Structured context is **model augmentation** — it does not replace what the model knows, it makes what it knows precise and auditable.

---

## Benchmarks

> Open methodology · fully reproducible · fixed baselines · [full paper →](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

<!-- Insert: token efficiency bar chart — CKG 269 tokens vs RAG 2,982 tokens vs GraphRAG 3,450 tokens -->

| System | Macro F1 | Tokens / query | Cost / 1K queries | F1 at 5 hops |
|---|---|---|---|---|
| **CKG (this package)** | **0.471** | **269** | **$7.81** | **0.772** |
| RAG (text-embedding-3-small) | 0.123 | 2,982 | $76.23 | 0.170 |
| GraphRAG (MS global mode) | 0.120 | 3,450+ | — | — |

**4× F1 · 11× fewer tokens · 42× Retrieval Density Score · 5-hop accuracy 4.5× RAG**

```
At 335 queries:
  RAG   = 1,000,000 tokens  ($76.23)
  CKG   =    90,000 tokens  ($7.81)
```

- **CKG accuracy rises with depth** (0.37 → 0.77 over 5 hops). RAG is flat — there is no retrieval mechanism for traversing a dependency chain. Only a graph has that.
- **GraphRAG is not the answer.** 0.120 vs 0.123 F1 at *more* tokens. The word "graph" is not the win. A *pre-compiled, declared* graph is.
- **Zero fabricated edges — by construction.** The server can only return edges that exist in the data.

Independent validation: [arXiv:2603.14045](https://arxiv.org/abs/2603.14045) finds **73–84% of Graph-RAG errors are reasoning failures**, not retrieval failures — the exact failure mode CKGs solve structurally.

---

## Domain Library

### 68 free domains — no API key required

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

### Free vs Pro

| | **Free — MIT** | **Pro — $99/mo** |
|---|---|---|
| Domains | 68 | **97** |
| Healthcare & clinical | — | HIPAA · CPT coding · ICD-10 metabolic · payer formulary · drug interactions · clinical decision chain · medical billing |
| Enterprise data stack | — | Databricks Unity · Snowflake Horizon · PostgreSQL · AWS Data Catalog · Azure Purview · GCP Dataplex · OpenLineage |
| AI infrastructure | — | NVIDIA GPU inference · context-as-a-service · agent reliability · AI governance · token cost crisis |
| Legal & compliance | — | Legal citation chain · contract law elements · AML/KYC chain · investment risk chain |
| Agent blueprints | 2 included | 2 + priority access to new use cases |
| Updates | Community | Managed — domains stay current |
| License | MIT | Commercial |

**Activate in 60 seconds** — one env var after purchase:

```bash
export CKG_API_KEY=cs_live_your_key_here
# restart your MCP client — all 97 domains appear immediately
```

[**Get Pro → graphifymd.com/pro**](https://graphifymd.com/pro)

---

## Agent Blueprints

Pre-built agent specifications: which domains to load, step-by-step workflow, a ready-to-paste system prompt, and a LangGraph orchestration hint. Skip the context layer boilerplate — start with a working agent.

```
list_agent_blueprints()
→ gpu-inference-optimizer      — diagnose GPU bottlenecks, trace optimization paths
  context-as-a-service-advisor — design CKG-based retrieval pipelines

get_agent_blueprint("gpu-inference-optimizer")
→ Required domains: nvidia-gpu-inference, context-as-a-service
  Workflow: diagnose → trace prerequisites → identify optimization path → recommend
  Prompt template: [ready to paste]
  LangGraph hint: StateGraph · 4 nodes · diagnose → trace → optimize → report
```

---

## The Six Tools

All read-only. No database. No embeddings. No API key for free domains.

| Tool | What it does |
|---|---|
| `list_domains()` | See every domain available. **Start here.** |
| `query_ckg(concept, domain, depth)` | Full subgraph — prerequisites + dependents up to N hops |
| `get_prerequisites(concept, domain)` | Complete upstream chain in dependency order |
| `search_concepts(query, domain)` | Find concepts by keyword — use before query_ckg |
| `list_agent_blueprints()` | Browse pre-built agent configs by use case |
| `get_agent_blueprint(use_case)` | Full spec: domains, workflow, system prompt, LangGraph hint |

---

## Why Graphify.md

**ckg-mcp is the flagship product of [Graphify.md](https://graphifymd.com) — Context as a Service.**

We build the knowledge layer that sits between your agents and the domains they operate in. The same layer that powers this package runs inside enterprise deployments, sealed appliances, and custom vertical CKGs.

**What makes this different:**

- **Patent pending** — the CKG compression and traversal methodology
- **Open benchmark** — [KRB v0.6.2](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf), fully reproducible, not self-reported
- **Correction-forward** — every wrong edge is a community contribution; the graph gets more useful with every fix
- **No lock-in** — plain CSV DAGs, MIT-licensed, portable to any stack

**Not the right answer for every problem** — fine-tuning handles the final mile of specialization. CKG handles the knowledge architecture the fine-tuned model still needs to operate correctly. They compose.

### The alternative to fine-tuning

| | Fine-tuning | CKG |
|---|---|---|
| **Speed** | 6-month cycle before results | One session to deploy |
| **Adaptability** | Retrain when knowledge shifts | Update the graph, not the model |
| **Cost** | Expensive at scale | 269 tokens/query — 10,000 questions for the price of 1,000 |
| **Auditability** | Black box | Every edge declared, typed, and traceable |

### Compatibility — model-agnostic

| LLM | Agent framework | MCP client |
|-----|-----------------|------------|
| Claude (all tiers) | LangChain / LangGraph | Claude Desktop |
| GPT-4o / GPT-4 | AutoGen | Claude Code |
| Gemini 2.0 / 2.5 | smolagents | Cursor |
| Llama 3.x | CrewAI | Cline |
| Mistral / DeepSeek | OpenAI Agents SDK | Any MCP stdio client |

No graph database. No vector store. Python ≥ 3.10. Single dependency (`mcp`). stdio transport.

---

## Custom Domains & Enterprise

The free and Pro catalog covers breadth. Enterprise needs are different: your regulatory environment, your internal taxonomy, your product domain, your data stack configuration.

**[Graphify.md](https://graphifymd.com)** builds and maintains custom CKG domain graphs for enterprise teams — compressed, versioned, deployed over your MCP stack.

**Sealed Appliance** — a private CKG + query server deployed in your environment. Air-gapped. Your data never leaves.

Typical entry: a pilot on your highest-value domain, delivered in one session, benchmarked against your existing retrieval setup.

[Contact us → graphifymd.com](https://graphifymd.com)

---

## Call to Action

```
pip install ckg-mcp
```

- **Free tier:** `list_domains()` → 68 domains, no key required
- **Pro tier:** [graphifymd.com/pro](https://graphifymd.com/pro) → 97 domains, managed updates, enterprise data stack, HIPAA, legal chains
- **Custom CKG:** [graphifymd.com](https://graphifymd.com) → your domain, your stack, one session

---

## Ecosystem

| Package | What it does |
|---|---|
| **[ckg-mcp](https://pypi.org/project/ckg-mcp/)** | This repo — 97 domains, flagship CaaS product |
| **[ckg-nvidia-ai](https://pypi.org/project/ckg-nvidia-ai/)** | 20 NVIDIA AI domains, entirely free, MCP-native |
| **[agentmem-mcp](https://github.com/Yarmoluk/agent-memory-mcp)** | Cross-session agent memory, not vendor-locked |
| **[KRB Benchmark](https://huggingface.co/datasets/danyarm/ckg-benchmark)** | Open benchmark — reproduce the F1 numbers yourself |
| **[ckg-eval](https://github.com/Yarmoluk/ckg-eval)** | Path-Fidelity Score (PFS) — reasoning path correctness |

---

## Corrections Welcome

Spotted a wrong edge? A `RELATES_TO` that should be `REQUIRES`? A missing concept?

**Edge corrections are the highest-value contribution** — the graph gets more useful with every fix. Open an issue or PR on [GitHub](https://github.com/Yarmoluk/ckg-mcp).

---

## Reproduce the Benchmark

```bash
git clone https://github.com/Yarmoluk/ckg-benchmark && cd ckg-benchmark
pip install -r evaluation/requirements.txt
python evaluation/ckg_harness.py --domain calculus
python evaluation/analyze_results.py
```

[Full benchmark paper →](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

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

<div align="center">

**[graphifymd.com](https://graphifymd.com) · [graphifymd.com/pro](https://graphifymd.com/pro) · [Benchmark](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)**

*Patent pending. 42× Token Intelligence — more intelligence per watt.*

</div>

# ckg-mcp

<!-- mcp-name: io.github.Yarmoluk/ckg-mcp -->

[![PyPI](https://img.shields.io/pypi/v/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![Downloads](https://static.pepy.tech/badge/ckg-mcp/month)](https://pepy.tech/project/ckg-mcp)
[![Python](https://img.shields.io/pypi/pyversions/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)
[![Benchmark](https://img.shields.io/badge/benchmark-open%20%26%20reproducible-orange)](https://github.com/Yarmoluk/ckg-benchmark)

**Give your agent the structure, not the search.**

`ckg-mcp` serves **Compressed Knowledge Graphs** to any LLM via MCP — pre-structured, typed dependency graphs your agent *traverses* instead of text chunks it *guesses from*.

```
4× the F1 of RAG · 11× fewer tokens · works with Claude, GPT-4o, Gemini, Llama, Mistral, and any MCP client
```

> Measured on the open [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark) — 45 domains, 7,928 queries. [Re-run it yourself.](#reproducibility)

---

## Quickstart — 30 seconds

```bash
pip install ckg-mcp        # Python ≥ 3.10
# or zero-install:  uvx ckg-mcp
```

Pick your client:

<details open>
<summary><strong>Claude Desktop</strong></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ckg": { "command": "ckg-mcp" }
  }
}
```
</details>

<details>
<summary><strong>Claude Code (CLI)</strong></summary>

```bash
claude mcp add ckg -- ckg-mcp
```
</details>

<details>
<summary><strong>Cursor · Cline · Windsurf · any MCP client</strong></summary>

```json
{
  "mcpServers": {
    "ckg": { "command": "ckg-mcp" }
  }
}
```

Or with `uvx` (no global install):
```json
{
  "mcpServers": {
    "ckg": { "command": "uvx", "args": ["ckg-mcp"] }
  }
}
```
</details>

<details>
<summary><strong>LangChain / LangGraph / smolagents (Python)</strong></summary>

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient({
    "ckg": {"command": "ckg-mcp", "transport": "stdio"}
})
tools = await client.get_tools()
```
</details>

<details>
<summary><strong>OpenAI SDK</strong></summary>

```python
import subprocess, json
proc = subprocess.Popen(["ckg-mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
# Use any MCP-over-stdio adapter — e.g. mcp-client-python or openai-agents-mcp
```
</details>

Restart your client, then try:

```
list_domains()
get_prerequisites(domain="calculus", concept="Taylor Series")
query_ckg(domain="nvidia-gpu-inference", concept="FlashAttention-3", depth=3)
```

---

## What you get

**6 tools. No database. No embeddings. No API key.**

| Tool | What it does |
|------|--------------|
| `list_domains()` | List all available domains. **Call this first.** |
| `query_ckg(domain, concept, depth=3)` | Dependency subgraph around a concept — prerequisites + dependents up to N hops |
| `get_prerequisites(domain, concept)` | Full prerequisite chain — every concept to understand first, in order |
| `search_concepts(domain, query)` | Find concepts by name (partial match, case-insensitive) |
| `list_agent_blueprints()` | List pre-built agent configs for specific use cases |
| `get_agent_blueprint(use_case)` | Full blueprint: domains, constraints, workflow, prompt template, LangGraph hint |

### Example session

```
list_domains()
→ Available domains (62 free / 85 total): algebra-1, agent-reliability, calculus,
  context-as-a-service, databricks-unity, glp1-obesity, hipaa-compliance,
  nvidia-gpu-inference, payer-formulary, snowflake-horizon, ...

get_prerequisites(domain="calculus", concept="Taylor Series")
→ Prerequisite chain for 'Taylor Series' in calculus (20 concepts):
  Function → Limit → Derivative → ... → Power Series → Taylor Series

query_ckg(domain="nvidia-gpu-inference", concept="KV Cache", depth=3)
→ ## CKG: KV Cache (nvidia-gpu-inference)
  ### Prerequisites
  - Memory Bandwidth
    - HBM3 Memory (L2)
  - Transformer Attention
    - Scaled Dot-Product Attention (L2)
  ### Builds toward
  - PagedAttention
  - Continuous Batching
  - Speculative Decoding

list_agent_blueprints()
→ Agent blueprints (2):
    gpu-inference-optimizer: Diagnoses GPU inference bottlenecks and recommends optimizations
    context-as-a-service-advisor: Designs CaaS pipelines replacing RAG with CKG-based retrieval

get_agent_blueprint("gpu-inference-optimizer")
→ Full spec: required domains, constraints, 6-step workflow, prompt template, LangGraph state machine
```

---

## Free vs Pro

| | **Free** | **Pro — $99/mo** |
|---|---|---|
| Domains | 65 | 85 |
| Healthcare | — | HIPAA, CPT, ICD-10, drug interactions, payer formulary, modeling healthcare data |
| Enterprise data | — | Databricks Unity, Snowflake Horizon, PostgreSQL, AWS, Azure Purview, GCP Dataplex, dbt, OpenLineage |
| AI infrastructure | — | NVIDIA GPU inference, context-as-a-service, agent reliability, AI governance, token cost crisis |
| Agent blueprints | 2 included | 2 included + priority access to new ones |
| License | MIT | Commercial |

**Upgrade:** [graphifymd.com/pro](https://graphifymd.com/pro) — key delivered to your inbox, activate with one env var:

```bash
export CKG_API_KEY=your-license-key
# restart your MCP client — all 85 domains now appear in list_domains()
```

---

## Benchmark

Three architectures. Same questions. Open methodology.

| | **CKG (this tool)** | RAG | GraphRAG |
|---|---|---|---|
| Macro-F1 | **0.471** | 0.123 | 0.120 |
| Tokens / query | **269** | 2,982 | 3,450 |
| Cost / query | **$0.0010** | $0.0106 | — |
| F1 @ 5 hops | **0.772** | 0.170 | — |
| Fabricated edges | **0 — by construction** | variable | variable |

- **4× the F1 of RAG** at **11× fewer tokens**
- **~42× higher RDS** (Retrieval Density Score) — the compound efficiency metric
- **~10× cheaper** full query set ($7.81 vs $76.23)
- **Scales with depth**: CKG F1 rises from 0.37 → 0.77 at 5 hops; RAG is flat. Retrieval has no traversal mechanism.
- **GraphRAG ≈ RAG** (0.120 vs 0.123) — the word "graph" isn't the win. *Pre-structured, compiled* graphs are.

Also validated by independent academic benchmark: [arXiv:2603.14045](https://arxiv.org/abs/2603.14045) (Zarrinkia, Thomo, Srinivasan — U. Victoria / Santa Clara) finds **73–84% of Graph-RAG errors are reasoning failures**, not retrieval failures — the problem CKGs solve by construction.

### Reproducibility

```bash
git clone https://github.com/Yarmoluk/ckg-benchmark && cd ckg-benchmark
pip install -r evaluation/requirements.txt
python evaluation/ckg_harness.py --domain calculus
python evaluation/analyze_results.py
```

[Full benchmark paper →](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf)

---

## How it works

A Compressed Knowledge Graph is a plain-text `.csv` DAG — concepts, typed dependency edges, taxonomy tags — that the LLM reads directly:

```csv
ConceptID,ConceptLabel,Dependencies,TaxonomyID
1,Function,,FOUND
2,Domain and Range,1,FOUND
4,Composite Function,1|3,FOUND
```

`ckg-mcp` runs deterministic BFS/DFS over declared edges and returns the exact subgraph the agent asked for. Because the server only returns **edges that are declared in the data**, it cannot invent a relationship. The LLM still writes the answer in prose — the *knowledge* it reasons over is exact.

No graph database. No vector store. No retrieval pipeline. No inference at query time.

```
1M RAG tokens = 335 queries   (burning context at $0.013/query)
1M CKG tokens = 3,717 queries (11× compression — the same budget, 11× the coverage)
```

---

## Agent Blueprints (new in v0.6.0)

Blueprints are pre-built, domain-locked agent specifications: which CKG domains to load, workflow steps, constraints, a ready-to-use system prompt, example queries, and a LangGraph orchestration hint.

```
get_agent_blueprint("gpu-inference-optimizer")
→ Required domains: nvidia-gpu-inference, context-as-a-service
  Constraints: only traverse declared edges, cite concept IDs, flag gaps
  Workflow: 1. list_domains → 2. query_ckg bottleneck → 3. trace prereqs →
            4. identify optimization path → 5. recommend with citations
  Prompt template: [ready to paste]
  LangGraph hint: StateGraph with 4 nodes: diagnose, trace, optimize, report
```

---

## Bundled domains (65 free)

**AI tools** — claude-anthropic, claude-skills, conversational-ai, cursor, deepseek, gemini-api, grok-xai, kimi-moonshot, midjourney, moss, openai-platform, qwen
**STEM / math** — algebra-1, calculus, chemistry, circuits, computer-science, data-science-course, digital-electronics, ecology, fft-benchmarking, functions, genetics, geometry-course, intro-to-graph, intro-to-physics-course, linear-algebra, machine-learning-textbook, pre-calc, quantum-computing, signal-processing, statistics-course
**Life sciences** — biology, bioinformatics, dementia, drug-interactions, glp1-muscle-loss, glp1-obesity
**Pedagogy / tools** — automating-instructional-design, infographics, microsims, prompt-class, tracking-ai-course, vercel-ai-sdk, langchain-core
**Business / society** — art-of-war, blockchain, digital-citizenship, economics-course, ethics-course, it-management-graph, laudato-si, learning-linux, personal-finance, reading-for-kindergarten, systems-thinking, theory-of-knowledge, unicorns, us-geography, asl-book

**Pro only (23):** Healthcare · Enterprise data · AI infrastructure — [see full list →](https://graphifymd.com/pro)

---

## Compatibility

Model-agnostic — the graph is plain text, readable by any LLM:

| LLM | Agent framework | MCP client |
|-----|-----------------|------------|
| Claude (all tiers) | LangChain / LangGraph | Claude Desktop |
| GPT-4o / GPT-4 | AutoGen | Claude Code |
| Gemini 1.5 / 2.0 | smolagents | Cursor |
| Llama 3 / 3.1 | CrewAI | Cline |
| Mistral | Haystack | Windsurf |
| DeepSeek | OpenAI Agents SDK | Any MCP stdio client |

Python ≥ 3.10 · single dependency (`mcp`) · stdio transport · zero configuration

---

## License

MIT. Source learning graphs derive from the McCreary Intelligent Textbook Corpus.

## Citation

```bibtex
@misc{yarmoluk2026ckg,
  title  = {Benchmarking Knowledge Retrieval Architectures Across Educational
            and Commercial Domains: RAG, GraphRAG, and Compressed (Compact) Knowledge Graphs},
  author = {Yarmoluk, Daniel and McCreary, Dan},
  year   = {2026},
  note   = {v0.6.2. https://github.com/Yarmoluk/ckg-benchmark}
}
```

---

**Links:** [Benchmark](https://github.com/Yarmoluk/ckg-benchmark) · [Paper](https://github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf) · [Pro domains](https://graphifymd.com/pro) · [Graphify.md](https://graphifymd.com) · [arXiv:2603.14045](https://arxiv.org/abs/2603.14045)

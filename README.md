# ckg-mcp

[![PyPI](https://img.shields.io/pypi/v/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![Downloads](https://static.pepy.tech/badge/ckg-mcp/month)](https://pepy.tech/project/ckg-mcp)
[![Python](https://img.shields.io/pypi/pyversions/ckg-mcp)](https://pypi.org/project/ckg-mcp/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-server-blue)](https://modelcontextprotocol.io)
[![Benchmark](https://img.shields.io/badge/benchmark-reproducible-orange)](https://github.com/Yarmoluk/ckg-benchmark)

`mcp-name: io.github.Yarmoluk/ckg-mcp`

**Give your agent the structure, not the search.** `ckg-mcp` serves **Compressed Knowledge Graphs** — pre-structured, typed dependency graphs — to any MCP client. Instead of retrieving text chunks and hoping the model infers the relationships, your agent traverses *declared* edges: prerequisites, dependency chains, and category membership, returned as a tight subgraph.

On the open [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark), this approach scores **3.8× the F1 of RAG at 11× fewer tokens** — and unlike RAG, it **cannot fabricate a relationship that isn't in the graph**.

---

## Quickstart (30 seconds)

```bash
pip install ckg-mcp        # or: uvx ckg-mcp  (zero-install)
```

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ckg": {
      "command": "ckg-mcp"
    }
  }
}
```

**Claude Code** (CLI):

```bash
claude mcp add ckg -- ckg-mcp
```

**Cursor / Cline / Windsurf** — same block in your MCP settings:

```json
{ "mcpServers": { "ckg": { "command": "ckg-mcp" } } }
```

Prefer no global install? Swap the command for uvx:

```json
{ "mcpServers": { "ckg": { "command": "uvx", "args": ["ckg-mcp"] } } }
```

Restart the client. Ask your agent: *"Use the ckg tools — list the domains, then trace the prerequisite chain for 'Taylor Series' in calculus."*

---

## What you get

Four tools over **59 bundled domains** (no database, no embeddings, no API key):

| Tool | Signature | What it does |
|------|-----------|--------------|
| `list_domains` | `list_domains()` | List all available CKG domains. **Call this first.** |
| `query_ckg` | `query_ckg(domain, concept, depth=3)` | Extract the subgraph around a concept — related concepts up to `depth` hops. |
| `get_prerequisites` | `get_prerequisites(domain, concept)` | The full prerequisite chain — everything to understand first. |
| `search_concepts` | `search_concepts(domain, query)` | Find concepts in a domain by name. |

### Example

```
list_domains()
→ calculus, circuits, machine-learning-textbook, glp1-obesity, payer-formulary, google-dataplex, ... (59)

get_prerequisites(domain="calculus", concept="Taylor Series")
→ Function → Derivative → Higher-Order Derivatives → Power Series → Taylor Series
  (each edge is declared in the graph, not inferred from prose)

query_ckg(domain="circuits", concept="RC Discharging", depth=2)
→ subgraph: RC Discharging ← RC Circuit, Capacitor Energy Storage, Initial Conditions ...
```

---

## Why it beats retrieval

Three architectures, same questions, measured on the open [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark) (45 domains, 7,928 queries, fully reproducible):

| | **CKG** | RAG | GraphRAG |
|---|---|---|---|
| Macro-F1 | **0.47** | 0.12 | 0.12 |
| Tokens / query | **269** | 2,982 | 3,450 |
| F1 @ 5 hops | **0.772** | 0.170 | — |
| Fabricated edges | **0 by construction** | variable | variable |

- **3.8× the F1 of RAG**, at **11× fewer tokens** per query.
- **~42× higher RDS** (Retrieval Density Score = F1 per token) — the compound efficiency metric.
- **~10× cheaper** to run the full query set ($7.81 vs $76.23; ≈$0.0010 vs $0.0106 per query).
- **CKG strengthens with depth** (0.37 → 0.77 from hop 0 to hop 5); RAG stays flat and low — retrieval has no mechanism for traversing a chain.
- **GraphRAG is *not* better than RAG** here (0.120 vs 0.123, and *more* tokens). The win isn't "a graph" — it's a *pre-structured, compiled* graph.

> **Don't trust the numbers — re-run them:**
> ```bash
> git clone https://github.com/Yarmoluk/ckg-benchmark && cd ckg-benchmark
> pip install -r evaluation/requirements.txt
> python evaluation/ckg_harness.py --domain calculus
> python evaluation/analyze_results.py
> ```

---

## How it works

A Compressed Knowledge Graph is a plain-text `.csv`/`.md` DAG — entities, typed dependency edges, and taxonomy — that the LLM reads **directly**:

```csv
ConceptID,ConceptLabel,Dependencies,TaxonomyID
1,Function,,FOUND
2,Domain and Range,1,FOUND
4,Composite Function,1|3,FOUND
```

`ckg-mcp` does deterministic graph traversal (BFS/DFS) over these declared edges and hands the agent the exact subgraph it asked for. Because the server returns **declared edges, not generated text**, it cannot invent a relationship that isn't in the graph — that's what "**0 fabricated edges by construction**" means. (The LLM still writes the final answer in prose; the *knowledge* it reasons over is exact.)

No graph database. No vector store. No retrieval pipeline. Drop the server in, or drop a single `.md` into a system prompt.

---

## Bundled domains (59)

**Data catalog / governance** — google-dataplex, aws-data-catalog, azure-purview, databricks-unity, snowflake-horizon
**Life sciences / clinical** — glp1-obesity, glp1-muscle-loss, drug-interactions, dementia, icd10-metabolic, cpt-em-coding, hipaa-compliance, payer-formulary, modeling-healthcare-data, bioinformatics, genetics, biology
**STEM / math** — calculus, pre-calc, algebra-1, linear-algebra, geometry-course, statistics-course, functions, intro-to-physics-course, chemistry, ecology, signal-processing, fft-benchmarking
**Engineering / CS** — circuits, digital-electronics, computer-science, quantum-computing, machine-learning-textbook, langchain-core, claude-skills, data-science-course, it-management-graph, intro-to-graph
**AI / data / pedagogy** — conversational-ai, prompt-class, tracking-ai-course, automating-instructional-design, microsims, infographics, modeling-healthcare-data
**Business / society / other** — economics-course, personal-finance, organizational-analytics, ethics-course, theory-of-knowledge, systems-thinking, digital-citizenship, learning-linux, reading-for-kindergarten, us-geography, asl-book, moss, unicorns, blockchain

Need a domain we don't ship? Build your own CKG from a CSV, or ask about managed enterprise domains → [graphifymd.com](https://graphifymd.com).

---

## Compatibility

Works with any MCP client — Claude Desktop, Claude Code, Cursor, Cline, Windsurf — and any agent framework that speaks MCP (LangGraph, AutoGen, etc.). Model-agnostic: the graph is plain text, so it works equally with Claude, GPT, Llama, or a local model. Python ≥ 3.10, stdio transport, single dependency (`mcp`).

## Commercial

The open package ships 59 domains under MIT. Managed enterprise domains (clinical, regulatory, financial), weekly delta updates, and pilot engagements are available through **[Graphify.md](https://graphifymd.com)**.

## License

MIT. Source learning graphs derive from the McCreary Intelligent Textbook Corpus.

## Citation

```bibtex
@misc{yarmoluk2026ckg,
  title  = {Benchmarking Knowledge Retrieval Architectures Across Educational
            and Commercial Domains: RAG, GraphRAG, and Compact Knowledge Graphs},
  author = {Yarmoluk, Daniel and McCreary, Dan},
  year   = {2026},
  note   = {Pre-print in preparation. v0.6.2.}
}
```

**Links:** [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark) · [Paper](https://graphifymd.com/paper.html) · [Graphify.md](https://graphifymd.com)

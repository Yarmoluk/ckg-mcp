# ckg-mcp

mcp-name: io.github.Yarmoluk/ckg-mcp

**Compact Knowledge Graph MCP server.** Pre-structured domain knowledge as a routing layer for agent stacks — 65× more efficient than RAG on structural queries.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)]()
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)]()

> Built on the [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark) — 45 domains, 7,928 queries, fully reproducible results.

---

## What It Does

Drop CKG into your agent stack as an MCP tool. Instead of retrieving text chunks and hoping the LLM infers structure, CKG gives agents pre-compiled dependency paths, prerequisite chains, and concept relationships — directly from a structured graph.

| System | BERT F1 | Tokens/query | Hallucination Rate |
|--------|---------|-------------|-------------------|
| **CKG** | **0.857** | **274** | **0%** |
| RAG | 0.817 | 17,900 | Variable |
| GraphRAG | 0.825 | — | Variable |

65× more efficient per token. Higher accuracy than both RAG and Microsoft GraphRAG. Zero hallucinations by construction.

---

## Install

```bash
pip install ckg-mcp
```

## Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ckg": {
      "command": "ckg-mcp"
    }
  }
}
```

Works with Claude Desktop, LangGraph, AutoGen, or any MCP-compatible orchestrator.

---

## Tools

| Tool | Description |
|------|-------------|
| `list_domains()` | List all 53 available CKG domains |
| `query_ckg(domain, concept, depth)` | Extract subgraph — prerequisites + dependents up to N hops |
| `get_prerequisites(domain, concept)` | Full prerequisite chain to root |
| `search_concepts(domain, query)` | Find concepts by name |

---

## Example

```python
# In your agent — via MCP tool call
query_ckg(domain="glp1-obesity", concept="Prior Authorization", depth=3)

# Returns the full causal chain:
## CKG: Prior Authorization (glp1-obesity)

### Prerequisites (what gates this)
  - Payer formulary tier assignment
    - Cost-effectiveness of GLP-1RA therapy
      - GLP-1 receptor agonist drug class
  - Medical necessity criteria

### Builds toward
  - Formulary position
  - Coverage decision
```

Same interface for codebases:

```python
query_ckg(domain="langchain-core", concept="RunnableSequence", depth=2)
# Returns exact blast radius — 23 dependent modules — before your agent edits anything
```

---

## Bundled Domains (53 total)

**Life Sciences & Clinical**
`glp1-obesity` · `glp1-muscle-loss` · `drug-interactions` · `dementia` · `icd10-metabolic` · `modeling-healthcare-data` · `payer-formulary` · `cpt-em-coding` · `hipaa-compliance`

**Codebase & Software**
`langchain-core` · `computer-science` · `circuits` · `digital-electronics` · `blockchain` · `quantum-computing` · `claude-skills`

**Mathematics & STEM**
`calculus` · `algebra-1` · `linear-algebra` · `pre-calc` · `geometry-course` · `chemistry` · `biology` · `ecology` · `genetics` · `bioinformatics` · `physics` · `signal-processing` · `fft-benchmarking`

**AI & Data**
`machine-learning-textbook` · `data-science-course` · `conversational-ai` · `tracking-ai-course` · `prompt-class` · `intro-to-graph` · `systems-thinking` · `microsims`

**Business & Finance**
`economics-course` · `personal-finance` · `organizational-analytics` · `it-management-graph` · `unicorns`

**Education & Other**
`statistics-course` · `ethics-course` · `theory-of-knowledge` · `digital-citizenship` · `asl-book` · `reading-for-kindergarten` · `learning-linux` · `infographics` · `automating-instructional-design` · `functions` · `us-geography` · `moss`

Enterprise domains (regulatory, legal, financial, custom) → [graphifymd.com](https://graphifymd.com)

---

## Why Not RAG?

RAG retrieves text chunks and forces the LLM to infer structure. On multi-hop structural queries — prerequisites, dependency chains, blast radius — that inference fails.

CKG is a **pre-compiled routing layer**: dependency paths are already in the graph. BFS/DFS traversal, not similarity search. No hallucinations by construction.

Full benchmark: [github.com/Yarmoluk/ckg-benchmark](https://github.com/Yarmoluk/ckg-benchmark)

---

## License

MIT — Yarmoluk & McCreary, 2026. Commercial deployment → [graphifymd.com](https://graphifymd.com)

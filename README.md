# ckg-mcp

**Compact Knowledge Graph MCP server.** Pre-structured domain knowledge as a routing layer for agent stacks — 42× more efficient than RAG on structural queries.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)]()
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-purple.svg)]()

> Built on the [CKG Benchmark](https://github.com/Yarmoluk/ckg-benchmark) — 45 domains, 7,928 queries, fully reproducible results.

---

## What It Does

Drop CKG into your agent stack as an MCP tool. Instead of retrieving text chunks and hoping the LLM infers structure, CKG gives agents pre-compiled dependency paths, prerequisite chains, and concept relationships — directly from a structured graph.

| System | Macro F1 | Tokens/query | Hallucination Rate |
|--------|----------|-------------|-------------------|
| **CKG** | **0.471** | **269** | **0%** |
| RAG | 0.123 | 2,982 | Variable |
| GraphRAG | 0.120 | 3,450 | Variable |

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

---

## Tools

| Tool | Description |
|------|-------------|
| `list_domains()` | List all available CKG domains |
| `query_ckg(domain, concept, depth)` | Extract subgraph — prerequisites + dependents |
| `get_prerequisites(domain, concept)` | Full prerequisite chain to root |
| `search_concepts(domain, query)` | Find concepts by name |

---

## Bundled Domains (v0.1.0)

| Domain | Concepts |
|--------|---------|
| calculus | 105 |
| algebra-1 | 80 |
| chemistry | 95 |
| biology | 88 |
| linear-algebra | 72 |
| data-science-course | 91 |
| economics-course | 78 |
| glp1-obesity | 90 |

More domains available via [Graphify.md](https://graphifymd.com) — weekly-updated commercial CKGs for clinical, regulatory, legal, and financial domains.

---

## Example

```python
# In your agent — via MCP tool call
query_ckg(domain="calculus", concept="Taylor Series", depth=3)

# Returns:
## CKG: Taylor Series (calculus)

### Prerequisites (what you need to know first)
  - Power Series
    - Sequences and Series
      - Limits
  - Derivatives
  - Infinite Series

### Builds toward
  - Maclaurin Series
  - Error Estimation
```

---

## Why Not RAG?

RAG retrieves text chunks and forces the LLM to infer structure. On multi-hop structural queries (prerequisites, dependency chains, category aggregation), that inference fails — F1 = 0.123 vs CKG's 0.471.

CKG is a **pre-compiled routing layer**: the dependency paths are already in the graph. BFS/DFS traversal, not similarity search. No hallucinations by construction.

Full benchmark: [github.com/Yarmoluk/ckg-benchmark](https://github.com/Yarmoluk/ckg-benchmark)

---

## License

MIT — Yarmoluk & McCreary, 2026. Commercial deployment → [graphifymd.com](https://graphifymd.com)

from mcp.server.fastmcp import FastMCP
from .graph import available_domains, load_graph, find_concept, bfs_subgraph, prerequisite_chain

mcp = FastMCP(
    "ckg",
    instructions=(
        "Compact Knowledge Graph (CKG) server. Use list_domains to see available domains, "
        "then query_ckg or get_prerequisites to retrieve structured domain knowledge. "
        "CKG is a pre-structured routing layer — 42x more efficient than RAG on structural queries."
    ),
)


@mcp.tool()
def list_domains() -> str:
    """List all available CKG domains."""
    domains = available_domains()
    return f"Available domains ({len(domains)}): " + ", ".join(domains)


@mcp.tool()
def query_ckg(domain: str, concept: str, depth: int = 3) -> str:
    """
    Extract a CKG subgraph for a concept — returns related concepts up to `depth` hops.

    Args:
        domain: Domain name (use list_domains to see options)
        concept: Concept to query (e.g. "Taylor Series", "Semaglutide")
        depth: Hop depth for subgraph extraction (default 3, max 5)
    """
    depth = min(depth, 5)
    id_to_label, label_to_id, prerequisites, dependents, taxonomy = load_graph(domain)
    cid = find_concept(label_to_id, concept)
    if not cid:
        close = [l for l in label_to_id if concept.lower()[:4] in l][:5]
        return f"Concept '{concept}' not found in {domain}. Similar: {close}"

    prereq_nodes = bfs_subgraph(cid, prerequisites, id_to_label, depth)
    dep_nodes = bfs_subgraph(cid, dependents, id_to_label, 2)

    lines = [f"## CKG: {id_to_label[cid]} ({domain})", ""]
    lines.append("### Prerequisites (what you need to know first)")
    for node in prereq_nodes[1:]:
        indent = "  " * node["depth"]
        lines.append(f"{indent}- {node['concept']}")

    lines.append("")
    lines.append("### Builds toward (concepts that depend on this)")
    for node in dep_nodes[1:]:
        indent = "  " * node["depth"]
        lines.append(f"{indent}- {node['concept']}")

    tax = taxonomy.get(cid, "")
    if tax:
        lines.append(f"\nTaxonomy: {tax}")

    return "\n".join(lines)


@mcp.tool()
def get_prerequisites(domain: str, concept: str) -> str:
    """
    Get the full prerequisite chain for a concept — everything you need to know first.

    Args:
        domain: Domain name
        concept: Concept to trace back to roots
    """
    id_to_label, label_to_id, prerequisites, _, _ = load_graph(domain)
    cid = find_concept(label_to_id, concept)
    if not cid:
        return f"Concept '{concept}' not found in {domain}."

    chain = prerequisite_chain(cid, prerequisites, id_to_label)
    if len(chain) <= 1:
        return f"'{concept}' has no prerequisites in {domain} — it is a root concept."

    return (
        f"Prerequisite chain for '{chain[0]}' in {domain} ({len(chain) - 1} concepts):\n"
        + " → ".join(chain)
    )


@mcp.tool()
def search_concepts(domain: str, query: str) -> str:
    """
    Search for concepts in a domain by name.

    Args:
        domain: Domain name
        query: Partial concept name to search for
    """
    _, label_to_id, _, _, taxonomy = load_graph(domain)
    q = query.lower().strip()
    matches = [(label, cid) for label, cid in label_to_id.items() if q in label]
    if not matches:
        return f"No concepts matching '{query}' in {domain}."
    lines = [f"Concepts matching '{query}' in {domain}:"]
    for label, cid in sorted(matches)[:20]:
        tax = taxonomy.get(cid, "")
        lines.append(f"  - {label.title()}" + (f" [{tax}]" if tax else ""))
    return "\n".join(lines)


def main():
    mcp.run()

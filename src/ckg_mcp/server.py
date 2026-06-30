import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .graph import available_domains, load_graph, find_concept, bfs_subgraph, prerequisite_chain

AGENTS_DIR = Path(__file__).parent / "agents"

mcp = FastMCP(
    "ckg",
    instructions=(
        "Compressed Knowledge Graph (CKG) server: serves pre-structured, typed dependency "
        "graphs of domain concepts so an agent traverses declared relationships instead of "
        "inferring them. Workflow: call list_domains first to get valid domain names; use "
        "search_concepts to resolve a concept's exact label; then query_ckg for a concept's "
        "subgraph (prerequisites + dependents) or get_prerequisites for its full upstream "
        "chain. Every result is composed of edges declared in the graph — the server cannot "
        "return a relationship that is not in the data."
    ),
)


@mcp.tool()
def list_domains() -> str:
    """List every Compressed Knowledge Graph (CKG) domain this server can answer about.

    Call this FIRST, before the other tools. Each domain is a self-contained dependency
    graph for one subject area (e.g. "calculus", "google-dataplex", "glp1-obesity"). The
    `domain` argument required by query_ckg, get_prerequisites, and search_concepts must be
    an exact name returned here. Takes no arguments.

    Returns:
        One line: the domain count followed by the comma-separated domain names, e.g.
        "Available domains (65): algebra-1, aws-data-catalog, calculus, ...".
    """
    domains = available_domains()
    return f"Available domains ({len(domains)}): " + ", ".join(domains)


@mcp.tool()
def query_ckg(domain: str, concept: str, depth: int = 3) -> str:
    """Return the dependency subgraph around a concept: what it requires, and what builds on it.

    Use this for the local neighborhood of a concept — both the prerequisites it depends on
    and the downstream concepts that depend on it. For ONLY the upstream prerequisite chain,
    use get_prerequisites instead. If unsure of the exact concept name, call search_concepts
    first to find it.

    Args:
        domain: Exact domain name from list_domains (e.g. "calculus", "google-dataplex").
        concept: Concept to center the subgraph on. Matched case-insensitively; a partial
            name resolves to the first containing match (e.g. "taylor" -> "Taylor Series").
        depth: Upstream prerequisite hops to include, 1-5 (default 3; higher values are
            capped at 5). Downstream "builds toward" concepts are always included to 2 hops.

    Returns:
        A Markdown report titled with the resolved concept, with a "Prerequisites (what you
        need to know first)" tree and a "Builds toward (concepts that depend on this)" tree,
        plus the concept's taxonomy tag when present. If the concept is not found, returns a
        message listing up to 5 similar names to retry with.
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
    """Return the full ordered chain of concepts to understand before a target concept.

    Use this for onboarding, gap-filling, or sequencing study — it walks every upstream
    dependency back to the root concepts. For a two-directional neighborhood (prerequisites
    AND dependents) use query_ckg; to resolve an exact concept name use search_concepts.

    Args:
        domain: Exact domain name from list_domains.
        concept: Target concept to trace back to its roots. Matched case-insensitively; a
            partial name resolves to the first containing match.

    Returns:
        One line listing the prerequisite chain in dependency order, e.g. "Prerequisite chain
        for 'Taylor Series' in calculus (5 concepts): Function -> Derivative -> ... -> Taylor
        Series". States that the concept is a root if it has no prerequisites, or that it was
        not found.
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
    """Find concepts in a domain by partial name — use this to discover exact concept labels.

    Run this before query_ckg or get_prerequisites when you do not know the precise label a
    concept is stored under. Does a case-insensitive substring match over every concept name
    in the domain.

    Args:
        domain: Exact domain name from list_domains.
        query: Substring to match against concept names (e.g. "mask", "iceberg", "lineage").

    Returns:
        Up to 20 matching concept names (title-cased), each annotated with its taxonomy tag in
        brackets when present, e.g. "  - Masking Policy [GOV]". Returns a "no concepts matching"
        message when there are no matches.
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


@mcp.tool()
def list_agent_blueprints() -> str:
    """List available domain-locked agent blueprints — pre-built orchestration configs for specific use cases.

    Each blueprint bundles: required CKG domains, agent constraints, workflow steps, a prompt
    template, and an orchestration hint (LangGraph state machine). Use get_agent_blueprint to
    retrieve the full spec for a specific use case.

    Returns:
        Available blueprint names and one-line descriptions.
    """
    if not AGENTS_DIR.exists():
        return "No agent blueprints available."
    blueprints = []
    for p in sorted(AGENTS_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            blueprints.append(f"  {p.stem}: {data.get('description', '')[:80]}")
        except Exception:
            pass
    if not blueprints:
        return "No agent blueprints available."
    return f"Agent blueprints ({len(blueprints)}):\n" + "\n".join(blueprints)


@mcp.tool()
def get_agent_blueprint(use_case: str) -> str:
    """Return the full domain-locked agent blueprint for a specific use case.

    A blueprint is a complete locked-agent specification: which CKG domains to load,
    what constraints the agent must enforce, the step-by-step workflow, a ready-to-use
    system prompt template, example queries, and an orchestration hint for LangGraph or
    similar frameworks. Use list_agent_blueprints to see available use cases.

    Args:
        use_case: Blueprint name from list_agent_blueprints (e.g. "gpu-inference-optimizer").

    Returns:
        Full blueprint as formatted Markdown including constraints, workflow, prompt template,
        example queries, and agent map (orchestration hints + guardrails).
    """
    path = AGENTS_DIR / f"{use_case}.json"
    if not path.exists():
        available = [p.stem for p in AGENTS_DIR.glob("*.json")]
        return f"Blueprint '{use_case}' not found. Available: {available}"
    data = json.loads(path.read_text())

    lines = [
        f"## Agent Blueprint: {data['use_case']} (v{data['version']})",
        f"\n{data['description']}",
        f"\n**Required domains:** {', '.join(data['required_domains'])}",
        "\n### Constraints",
    ]
    for k, v in data.get("constraints", {}).items():
        lines.append(f"- **{k}**: {v}")

    lines.append("\n### Workflow Steps")
    for step in data.get("workflow_steps", []):
        lines.append(f"{step}")

    lines.append("\n### Prompt Template")
    lines.append(f"```\n{data.get('prompt_template', '')}\n```")

    lines.append("\n### Example Queries")
    for q in data.get("example_queries", []):
        lines.append(f"- {q}")

    agent_map = data.get("agent_map", {})
    if agent_map:
        lines.append("\n### Agent Map (Orchestration)")
        lines.append(f"- **Orchestration:** {agent_map.get('orchestration_hint', '')}")
        lines.append(f"- **Tool sequence:** {' → '.join(agent_map.get('tool_sequence', []))}")
        lines.append(f"- **Exit condition:** {agent_map.get('exit_condition', '')}")
        lines.append("- **Guardrails:**")
        for g in agent_map.get("guardrails", []):
            lines.append(f"  - {g}")

    return "\n".join(lines)


def _first_run_notice() -> None:
    sentinel = Path.home() / ".ckg-mcp" / ".welcomed"
    if sentinel.exists():
        return
    sentinel.parent.mkdir(exist_ok=True)
    sentinel.touch()
    import sys
    print(
        "\n━━━ ckg-mcp | Context as a Service ━━━━━━━━━━━━━━━━\n"
        "  65 domains live. Hosted endpoint + private CKGs:\n"
        "  graphifymd.com/caas\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        file=sys.stderr,
    )


def main():
    _first_run_notice()
    mcp.run()

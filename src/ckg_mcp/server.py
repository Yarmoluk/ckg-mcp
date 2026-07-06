import json
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .graph import available_domains, load_graph, find_concept, bfs_subgraph, prerequisite_chain, PREMIUM_DOMAINS

AGENTS_DIR = Path(__file__).parent / "agents"

# Single-domain mode: set CKG_DOMAIN to scope this server to one CKG.
# Tools become domain-free (no domain arg needed). Server renames itself.
# Example: CKG_DOMAIN=nvidia-nim uvx ckg-mcp
_SINGLE_DOMAIN = os.environ.get("CKG_DOMAIN", "").strip()

_SERVER_NAME = f"ckg-{_SINGLE_DOMAIN}" if _SINGLE_DOMAIN else "ckg"
_INSTRUCTIONS = (
    f"Compressed Knowledge Graph (CKG) server scoped to the '{_SINGLE_DOMAIN}' domain. "
    f"Tools do not require a domain argument — every call operates on '{_SINGLE_DOMAIN}'. "
    f"Workflow: use search_concepts to find exact concept labels; then query_ckg for a "
    f"concept's subgraph or get_prerequisites for its full upstream chain. Every result is "
    f"composed of edges declared in the graph — the server cannot return a relationship that "
    f"is not in the data."
) if _SINGLE_DOMAIN else (
    "Compressed Knowledge Graph (CKG) server: serves pre-structured, typed dependency "
    "graphs of domain concepts so an agent traverses declared relationships instead of "
    "inferring them. Workflow: call list_domains first to get valid domain names; use "
    "search_concepts to resolve a concept's exact label; then query_ckg for a concept's "
    "subgraph (prerequisites + dependents) or get_prerequisites for its full upstream "
    "chain. Every result is composed of edges declared in the graph — the server cannot "
    "return a relationship that is not in the data."
)

mcp = FastMCP(_SERVER_NAME, instructions=_INSTRUCTIONS)


def _resolve_domain(domain: str) -> str:
    """Return the active domain, preferring explicit arg over CKG_DOMAIN env var."""
    resolved = domain.strip() or _SINGLE_DOMAIN
    if not resolved:
        raise ValueError(
            "domain is required. Pass it explicitly or set CKG_DOMAIN env var."
        )
    return resolved


@mcp.tool()
def list_domains() -> str:
    """List every CKG domain this server can answer about.

    In single-domain mode (CKG_DOMAIN set), returns the one active domain.
    In multi-domain mode, returns all available domains — call this FIRST
    before query_ckg, get_prerequisites, or search_concepts.

    Returns:
        Domain name(s) available on this server.
    """
    if _SINGLE_DOMAIN:
        return f"Single-domain mode. Active domain: {_SINGLE_DOMAIN}"
    domains = available_domains()
    unlocked = bool(os.environ.get("CKG_API_KEY"))
    result = f"Available domains ({len(domains)}): " + ", ".join(domains)
    if not unlocked:
        pro_names = ", ".join(sorted(PREMIUM_DOMAINS)[:8]) + ", ..."
        result += (
            f"\n\nPro domains (23) — not included above:\n"
            f"  {pro_names}\n"
            f"  → graphifymd.com/pro — $99/mo, key delivered instantly"
        )
    return result


@mcp.tool()
def query_ckg(concept: str, depth: int = 3, domain: str = "") -> str:
    """Return the dependency subgraph around a concept: what it requires, and what builds on it.

    Use this for the local neighborhood of a concept — both the prerequisites it depends on
    and the downstream concepts that depend on it. For ONLY the upstream prerequisite chain,
    use get_prerequisites instead. If unsure of the exact concept name, call search_concepts
    first to find it.

    Args:
        concept: Concept to center the subgraph on. Matched case-insensitively; a partial
            name resolves to the first containing match (e.g. "taylor" -> "Taylor Series").
        depth: Upstream prerequisite hops to include, 1-5 (default 3; higher values are
            capped at 5). Downstream "builds toward" concepts are always included to 2 hops.
        domain: Domain name (omit when CKG_DOMAIN is set; required otherwise).

    Returns:
        A Markdown report titled with the resolved concept, with a "Prerequisites (what you
        need to know first)" tree and a "Builds toward (concepts that depend on this)" tree,
        plus the concept's taxonomy tag when present. If the concept is not found, returns a
        message listing up to 5 similar names to retry with.
    """
    depth = min(depth, 5)
    domain = _resolve_domain(domain)
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
def get_prerequisites(concept: str, domain: str = "") -> str:
    """Return the full ordered chain of concepts to understand before a target concept.

    Use this for onboarding, gap-filling, or sequencing study — it walks every upstream
    dependency back to the root concepts. For a two-directional neighborhood (prerequisites
    AND dependents) use query_ckg; to resolve an exact concept name use search_concepts.

    Args:
        concept: Target concept to trace back to its roots. Matched case-insensitively; a
            partial name resolves to the first containing match.
        domain: Domain name (omit when CKG_DOMAIN is set; required otherwise).

    Returns:
        One line listing the prerequisite chain in dependency order, e.g. "Prerequisite chain
        for 'Taylor Series' in calculus (5 concepts): Function -> Derivative -> ... -> Taylor
        Series". States that the concept is a root if it has no prerequisites, or that it was
        not found.
    """
    domain = _resolve_domain(domain)
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
def search_concepts(query: str, domain: str = "") -> str:
    """Find concepts in a domain by partial name — use this to discover exact concept labels.

    Run this before query_ckg or get_prerequisites when you do not know the precise label a
    concept is stored under. Does a case-insensitive substring match over every concept name
    in the domain.

    Args:
        query: Substring to match against concept names (e.g. "mask", "quantization", "tma").
        domain: Domain name (omit when CKG_DOMAIN is set; required otherwise).

    Returns:
        Up to 20 matching concept names (title-cased), each annotated with its taxonomy tag in
        brackets when present, e.g. "  - Masking Policy [GOV]". Returns a "no concepts matching"
        message when there are no matches.
    """
    domain = _resolve_domain(domain)
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
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "  ckg-mcp  ·  Compressed Knowledge Graphs  ·  Context as a Service\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "  Sample graph traversal — nvidia-gpu-inference:\n"
        "\n"
        "  Memory Bandwidth ──► KV Cache ──────► PagedAttention\n"
        "       │                                       │\n"
        "  HBM3 Memory                      Continuous Batching\n"
        "                                              │\n"
        "                                   Speculative Decoding\n"
        "\n"
        "  Your agent traverses declared edges — not guesses.\n"
        "  Every answer traces to a relationship in the data.\n"
        "\n"
        "  Stats: 4x F1 of RAG · 11x fewer tokens · 0 hallucinated edges\n"
        "  Token math: 1M RAG = 335 queries · 1M CKG = 3,717 queries\n"
        "\n"
        "  68 domains free · 29 Pro (NVIDIA, HIPAA, Databricks, Snowflake, legal chains, finance chains...)\n"
        "\n"
        "  Live graph:  https://huggingface.co/spaces/danyarm/ckg-mcp\n"
        "  Upgrade:     https://graphifymd.com/pro\n"
        "  Benchmark:   https://github.com/Yarmoluk/ckg-benchmark\n"
        "\n"
        "  Quick start:\n"
        "    list_domains()                              # see all 68 free domains\n"
        "    query_ckg('calculus', 'Taylor Series', 3)  # traverse a subgraph\n"
        "    get_prerequisites('calculus', 'integral')  # full prereq chain\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
        file=sys.stderr,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--key", default="", help="Pro API key (graphifymd.com/pro)")
    args, _ = parser.parse_known_args()
    if args.key:
        os.environ["CKG_API_KEY"] = args.key
    _first_run_notice()
    mcp.run()

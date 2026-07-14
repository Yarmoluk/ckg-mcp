import csv
import json
import os
import time
import urllib.request
from collections import defaultdict, deque
from pathlib import Path

_VALIDATE_URL = "https://graphifymd.com/api/validate-license"
_GRAPH_API_URL = "https://graphifymd.com/api/graph"
_CACHE_FILE = Path.home() / ".ckg-mcp" / "license_cache.json"
_CACHE_TTL = 86400  # 24 hours

DOMAINS_DIR = Path(__file__).parent / "domains"

# In-memory graph cache — avoid redundant API calls within a session
_GRAPH_CACHE: dict = {}

PREMIUM_DOMAINS: frozenset[str] = frozenset({
    # Healthcare & clinical
    "payer-formulary",
    "icd10-metabolic",
    "cpt-em-coding",
    "hipaa-compliance",
    "hipaa-ai",
    "drug-interactions",
    "modeling-healthcare-data",
    # Enterprise data stack
    "databricks-unity",
    "snowflake-horizon",
    "postgresql",
    "sql-dialect-portability",
    "aws-data-catalog",
    "azure-purview",
    "google-dataplex",
    "open-catalog-endpoints",
    "openlineage",
    "knowledge-layer-standards",
    # AI infrastructure (new in v0.6)
    "nvidia-gpu-inference",
    "context-as-a-service",
    "agent-reliability",
    "ai-governance",
    "organizational-analytics",
    "token-cost-crisis",
    # Legal (agent hallucination hotspots)
    "legal-citation-chain",
    "contract-law-elements",
    # Healthcare chains
    "clinical-decision-chain",
    "medical-billing-chain",
    # Finance & compliance chains
    "aml-kyc-chain",
    "investment-risk-chain",
    # Salesforce AgentForce stack
    "agentforce-developer",
    "agentforce-vibes",
    "einstein-trust-layer",
    "data-cloud",
})


def _is_valid_key(key: str) -> bool:
    if not key:
        return False
    # 1. Local allowlist override (for self-hosted or enterprise)
    valid_env = os.environ.get("CKG_VALID_KEYS", "")
    if valid_env:
        return key in {k.strip() for k in valid_env.split(",") if k.strip()}
    # 2. Read cached result (avoid network call on every startup)
    try:
        if _CACHE_FILE.exists():
            cached = json.loads(_CACHE_FILE.read_text())
            if cached.get("key") == key and time.time() - cached.get("ts", 0) < _CACHE_TTL:
                return cached.get("valid", False)
    except Exception:
        pass
    # 3. Online validation
    try:
        url = f"{_VALIDATE_URL}?key={key}"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read())
        valid = bool(data.get("valid"))
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps({"key": key, "valid": valid, "ts": time.time()}))
        return valid
    except Exception:
        # Fail open — don't block users on network hiccup; cache is authoritative
        if _CACHE_FILE.exists():
            try:
                cached = json.loads(_CACHE_FILE.read_text())
                if cached.get("key") == key:
                    return cached.get("valid", False)
            except Exception:
                pass
        return False


def available_domains() -> list[str]:
    key = os.environ.get("CKG_API_KEY", "")
    unlocked = _is_valid_key(key)
    return sorted(
        p.stem for p in DOMAINS_DIR.glob("*.csv")
        if unlocked or p.stem not in PREMIUM_DOMAINS
    )


def _parse_graph_nodes(nodes: list) -> tuple:
    """Parse the JSON node list from the API into the same tuple load_graph returns."""
    id_to_label: dict = {}
    label_to_id: dict = {}
    prerequisites: dict = defaultdict(list)
    dependents: dict = defaultdict(list)
    taxonomy: dict = {}
    for node in nodes:
        cid = node["id"]
        label = node["label"]
        id_to_label[cid] = label
        label_to_id[label.lower()] = cid
        taxonomy[cid] = node.get("taxonomy", "")
        deps = node.get("deps", [])
        prerequisites[cid] = deps
        for dep_str in deps:
            dep_id = dep_str.split(":")[0]
            dependents[dep_id].append(cid)
    return id_to_label, label_to_id, prerequisites, dependents, taxonomy


def _fetch_graph_from_api(domain: str, key: str) -> tuple | None:
    """Fetch a Pro domain graph from the graphifymd.com API. Returns parsed tuple or None on error."""
    try:
        req = urllib.request.Request(
            f"{_GRAPH_API_URL}/{domain}",
            headers={"Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return _parse_graph_nodes(data["nodes"])
    except Exception:
        return None


def load_graph(domain: str):
    if domain in _GRAPH_CACHE:
        return _GRAPH_CACHE[domain]

    key = os.environ.get("CKG_API_KEY", "")

    if domain in PREMIUM_DOMAINS:
        if not _is_valid_key(key):
            raise ValueError(
                f"Domain '{domain}' is a Pro domain. "
                "Unlock at graphifymd.com/pro/ — $99/mo, key delivered instantly. "
                "Set CKG_API_KEY=<your-key> to activate."
            )
        # Try API first — graph data is served remotely, never bundled in the wheel
        result = _fetch_graph_from_api(domain, key)
        if result is not None:
            _GRAPH_CACHE[domain] = result
            return result
        # Fallback: local CSV if present (offline / legacy)

    csv_path = DOMAINS_DIR / f"{domain}.csv"
    if not csv_path.exists():
        if domain in PREMIUM_DOMAINS:
            raise ValueError(
                f"Domain '{domain}' could not be fetched from the API and no local copy exists. "
                "Check your network connection or contact support@graphifymd.com."
            )
        raise ValueError(f"Domain '{domain}' not found. Available: {available_domains()}")

    id_to_label: dict = {}
    label_to_id: dict = {}
    prerequisites: dict = defaultdict(list)
    dependents: dict = defaultdict(list)
    taxonomy: dict = {}

    with open(csv_path) as f:
        for row in csv.DictReader(f):
            cid = row["ConceptID"]
            label = row["ConceptLabel"].strip()
            deps = [d.strip() for d in row["Dependencies"].split("|") if d.strip()]
            id_to_label[cid] = label
            label_to_id[label.lower()] = cid
            taxonomy[cid] = row.get("TaxonomyID", "").strip()
            prerequisites[cid] = deps
            for dep in deps:
                dependents[_dep_id(dep)].append(cid)

    result = id_to_label, label_to_id, prerequisites, dependents, taxonomy
    _GRAPH_CACHE[domain] = result
    return result


def find_concept(label_to_id: dict, query: str) -> str | None:
    q = query.lower().strip()
    if q in label_to_id:
        return label_to_id[q]
    for label, cid in label_to_id.items():
        if q in label:
            return cid
    return None


def _dep_id(dep_str: str) -> str:
    """Extract concept ID from a dependency string — handles both '5' and '5:REQUIRES:0.95'."""
    return dep_str.split(":")[0] if ":" in dep_str else dep_str


def bfs_subgraph(start_id: str, adj: dict, id_to_label: dict, max_depth: int) -> list[dict]:
    visited = set()
    queue = deque([(start_id, 0)])
    results = []
    while queue:
        cid, depth = queue.popleft()
        cid = _dep_id(cid)
        if cid in visited or depth > max_depth:
            continue
        visited.add(cid)
        neighbors = adj.get(cid, [])
        results.append({
            "concept": id_to_label.get(cid, cid),
            "related": [id_to_label.get(_dep_id(n), _dep_id(n)) for n in neighbors],
            "depth": depth,
        })
        for n in neighbors:
            n_id = _dep_id(n)
            if n_id not in visited:
                queue.append((n_id, depth + 1))
    return results


def prerequisite_chain(start_id: str, prerequisites: dict, id_to_label: dict) -> list[str]:
    visited = set()
    queue = deque([start_id])
    chain = []
    while queue:
        cid = queue.popleft()
        cid = _dep_id(cid)
        if cid in visited:
            continue
        visited.add(cid)
        chain.append(id_to_label.get(cid, cid))
        for p in prerequisites.get(cid, []):
            p_id = _dep_id(p)
            if p_id not in visited:
                queue.append(p_id)
    return chain

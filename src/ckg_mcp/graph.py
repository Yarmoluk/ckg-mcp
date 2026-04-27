import csv
from collections import defaultdict, deque
from pathlib import Path

DOMAINS_DIR = Path(__file__).parent / "domains"


def available_domains() -> list[str]:
    return sorted(p.stem for p in DOMAINS_DIR.glob("*.csv"))


def load_graph(domain: str):
    csv_path = DOMAINS_DIR / f"{domain}.csv"
    if not csv_path.exists():
        raise ValueError(f"Domain '{domain}' not found. Available: {available_domains()}")

    id_to_label = {}
    label_to_id = {}
    prerequisites = defaultdict(list)
    dependents = defaultdict(list)
    taxonomy = {}

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
                dependents[dep].append(cid)

    return id_to_label, label_to_id, prerequisites, dependents, taxonomy


def find_concept(label_to_id: dict, query: str) -> str | None:
    q = query.lower().strip()
    if q in label_to_id:
        return label_to_id[q]
    for label, cid in label_to_id.items():
        if q in label:
            return cid
    return None


def bfs_subgraph(start_id: str, adj: dict, id_to_label: dict, max_depth: int) -> list[dict]:
    visited = set()
    queue = deque([(start_id, 0)])
    results = []
    while queue:
        cid, depth = queue.popleft()
        if cid in visited or depth > max_depth:
            continue
        visited.add(cid)
        neighbors = adj.get(cid, [])
        results.append({
            "concept": id_to_label.get(cid, cid),
            "related": [id_to_label.get(n, n) for n in neighbors],
            "depth": depth,
        })
        for n in neighbors:
            if n not in visited:
                queue.append((n, depth + 1))
    return results


def prerequisite_chain(start_id: str, prerequisites: dict, id_to_label: dict) -> list[str]:
    visited = set()
    queue = deque([start_id])
    chain = []
    while queue:
        cid = queue.popleft()
        if cid in visited:
            continue
        visited.add(cid)
        chain.append(id_to_label.get(cid, cid))
        for p in prerequisites.get(cid, []):
            if p not in visited:
                queue.append(p)
    return chain

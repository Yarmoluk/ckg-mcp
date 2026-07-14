#!/usr/bin/env python3
"""
Convert Pro domain CSVs → data/pro-graphs.json for the Vercel API endpoint.
Run after adding or updating any Pro domain CSV.

Usage:
    python3 scripts/build_pro_graphs_json.py
    # outputs: /Users/danielyarmoluk/projects/graphifymd/data/pro-graphs.json
"""
import csv
import json
from pathlib import Path

DOMAINS_DIR = Path(__file__).parent.parent / "src" / "ckg_mcp" / "domains"
OUT_FILE = Path(__file__).parent.parent.parent / "graphifymd" / "data" / "pro-graphs.json"

PREMIUM_DOMAINS = {
    "payer-formulary", "icd10-metabolic", "cpt-em-coding", "hipaa-compliance",
    "hipaa-ai", "drug-interactions", "modeling-healthcare-data",
    "databricks-unity", "snowflake-horizon", "postgresql", "sql-dialect-portability",
    "aws-data-catalog", "azure-purview", "google-dataplex", "open-catalog-endpoints",
    "openlineage", "knowledge-layer-standards", "nvidia-gpu-inference",
    "context-as-a-service", "agent-reliability", "ai-governance",
    "organizational-analytics", "token-cost-crisis", "legal-citation-chain",
    "contract-law-elements", "clinical-decision-chain", "medical-billing-chain",
    "aml-kyc-chain", "investment-risk-chain",
    "agentforce-developer", "agentforce-vibes", "einstein-trust-layer", "data-cloud",
}

def build():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    graphs = {}

    for domain in sorted(PREMIUM_DOMAINS):
        csv_path = DOMAINS_DIR / f"{domain}.csv"
        if not csv_path.exists():
            print(f"  SKIP {domain} (no CSV)")
            continue

        nodes = []
        with open(csv_path) as f:
            for row in csv.DictReader(f):
                deps = [d.strip() for d in row.get("Dependencies", "").split("|") if d.strip()]
                node = {
                    "id": row["ConceptID"],
                    "label": row["ConceptLabel"].strip(),
                    "taxonomy": row.get("TaxonomyID", "").strip(),
                    "deps": deps,
                }
                if "SourceURL" in row and row["SourceURL"].strip():
                    node["source_url"] = row["SourceURL"].strip()
                nodes.append(node)

        graphs[domain] = {"nodes": nodes}
        print(f"  OK  {domain} ({len(nodes)} nodes)")

    OUT_FILE.write_text(json.dumps(graphs, indent=2))
    total = sum(len(g["nodes"]) for g in graphs.values())
    print(f"\nWrote {len(graphs)} domains / {total} nodes → {OUT_FILE}")

if __name__ == "__main__":
    build()

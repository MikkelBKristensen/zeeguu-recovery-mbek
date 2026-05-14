# reflexion.py — compares source view against hypothetical view (Murphy & Notkin, 2001)
# Produces convergences, divergences, and absences at group level.

import json
from collections import defaultdict
from pathlib import Path

ANALYSIS_DIR = Path(__file__).parent

with open(ANALYSIS_DIR / "graph.json", encoding="utf-8") as f:
    graph = json.load(f)

# Noise nodes excluded from group-level comparison (same set as graph.html)
HIDE_NODES = {
    "logging", "core", "api", "config", "config.loader",
    "core.constants", "core.sql", "core.utils", "core.user_feature_toggles",
    "core.word_filter", "core.word_stats", "core.events",
    "api.app", "cl", "__init__", "operations", "operations.monitoring",
}

id_to_group = {
    n["id"]: n["group"]
    for n in graph["nodes"]
    if n["id"] not in HIDE_NODES
}

# Aggregate subpackage edges to group level; source_edges[A][B] = evidence list
source_edges: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

def _link_id(val):
    return val if isinstance(val, str) else val["id"]

for link in graph["links"]:
    src_id = _link_id(link["source"])
    tgt_id = _link_id(link["target"])
    if src_id in HIDE_NODES or tgt_id in HIDE_NODES:
        continue
    src_grp = id_to_group.get(src_id, "other")
    tgt_grp = id_to_group.get(tgt_id, "other")
    if src_grp != tgt_grp:
        source_edges[src_grp][tgt_grp].append((src_id, tgt_id))

# Expected group-level dependencies derived from archlens.json and domain knowledge.
# Any edge present in source but absent here is a divergence; any listed here
# but absent from source is an absence.
HYPOTHETICAL: set[tuple[str, str]] = {
    ("api",        "learning-system"),
    ("api",        "user-management"),
    ("api",        "content-pipeline"),
    ("api",        "language-processing"),
    ("api",        "audio-lessons"),
    ("api",        "data-layer"),
    ("api",        "operations"),
    ("api",        "other"),
    ("operations", "content-pipeline"),
    ("operations", "learning-system"),
    ("operations", "user-management"),
    ("operations", "data-layer"),
    ("operations", "language-processing"),
    ("operations", "other"),
    ("learning-system", "data-layer"),
    ("learning-system", "language-processing"),
    ("learning-system", "user-management"),
    ("learning-system", "content-pipeline"),
    ("learning-system", "other"),
    ("user-management", "data-layer"),
    ("user-management", "learning-system"),
    ("user-management", "other"),
    ("content-pipeline", "data-layer"),
    ("content-pipeline", "language-processing"),
    ("content-pipeline", "other"),
    ("language-processing", "data-layer"),
    ("language-processing", "other"),
    ("audio-lessons", "data-layer"),
    ("audio-lessons", "language-processing"),
    ("audio-lessons", "learning-system"),
    ("audio-lessons", "other"),
    ("other", "data-layer"),
}

# Classify each group pair as convergence, divergence, or absence
all_pairs: set[tuple[str, str]] = set(HYPOTHETICAL)
for a in source_edges:
    for b in source_edges[a]:
        all_pairs.add((a, b))

results = []
for (a, b) in sorted(all_pairs):
    in_hypo   = (a, b) in HYPOTHETICAL
    in_source = bool(source_edges[a][b])
    if in_hypo and in_source:
        verdict = "CONVERGENCE"
    elif in_source and not in_hypo:
        verdict = "DIVERGENCE"
    else:
        verdict = "ABSENCE"
    results.append({"from": a, "to": b, "verdict": verdict,
                    "evidence": source_edges[a][b]})

convergences = [r for r in results if r["verdict"] == "CONVERGENCE"]
divergences  = [r for r in results if r["verdict"] == "DIVERGENCE"]
absences     = [r for r in results if r["verdict"] == "ABSENCE"]

print(f"\nReflexion Model — Zeeguu-API")
print(f"{'='*40}")
print(f"  Convergences : {len(convergences)}")
print(f"  Divergences  : {len(divergences)}")
print(f"  Absences     : {len(absences)}\n")

if divergences:
    print("DIVERGENCES:")
    for r in divergences:
        pkgs = ", ".join(f"{s}->{t}" for s, t in r["evidence"][:3])
        more = f" (+{len(r['evidence'])-3} more)" if len(r["evidence"]) > 3 else ""
        print(f"  {r['from']:20s} --> {r['to']:20s}  [{pkgs}{more}]")

if absences:
    print("\nABSENCES:")
    for r in absences:
        print(f"  {r['from']:20s} --> {r['to']:20s}")

# Write markdown table
md_lines = [
    "# Reflexion Model — Zeeguu-API", "",
    "| From | To | Verdict | Evidence |",
    "|------|----|---------|----------|",
]
for r in results:
    ev = "; ".join(f"`{s}` -> `{t}`" for s, t in r["evidence"][:2])
    if len(r["evidence"]) > 2:
        ev += f" (+{len(r['evidence'])-2} more)"
    md_lines.append(f"| {r['from']} | {r['to']} | **{r['verdict']}** | {ev or '(none)'} |")

out_path = ANALYSIS_DIR / "reflexion.md"
out_path.write_text("\n".join(md_lines), encoding="utf-8")
print(f"\nWrote: {out_path}")

json_out = ANALYSIS_DIR / "reflexion.json"
json_out.write_text(json.dumps({
    "results": results,
    "summary": {"convergences": len(convergences),
                "divergences":  len(divergences),
                "absences":     len(absences)},
}, indent=2), encoding="utf-8")
print(f"Wrote: {json_out}")

# extract_deps.py — AST-based dependency extractor for Zeeguu-API
# Outputs edges.csv, metrics.csv, graph.json, and module_view.dot

import ast
import io
import os
import csv
import json
import tokenize
from collections import defaultdict
from pathlib import Path

REPO_ROOT   = Path("PATH/TO/ZEEGUU-API")  # replace with local path to the Zeeguu-API repo
SOURCE_ROOT = REPO_ROOT / "zeeguu"
OUTPUT_DIR  = Path(__file__).parent

EXCLUDE_DIRS = {"test", "tests", "diagrams"}

# Group assignments derived from archlens.json (used for reflexion model and D3 colours)
ARCHLENS_GROUPS: dict[str, str] = {
    "core.word_scheduling":      "learning-system",
    "core.exercises":            "learning-system",
    "core.bookmark_quality":     "learning-system",
    "core.bookmark_operations":  "learning-system",
    "core.behavioral_modeling":  "learning-system",
    "core.reading_analysis":     "learning-system",
    "core.tokenization":         "language-processing",
    "core.nlp_pipeline":         "language-processing",
    "core.language":             "language-processing",
    "core.ml_models":            "language-processing",
    "core.llm_services":         "language-processing",
    "core.semantic_search":      "language-processing",
    "core.semantic_vector_api":  "language-processing",
    "core.mwe":                  "language-processing",
    "core.translation_services": "language-processing",
    "core.crowd_translations":   "language-processing",
    "core.account_management":   "user-management",
    "core.user_statistics":      "user-management",
    "core.user_activity_hooks":  "user-management",
    "core.friends":              "user-management",
    "core.leaderboards":         "user-management",
    "core.badges":               "user-management",
    "core.emailer":              "user-management",
    "core.feed_handler":         "content-pipeline",
    "core.content_retriever":    "content-pipeline",
    "core.content_cleaning":     "content-pipeline",
    "core.content_quality":      "content-pipeline",
    "core.elastic":              "content-pipeline",
    "core.content_recommender":  "content-pipeline",
    "core.youtube_api":          "content-pipeline",
    "core.audio_lessons":        "audio-lessons",
    "api.endpoints":             "api",
    "api.utils":                 "api",
    "api.app.py":                "api",
    "operations.crawler":          "operations",
    "operations.report_generator": "operations",
    "core.model":                "data-layer",
}

def node_group(name: str) -> str:
    return ARCHLENS_GROUPS.get(name, "other")

def node_layer(name: str) -> int:
    """Y-axis layer for D3 layout: 0 = top (HTTP/ops), 5 = bottom (data layer)."""
    if name.startswith("api.") or name.startswith("operations."):
        return 0
    if name == "core.model":
        return 5
    if name in ("core.util", "core.constants", "core.sql", "core.emailer",
                "core.events", "core.mwe", "core.badges", "core.leaderboards",
                "core.friends", "core.crowd_translations",
                "core.user_feature_toggles", "core.youtube_api"):
        return 4
    if name in ("core.language", "core.tokenization", "core.nlp_pipeline",
                "core.ml_models", "core.llm_services", "core.semantic_search",
                "core.semantic_vector_api"):
        return 3
    if name in ("core.feed_handler", "core.content_retriever",
                "core.content_cleaning", "core.content_quality",
                "core.content_recommender", "core.elastic",
                "core.reading_analysis"):
        return 2
    if name in ("core.bookmark_operations", "core.bookmark_quality",
                "core.exercises", "core.word_scheduling",
                "core.behavioral_modeling", "core.account_management",
                "core.user_statistics", "core.user_activity_hooks",
                "core.audio_lessons"):
        return 1
    return 2


def collect_py_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py")
            if not any(part in EXCLUDE_DIRS for part in p.relative_to(root).parts)]


def file_to_subpackage(filepath: Path) -> str:
    """Map a file path to its two-level package name (e.g. core/model/user.py -> core.model)."""
    parts = filepath.relative_to(SOURCE_ROOT).parts
    if len(parts) >= 2 and not parts[1].endswith(".py"):
        return f"{parts[0]}.{parts[1]}"
    return parts[0].replace(".py", "")


def import_to_subpackage(module_str: str) -> str | None:
    """Convert a dotted import string to a two-level package name, or None if external."""
    if not module_str or not module_str.startswith("zeeguu."):
        return None
    parts = module_str[len("zeeguu."):].split(".")
    return f"{parts[0]}.{parts[1]}" if len(parts) >= 2 else parts[0]


def resolve_relative(level: int, module: str | None, current_pkg: str) -> str | None:
    """Resolve a relative import to an absolute subpackage name."""
    pkg_parts = current_pkg.split(".")
    up = level - 1
    if up >= len(pkg_parts):
        return None
    base = ".".join(pkg_parts[:len(pkg_parts) - up])
    if module:
        return import_to_subpackage(f"zeeguu.{base}.{module}")
    return import_to_subpackage(f"zeeguu.{base}")


def extract_imports(filepath: Path, current_pkg: str) -> list[str]:
    """Parse one file and return internal subpackage names it imports from."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8", errors="ignore"),
                         filename=str(filepath))
    except SyntaxError:
        return []
    targets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            pkg = (resolve_relative(node.level, node.module, current_pkg)
                   if node.level else import_to_subpackage(node.module or ""))
            if pkg:
                targets.append(pkg)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                pkg = import_to_subpackage(alias.name)
                if pkg:
                    targets.append(pkg)
    return targets


def count_loc(filepath: Path) -> int:
    """Count non-blank, non-comment lines, excluding multi-line strings (docstrings)."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        multiline_str_lines: set[int] = set()
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                if tok.type == tokenize.STRING:
                    s, e = tok.start[0], tok.end[0]
                    if e > s:
                        multiline_str_lines.update(range(s, e + 1))
        except tokenize.TokenError:
            pass
        return sum(
            1 for i, line in enumerate(source.splitlines(), 1)
            if line.strip() and not line.strip().startswith("#")
            and i not in multiline_str_lines
        )
    except Exception:
        return 0


def main():
    print(f"Scanning {SOURCE_ROOT} ...")
    files = collect_py_files(SOURCE_ROOT)
    print(f"Found {len(files)} Python files")

    edge_weights: dict[str, dict[str, int]]        = defaultdict(lambda: defaultdict(int))
    edge_files:   dict[str, dict[str, list[str]]]  = defaultdict(lambda: defaultdict(list))
    loc_per_pkg:  dict[str, int]                   = defaultdict(int)

    for filepath in files:
        pkg = file_to_subpackage(filepath)
        loc_per_pkg[pkg] += count_loc(filepath)
        rel_path = str(filepath.relative_to(SOURCE_ROOT)).replace("\\", "/")
        seen = set()
        for target in extract_imports(filepath, pkg):
            if target != pkg and target not in seen:
                edge_weights[pkg][target] += 1
                edge_files[pkg][target].append(rel_path)
                seen.add(target)

    all_nodes = set(loc_per_pkg.keys())
    for src, targets in edge_weights.items():
        all_nodes.add(src)
        all_nodes.update(targets.keys())

    fan_out = {n: len(edge_weights.get(n, {})) for n in all_nodes}
    fan_in: dict[str, int] = defaultdict(int)
    for src, targets in edge_weights.items():
        for tgt in targets:
            fan_in[tgt] += 1

    # edges.csv
    with open(OUTPUT_DIR / "edges.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "target", "weight"])
        for src, targets in sorted(edge_weights.items()):
            for tgt, wt in sorted(targets.items()):
                w.writerow([src, tgt, wt])
    print(f"Wrote edges.csv")

    # metrics.csv
    with open(OUTPUT_DIR / "metrics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["package", "loc", "fan_in", "fan_out"])
        for node in sorted(all_nodes):
            w.writerow([node, loc_per_pkg.get(node, 0),
                        fan_in.get(node, 0), fan_out.get(node, 0)])
    print(f"Wrote metrics.csv")

    # module_view.dot (Graphviz — node width ~ fan-out, height ~ LOC)
    max_loc    = max((loc_per_pkg.get(n, 1) for n in all_nodes), default=1)
    max_fanout = max((fan_out.get(n, 1) for n in all_nodes), default=1)
    def nw(n): return round(0.8 + 3.0 * fan_out.get(n, 0) / max_fanout, 2)
    def nh(n): return round(0.4 + 1.6 * loc_per_pkg.get(n, 0) / max_loc, 2)
    def nc(n):
        if n.startswith("core."): return "#dce8f5"
        if n.startswith("api."):  return "#d5f0d5"
        return "#ffffff"

    with open(OUTPUT_DIR / "module_view.dot", "w", encoding="utf-8") as f:
        f.write('digraph zeeguu {\n  rankdir=TB;\n')
        f.write('  node [shape=box, style=filled, fontname="Helvetica", fontsize=10];\n\n')
        for prefix, cluster in [("api.", "api"), ("core.", "core")]:
            f.write(f'  subgraph cluster_{cluster} {{\n    label="{cluster}"; style=dashed;\n')
            for n in sorted(n for n in all_nodes if n.startswith(prefix)):
                f.write(f'    "{n}" [label="{n.split(".")[-1]}", width={nw(n)}, height={nh(n)}, fillcolor="{nc(n)}"];\n')
            f.write('  }\n')
        for n in sorted(n for n in all_nodes if not n.startswith(("api.", "core."))):
            f.write(f'  "{n}" [label="{n}", width={nw(n)}, height={nh(n)}, fillcolor="{nc(n)}"];\n')
        for src, targets in sorted(edge_weights.items()):
            for tgt, wt in sorted(targets.items()):
                pw = round(0.5 + 2.5 * wt / max(edge_weights[src].values()), 2)
                f.write(f'  "{src}" -> "{tgt}" [penwidth={pw}];\n')
        f.write('}\n')
    print(f"Wrote module_view.dot")

    # graph.json (for D3 visualisation)
    graph = {
        "nodes": [{"id": n, "label": n.split(".")[-1],
                   "loc": loc_per_pkg.get(n, 0), "fan_in": fan_in.get(n, 0),
                   "fan_out": fan_out.get(n, 0), "layer": node_layer(n),
                   "group": node_group(n)}
                  for n in sorted(all_nodes)],
        "links": [{"source": src, "target": tgt, "weight": wt,
                   "files": edge_files[src][tgt],
                   "violation": src == "core.model" and tgt.startswith("api.")}
                  for src, targets in sorted(edge_weights.items())
                  for tgt, wt in sorted(targets.items())],
    }
    with open(OUTPUT_DIR / "graph.json", "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    print(f"Wrote graph.json")

    total_edges = sum(len(t) for t in edge_weights.values())
    print(f"\nNodes: {len(all_nodes)}  |  Edges: {total_edges}")
    print("\nTop 10 by fan-in:")
    for n, fi in sorted(fan_in.items(), key=lambda x: -x[1])[:10]:
        print(f"  {n:40s}  fan-in={fi:3d}  fan-out={fan_out.get(n,0):3d}  loc={loc_per_pkg.get(n,0):5d}")
    print("\nTop 10 by fan-out:")
    for n, fo in sorted(fan_out.items(), key=lambda x: -x[1])[:10]:
        print(f"  {n:40s}  fan-out={fo:3d}  fan-in={fan_in.get(n,0):3d}  loc={loc_per_pkg.get(n,0):5d}")


if __name__ == "__main__":
    main()

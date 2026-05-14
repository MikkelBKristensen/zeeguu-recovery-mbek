# visualize.py — renders module view PNGs from edges.csv and metrics.csv

import csv
from pathlib import Path
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory

ANALYSIS_DIR = Path(__file__).parent


def load_graph() -> tuple[nx.DiGraph, dict]:
    G = nx.DiGraph()
    with open(ANALYSIS_DIR / "metrics.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            G.add_node(row["package"], loc=int(row["loc"]),
                       fan_in=int(row["fan_in"]), fan_out=int(row["fan_out"]))
    with open(ANALYSIS_DIR / "edges.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            G.add_edge(row["source"], row["target"], weight=int(row["weight"]))
    return G, {n: G.nodes[n] for n in G.nodes}


# Bare package roots and infrastructure nodes that are not architectural subsystems
NOISE_NODES = {
    "logging", "core", "api", "config", "core.constants", "core.sql",
    "api.app.py", "core.diagrams", "core.cl", "cl", "zeeguu",
}


def node_layer(name: str) -> int:
    """Y-axis layer: 0 = top (HTTP/ops), 5 = bottom (data layer)."""
    if name.startswith("api.") or name.startswith("operations."):
        return 0
    if name == "core.model":
        return 5
    if name in ("core.util", "core.constants", "core.sql", "core.emailer",
                "core.events", "core.mwe", "core.badges", "core.leaderboards",
                "core.friends"):
        return 4
    if name in ("core.language", "core.tokenization", "core.nlp_pipeline",
                "core.ml_models", "core.llm_services", "core.semantic_search",
                "core.semantic_vector_api", "core.youtube_api",
                "core.crowd_translations"):
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
                "core.user_feature_toggles", "core.audio_lessons"):
        return 1
    return 2


def node_color(name: str) -> str:
    if name.startswith("api."):        return "#7fbfff"
    if name.startswith("operations."): return "#ffb347"
    if name == "core.model":           return "#ff7f7f"
    if name.startswith("core."):       return "#90ee90"
    return "#dddddd"


def layered_layout(G: nx.DiGraph) -> dict:
    """Spread nodes evenly along x within each layer row."""
    layers: dict[int, list] = {}
    for node in G.nodes:
        layers.setdefault(node_layer(node), []).append(node)
    pos = {}
    for layer_num, nodes in layers.items():
        nodes_sorted = sorted(nodes)
        n = len(nodes_sorted)
        for i, node in enumerate(nodes_sorted):
            pos[node] = ((i - (n - 1) / 2) * 2.2, -layer_num * 3.0)
    return pos


def draw(G: nx.DiGraph, metrics: dict, title: str, output_path: Path,
         figsize=(24, 16), font_size=8, node_size_multiplier=1.0):

    pos = layered_layout(G)
    max_loc = max((metrics.get(n, {}).get("loc", 1) for n in G.nodes), default=1)
    node_sizes = [
        max(2340, 10000 * metrics.get(n, {}).get("loc", 0) / max_loc) * node_size_multiplier
        for n in G.nodes
    ]
    colors = [node_color(n) for n in G.nodes]

    weights = [G[u][v].get("weight", 1) for u, v in G.edges]
    max_w = max(weights) if weights else 1
    edge_widths = [0.5 + 2.5 * w / max_w for w in weights]

    # Draw the layer violation edge separately in red
    edges_list = list(G.edges)
    violation_set = {(u, v) for u, v in edges_list
                     if u == "core.model" and v.startswith("api.")}
    regular_edges  = [e for e in edges_list if e not in violation_set]
    violation_edges = [e for e in edges_list if e in violation_set]
    regular_widths = [edge_widths[i] for i, e in enumerate(edges_list)
                      if e not in violation_set]

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor("#fafafa")
    fig.patch.set_facecolor("#fafafa")

    ROW_GAP = 3.0
    HALF = ROW_GAP / 2.0
    BAND_FILL = {0: "#edf4ff", 1: "#f5f5f5", 2: "#f0f0f0",
                 3: "#f5f5f5", 4: "#f0f0f0", 5: "#fff0f0"}
    for l in range(6):
        ax.axhspan(-l * ROW_GAP - HALF, -l * ROW_GAP + HALF,
                   color=BAND_FILL[l], alpha=0.6, zorder=0)
    for l in range(1, 6):
        ax.axhline(-l * ROW_GAP + HALF, color="#cccccc",
                   linewidth=0.6, linestyle="--", zorder=1)

    nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                           node_color=colors, ax=ax, alpha=0.9)
    if regular_edges:
        nx.draw_networkx_edges(G, pos, edgelist=regular_edges,
                               width=regular_widths, edge_color="#555555",
                               arrows=True, arrowsize=14, node_size=node_sizes,
                               connectionstyle="arc3,rad=0.08", ax=ax, alpha=0.7)
    if violation_edges:
        nx.draw_networkx_edges(G, pos, edgelist=violation_edges,
                               width=3.5, edge_color="#cc0000",
                               arrows=True, arrowsize=22, node_size=node_sizes,
                               style="dashed", connectionstyle="arc3,rad=0.2",
                               ax=ax, alpha=1.0)

    # Strip package prefix from labels — colour already encodes the layer
    short_labels = {}
    for n in G.nodes:
        label = n
        for prefix in ("core.", "api.", "operations."):
            if n.startswith(prefix):
                label = n[len(prefix):]
                break
        short_labels[n] = label
    nx.draw_networkx_labels(G, pos, labels=short_labels,
                            font_size=font_size, font_family="monospace", ax=ax)

    layer_labels = {0: "HTTP / operations", 1: "Learning & users",
                    2: "Content pipeline",  3: "NLP & language",
                    4: "Utilities",         5: "Data layer (ORM)"}
    blend = blended_transform_factory(ax.transAxes, ax.transData)
    for layer_num, label in layer_labels.items():
        ax.text(-0.03, -layer_num * ROW_GAP, label, transform=blend,
                ha="right", va="center", fontsize=12, color="#777777",
                style="italic")

    # Left-margin bars marking the two architectural layers
    brkt_x, brkt_w = -0.115, 0.018
    brkt_cx = brkt_x + brkt_w / 2
    for color, y_top_l, y_bot_l, label, text_color in [
        ("#7fbfff", 0 * ROW_GAP + HALF, 0 * ROW_GAP - HALF, "API",  "#1a5fa8"),
        ("#90ee90", -1 * ROW_GAP + HALF, -5 * ROW_GAP - HALF, "CORE", "#1a6b1a"),
    ]:
        ax.add_patch(Rectangle((brkt_x, y_bot_l), brkt_w, y_top_l - y_bot_l,
                                transform=blend, color=color, alpha=0.5,
                                clip_on=False, zorder=5))
        ax.text(brkt_cx, (y_top_l + y_bot_l) / 2, label, transform=blend,
                ha="center", va="center", fontsize=11, color=text_color,
                fontweight="bold", rotation=90, clip_on=False)

    legend_items = [
        mpatches.Patch(color="#7fbfff", label="api: HTTP adapter layer"),
        mpatches.Patch(color="#90ee90", label="core: domain logic"),
        mpatches.Patch(color="#ff7f7f", label="core.model: data layer (ORM)"),
        mpatches.Patch(color="#ffb347", label="operations: background processes"),
        mpatches.Patch(color="#cc0000", label="layer violation (core.model to api.*)"),
    ]
    ax.legend(handles=legend_items, loc="lower right", fontsize=19, framealpha=0.9)
    ax.text(0.01, 0.01, "Node size proportional to lines of code",
            transform=ax.transAxes, fontsize=8, color="#888888")

    ax.axis("off")
    # Clamp y-axis to band extents to avoid empty whitespace above/below
    y_top = HALF + 0.3
    y_bot = -5 * ROW_GAP - HALF - 0.3
    ax.set_ylim(y_bot, y_top)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def main():
    G_full, metrics = load_graph()

    draw(G_full, metrics, title="",
         output_path=ANALYSIS_DIR / "module_view_full.png",
         figsize=(30, 20), font_size=7)

    # Report view: keep only structurally significant nodes (high fan-in/out)
    ANCHORS = {"api.endpoints", "operations.crawler", "core.model"}
    def is_significant(n):
        m = metrics.get(n, {})
        return m.get("fan_in", 0) >= 3 or m.get("fan_out", 0) >= 4 or n in ANCHORS

    report_nodes = [n for n in G_full.nodes
                    if n not in NOISE_NODES and is_significant(n)]
    G_report = G_full.subgraph(report_nodes).copy()
    print(f"Report view: {G_report.number_of_nodes()} nodes, "
          f"{G_report.number_of_edges()} edges")
    draw(G_report, metrics, title="",
         output_path=ANALYSIS_DIR / "module_view_report.png",
         figsize=(28, 18), font_size=13, node_size_multiplier=1.8)

    # Detailed view: all non-noise nodes with at least one edge
    clean_nodes = [n for n in G_full.nodes if n not in NOISE_NODES]
    G_clean = G_full.subgraph(clean_nodes).copy()
    isolated = [n for n in G_clean.nodes
                if G_clean.in_degree(n) == 0 and G_clean.out_degree(n) == 0]
    G_clean.remove_nodes_from(isolated)
    print(f"Detailed view: {G_clean.number_of_nodes()} nodes, "
          f"{G_clean.number_of_edges()} edges")
    draw(G_clean, metrics, title="",
         output_path=ANALYSIS_DIR / "module_view_detailed.png",
         figsize=(36, 22), font_size=13, node_size_multiplier=1.8)


if __name__ == "__main__":
    main()

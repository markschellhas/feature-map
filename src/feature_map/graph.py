import re
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

from feature_map.loader import extract_related_slug, list_map_files
from feature_map.yamlutil import read_yaml_file


def build_graph(features_dir: Path) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
    for path in list_map_files(features_dir):
        slug = path.stem
        graph.setdefault(slug, [])
        try:
            data = read_yaml_file(path) or {}
        except (yaml.YAMLError, OSError, UnicodeDecodeError):
            continue
        related = data.get("related_features") or []
        if not isinstance(related, list):
            continue
        for entry in related:
            target = extract_related_slug(entry)
            if target:
                graph[slug].append(target)
    return graph


def graph_data(
    features_dir: Path,
    root: Optional[str] = None,
) -> dict:
    full_graph = build_graph(features_dir)
    nodes: Set[str] = set()
    edges = []

    if root:
        root = root.replace(".yaml", "")
        visited = set()
        stack = [root]

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            nodes.add(node)
            for target in full_graph.get(node, []):
                edges.append({"from": node, "to": target})
                visit(target)

        visit(root)
        for edge in edges:
            nodes.add(edge["to"])
    else:
        nodes = set(full_graph.keys())
        for source, targets in full_graph.items():
            nodes.add(source)
            for target in targets:
                nodes.add(target)
                edges.append({"from": source, "to": target})

    return {
        "nodes": sorted(nodes),
        "edges": edges,
    }


def _graph_id(name: str) -> str:
    """Keep mermaid/dot node ids from becoming extra graph syntax."""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
    if not cleaned:
        cleaned = "node"
    if cleaned[0].isdigit():
        cleaned = "n_" + cleaned
    return cleaned


def format_mermaid(data: dict) -> str:
    lines = ["graph LR"]
    for edge in data.get("edges", []):
        lines.append(f"  {_graph_id(edge['from'])} --> {_graph_id(edge['to'])}")
    return "\n".join(lines) + "\n"


def format_dot(data: dict) -> str:
    lines = ["digraph feature_map {"]
    for edge in data.get("edges", []):
        src = str(edge["from"]).replace("\\", "\\\\").replace('"', '\\"')
        dst = str(edge["to"]).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  "{src}" -> "{dst}";')
    lines.append("}")
    return "\n".join(lines) + "\n"

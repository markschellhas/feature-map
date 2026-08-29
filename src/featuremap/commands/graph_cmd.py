from featuremap.graph import format_dot, format_mermaid, graph_data


def run_graph(features_dir, name=None, fmt="mermaid", as_json=False):
    data = graph_data(features_dir, root=name)

    if fmt == "json" or as_json:
        return {"ok": True, **data}

    if fmt == "dot":
        return format_dot(data)

    if fmt == "mermaid":
        return format_mermaid(data)

    from featuremap.errors import CliError

    raise CliError(f'Unknown graph format "{fmt}".', suggestion="Use mermaid, json, or dot.")
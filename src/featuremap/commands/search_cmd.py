from pathlib import Path

from featuremap.text_index import search_maps


def run_search(features_dir: Path, query: str, as_json: bool = False):
    results = search_maps(features_dir, query)
    payload = {"ok": True, "query": query, "count": len(results), "results": results}

    if as_json:
        return payload

    if not results:
        print(f"No features matched '{query}'.")
        return payload

    for item in results:
        print(item["feature"])
        for snippet in item.get("snippets", []):
            print(f"  {snippet}")
    return payload
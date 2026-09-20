from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, List, Optional

from feature_map.output import emit
from feature_map.view_model import build_view_snapshot
from feature_map.view_render import render_view_html
from feature_map.view_server import make_server, serve_until, server_url


class ViewerSession:
    def __init__(self, url: str, server, html: str, snapshot: dict):
        self.url = url
        self.server = server
        self.html = html
        self.snapshot = snapshot


def start_viewer(
    features_dir: Path,
    repo_root: Path,
    apps: Optional[List[str]] = None,
) -> ViewerSession:
    snapshot = build_view_snapshot(features_dir, repo_root, apps)
    html = render_view_html(snapshot)
    server = make_server(html)
    return ViewerSession(server_url(server), server, html, snapshot)


def run_viewer(
    features_dir: Path,
    repo_root: Path,
    apps: Optional[List[str]] = None,
    *,
    as_json: bool = False,
    no_open: bool = False,
    timeout: Optional[float] = None,
    open_browser: Optional[Callable[[str], object]] = None,
):
    session = start_viewer(features_dir, repo_root, apps)
    payload = {"ok": True, "url": session.url}
    if as_json:
        emit(payload, as_json=True)
    else:
        sys.stdout.write(session.url + "\n")
        sys.stdout.flush()
    if not no_open:
        opener = open_browser
        if opener is None:
            import webbrowser

            opener = webbrowser.open
        opener(session.url)
    serve_until(session.server, timeout=timeout)
    return None

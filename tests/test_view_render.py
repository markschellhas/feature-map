import json
import shutil
import subprocess
import unittest

from helpers import FeaturemapTestCase


class ViewRenderTests(FeaturemapTestCase):
    def _html(self, extra_map_fields=None):
        from feature_map.view_model import build_view_snapshot
        from feature_map.view_render import render_view_html

        repo = self.copy_repo()
        if extra_map_fields:
            path = repo / ".features" / "auth.yaml"
            path.write_text(path.read_text(encoding="utf-8") + extra_map_fields, encoding="utf-8")
        snapshot = build_view_snapshot(repo / ".features", repo, ["api", "web"])
        html = render_view_html(snapshot)
        return html, snapshot, repo

    def test_html_embeds_snapshot_and_sidebar_slugs(self):
        html, snapshot, _repo = self._html()
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("auth", html)
        self.assertIn("billing", html)
        self.assertIn("notifications", html)
        self.assertNotIn("__VIEW_SNAPSHOT_JSON__", html)
        self.assertIn(snapshot["maps"]["auth"]["purpose"], html)

    def test_sidebar_renders_titles_without_purpose_description(self):
        html, snapshot, _repo = self._html()
        self.assertIn("featureTitle(map.feature_name || slug)", html)
        self.assertNotIn('purpose.className = "purpose"', html)
        self.assertNotIn("btn.appendChild(purpose)", html)
        self.assertIn(snapshot["maps"]["auth"]["feature_name"], html)

    def test_feature_header_and_sidebar_use_human_friendly_titles(self):
        html, _snapshot, _repo = self._html()
        self.assertIn("function featureTitle(name)", html)
        self.assertIn('.replace(/_+/g, " ")', html)
        self.assertIn("ch.toUpperCase()", html)
        self.assertIn("featureTitle(map.feature_name || slug)", html)
        self.assertIn('heading.textContent = featureTitle(map.feature_name || map.slug || "")', html)

    @unittest.skipUnless(shutil.which("node"), "node not on PATH")
    def test_feature_title_formats_user_signup(self):
        html, _snapshot, _repo = self._html()
        start = html.index("function featureTitle(name) {")
        depth = 0
        end = None
        for index, char in enumerate(html[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        self.assertIsNotNone(end)
        script = (
            html[start:end]
            + "\n"
            + "const assert = require('assert');\n"
            + "assert.strictEqual(featureTitle('user_signup'), 'User Signup');\n"
            + "assert.strictEqual(featureTitle('auth'), 'Auth');\n"
            + "assert.strictEqual(featureTitle('USER_SIGNUP'), 'User Signup');\n"
            + "assert.strictEqual(featureTitle('already friendly'), 'Already Friendly');\n"
        )
        result = subprocess.run(
            ["node", "--input-type=commonjs", "-e", script],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sidebar_includes_search_filter(self):
        html, _snapshot, _repo = self._html()
        self.assertIn('id="sidebar-search"', html)
        self.assertIn('type="search"', html)
        self.assertIn("matchesSearch", html)
        self.assertIn("No matching maps.", html)

    def test_graph_and_mermaid_use_diagram_canvas_not_source(self):
        html, snapshot, _repo = self._html(
            "\nflow:\n  |\n    graph LR\n      start --> done\n"
        )
        self.assertIn('id="graph-canvas"', html)
        self.assertIn("diagram-canvas", html)
        self.assertIn("parseMermaid", html)
        self.assertNotIn("Mermaid source", html)
        self.assertNotIn("mermaid-source", html)
        self.assertNotIn('id="graph-nodes"', html)
        self.assertNotIn('id="graph-edges"', html)
        self.assertIn("graph LR", html)
        self.assertIn("start --> done", snapshot["maps"]["auth"]["fields"][-1]["value"])

    def test_html_escapes_script_breakout_in_json(self):
        repo = self.copy_repo()
        path = repo / ".features" / "auth.yaml"
        original = path.read_text(encoding="utf-8")
        path.write_text(
            original.replace(
                "Fixture map for the standalone featuremap test suite.",
                "</script><script>alert(1)</script>",
            ),
            encoding="utf-8",
        )
        from feature_map.view_model import build_view_snapshot
        from feature_map.view_render import render_view_html

        snapshot = build_view_snapshot(repo / ".features", repo, ["api", "web"])
        html = render_view_html(snapshot)
        self.assertNotIn("</script><script>alert(1)</script>", html)
        start = html.index("window.FEATURE_MAP = ") + len("window.FEATURE_MAP = ")
        end = html.index(";</script>", start)
        payload = json.loads(html[start:end])
        self.assertIn("</script>", payload["maps"]["auth"]["notes"])

    def test_stale_path_string_is_present_unrewritten(self):
        html, snapshot, _repo = self._html()
        self.assertIn("src/missing_file.py", html)
        self.assertEqual(
            snapshot["maps"]["billing"]["entry_points"][1],
            "src/missing_file.py",
        )

    def test_empty_maps_render_no_maps_copy(self):
        from feature_map.view_render import render_view_html

        html = render_view_html(
            {
                "slugs": [],
                "selected": None,
                "maps": {},
                "graph": {"nodes": [], "edges": [], "mermaid": "graph LR\n"},
            }
        )
        self.assertIn("No feature maps", html)

    def test_section_headers_are_capitalized_spaced_and_indented(self):
        html, _snapshot, _repo = self._html()
        self.assertIn("function labelFor(key)", html)
        self.assertIn("ch.toUpperCase()", html)
        self.assertIn("text-transform: uppercase", html)
        self.assertIn("--section-gap", html)
        self.assertIn("var(--indent)", html)
        self.assertIn("nested-fields", html)
        self.assertIn('wrap.className = "field field-"', html)

    def test_does_not_write_the_consumer_repo(self):
        html, _snapshot, repo = self._html()
        self.assertTrue(html)
        written = list(repo.rglob("*.html"))
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()

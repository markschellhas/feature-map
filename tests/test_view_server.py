import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen

from helpers import FeaturemapTestCase


class ViewServerTests(FeaturemapTestCase):
    def _serve(self, html="<html>ok</html>"):
        from feature_map.view_server import make_server, server_url

        server = make_server(html)
        url = server_url(server)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        return url, server

    def test_binds_loopback_and_serves_html_from_memory(self):
        url, server = self._serve("<html>viewer-body</html>")
        host, port = server.server_address
        self.assertEqual(host, "127.0.0.1")
        self.assertGreater(port, 0)
        self.assertTrue(url.startswith("http://127.0.0.1:"))
        with urlopen(url, timeout=2) as resp:
            body = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
        self.assertEqual(body, "<html>viewer-body</html>")
        with urlopen(url + "index.html", timeout=2) as resp:
            self.assertEqual(resp.read().decode("utf-8"), "<html>viewer-body</html>")

    def test_unknown_paths_are_404_and_do_not_read_repo_files(self):
        repo = self.copy_repo()
        secret = repo / "src" / "auth" / "session.py"
        self.assertTrue(secret.is_file())
        url, _server = self._serve("<html>viewer-only</html>")
        with self.assertRaises(HTTPError) as raised:
            urlopen(url + "src/auth/session.py", timeout=2)
        self.assertEqual(raised.exception.code, 404)
        with self.assertRaises(HTTPError):
            urlopen(url + secret.name, timeout=2)
        with urlopen(url, timeout=2) as resp:
            self.assertNotIn("Sign-in", resp.read().decode("utf-8"))

    def test_timeout_stops_the_server(self):
        from feature_map.view_server import make_server, serve_until, server_url

        server = make_server("<html>t</html>")
        url = server_url(server)
        serve_until(server, timeout=0.3)
        with self.assertRaises(Exception):
            urlopen(url, timeout=1)


if __name__ == "__main__":
    unittest.main()

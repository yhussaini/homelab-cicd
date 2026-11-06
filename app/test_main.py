import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer

import main


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), main.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as r:
            return r.status, r.read().decode()

    def test_home_page(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn("Hello from the homelab", body)

    def test_healthz(self):
        self.assertEqual(self.get("/healthz"), (200, "ok"))

    def test_version(self):
        status, body = self.get("/version")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["version"], main.VERSION)

    def test_unknown_path_is_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/nope")
        self.assertEqual(ctx.exception.code, 404)

    def test_render_page_uses_values(self):
        html = main.render_page("v9", "pod-x", "#ff0000")
        for s in ("v9", "pod-x", "#ff0000"):
            self.assertIn(s, html)


if __name__ == "__main__":
    unittest.main()

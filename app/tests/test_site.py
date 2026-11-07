"""Checks that run in CI before the image is built (Python standard library only)."""
import os
import re
import unittest
from html.parser import HTMLParser

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(APP, "site")
INDEX = os.path.join(SITE, "index.html")

# Domains allowed to appear in the published site. Anything else could be a real internal name.
ALLOWED_DOMAINS = ("example.com", "example.org", "example.net")
# ".ca" needs two dots (host.company.ca) so JavaScript like `c.ca` (a property) is not flagged.
DOMAIN_RE = re.compile(
    r"\b(?:(?:[a-z0-9-]+\.)+(?:com|net|org|local|corp|lan|internal)|(?:[a-z0-9-]+\.){2,}ca)\b", re.I)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


class SiteTest(unittest.TestCase):
    def test_index_exists(self):
        self.assertTrue(os.path.isfile(INDEX), "app/site/index.html is missing")

    def test_index_has_title_and_body(self):
        html = read(INDEX)
        p = TitleParser()
        p.feed(html)
        self.assertTrue(p.title.strip(), "page has no <title>")
        self.assertIn("</body>", html, "Dockerfile needs </body> to add the version footer")

    def test_only_example_domains(self):
        """Fail the pipeline if a real-looking domain name ends up in the public site."""
        bad = set()
        for root, _, files in os.walk(SITE):
            for name in files:
                if not name.endswith((".html", ".js", ".css", ".json", ".txt")):
                    continue
                for m in DOMAIN_RE.finditer(read(os.path.join(root, name))):
                    d = m.group(0).lower()
                    if not d.endswith(ALLOWED_DOMAINS):
                        bad.add(d)
        self.assertFalse(bad, "non-example domains found: %s" % sorted(bad))

    def test_nginx_config_has_health_endpoint(self):
        conf = read(os.path.join(APP, "nginx.conf"))
        self.assertIn("listen 8080", conf)
        self.assertIn("location = /healthz", conf)


if __name__ == "__main__":
    unittest.main()

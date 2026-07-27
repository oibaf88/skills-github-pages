from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".jekyll-cache", "node_modules", "vendor"}


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()

    def handle_starttag(self, _tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append(values[attribute])


def public_html_files():
    return sorted(
        path
        for path in ROOT.rglob("*.html")
        if not set(path.relative_to(ROOT).parts) & IGNORED_PARTS
    )


def public_route(path):
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative.removesuffix("index.html")
    return "/" + relative


def route_file(path_value):
    relative = unquote(path_value).lstrip("/")
    candidate = ROOT / relative

    if not relative:
        return ROOT / "index.html"
    if candidate.is_file():
        return candidate
    if (candidate / "index.html").is_file():
        return candidate / "index.html"
    if not candidate.suffix and candidate.with_suffix(".html").is_file():
        return candidate.with_suffix(".html")
    return candidate


def parsed_document(path, cache):
    if path not in cache:
        parser = DocumentParser()
        parser.feed(path.read_text(encoding="utf-8"))
        cache[path] = parser
    return cache[path]


def test_internal_links_and_fragments_resolve():
    cache = {}
    failures = []

    for html_path in public_html_files():
        document = parsed_document(html_path, cache)
        base_url = "https://bfab.io" + public_route(html_path)

        for reference in document.references:
            if "{{" in reference or reference.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue

            parsed = urlparse(urljoin(base_url, reference))
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc not in {"bfab.io", "www.bfab.io"}:
                continue

            target = route_file(parsed.path)
            if not target.is_file():
                failures.append(f"{html_path.relative_to(ROOT)} -> {reference} (missing file)")
                continue

            if parsed.fragment and target.suffix == ".html":
                target_ids = parsed_document(target, cache).ids
                if parsed.fragment not in target_ids:
                    failures.append(
                        f"{html_path.relative_to(ROOT)} -> {reference} (missing fragment)"
                    )

    assert failures == []


def test_no_legacy_jekyll_posts_remain():
    posts = ROOT / "_posts"
    assert not posts.exists() or not any(posts.iterdir())

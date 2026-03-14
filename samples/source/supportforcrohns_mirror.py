from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import hashlib
import os
import re
from urllib.parse import urljoin, urlparse

import requests

BASE_URL = "https://supportforcrohns.org/"
OUTPUT_DIR = Path(r"C:\Users\ManishKL\Documents\Playground\supportforcrohns")
PAGES = [
    "/",
    "/about-me/",
    "/podcast-page/",
    "/what-we-do/",
    "/books/",
    "/contact/",
]


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        for key in ("href", "src", "data-src"):
            value = attrs_dict.get(key)
            if value:
                self.urls.add(value)
        srcset = attrs_dict.get("srcset")
        if srcset:
            for item in srcset.split(","):
                url = item.strip().split(" ")[0]
                if url:
                    self.urls.add(url)


def normalize_url(raw: str) -> str:
    if raw.startswith("//"):
        return "https:" + raw
    return urljoin(BASE_URL, raw)


def should_download(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc in {"", "supportforcrohns.org", "www.supportforcrohns.org"}:
        return True
    if parsed.netloc in {"fonts.googleapis.com", "fonts.gstatic.com"} and parsed.path not in {"", "/"}:
        return True
    return False


def local_path_for(url: str) -> Path:
    parsed = urlparse(url)
    host = parsed.netloc or "supportforcrohns.org"
    path = (parsed.path or '/').lstrip('/') or 'index.html'
    if path.endswith('/'):
        path = path + "index.html"
    if not Path(path).suffix:
        path = path + ".html"
    if parsed.query:
        digest = hashlib.md5(parsed.query.encode("utf-8")).hexdigest()[:12]
        suffix = Path(path).suffix or ".html"
        stem = Path(path).stem
        folder = Path(path).parent
        path = str(folder / f"{stem}__{digest}{suffix}")
    return OUTPUT_DIR / host / path


def collect_asset_urls(html: str) -> set[str]:
    parser = AssetParser()
    parser.feed(html)
    urls: set[str] = set()
    for raw in parser.urls:
        url = normalize_url(raw)
        if url.startswith(("mailto:", "tel:", "javascript:")):
            continue
        if should_download(url):
            urls.add(url)
    return urls


def rewrite_urls(html: str, current_file: Path, mapping: dict[str, Path]) -> str:
    replacements: list[tuple[str, str]] = []
    current_dir = current_file.parent
    for url, local_path in mapping.items():
        rel = os.path.relpath(local_path, current_dir).replace("\\", "/")
        replacements.append((url, rel))
        if url.startswith("https://"):
            replacements.append((url.replace("https://", "//"), rel))
    for src, dst in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        html = html.replace(src, dst)
    return html


def fetch(session: requests.Session, url: str, timeout: int = 60) -> requests.Response:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; SupportForCrohnsMirror/1.0)"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    page_html: dict[str, str] = {}
    page_paths: dict[str, Path] = {}
    asset_paths: dict[str, Path] = {}

    for page in PAGES:
        url = urljoin(BASE_URL, page)
        page_html[url] = fetch(session, url).text
        page_paths[url] = local_path_for(url)

    asset_urls: set[str] = set()
    for html in page_html.values():
        asset_urls.update(collect_asset_urls(html))

    for url in sorted(asset_urls):
        asset_paths[url] = local_path_for(url)

    for url, path in asset_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        response = session.get(url, timeout=120)
        if not response.ok:
            continue
        path.write_bytes(response.content)

    mapping = {}
    mapping.update(page_paths)
    mapping.update(asset_paths)

    for url, html in page_html.items():
        path = page_paths[url]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rewrite_urls(html, path, mapping), encoding="utf-8")


if __name__ == "__main__":
    main()



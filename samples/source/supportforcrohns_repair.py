from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

ROOT = Path(r"C:\Users\ManishKL\Documents\Playground\supportforcrohns-repo")
SITE = "https://supportforcrohns.org"
ALLOWED = {"supportforcrohns.org", "www.supportforcrohns.org", "fonts.googleapis.com", "fonts.gstatic.com"}
TEXT_EXTS = {".html", ".css", ".js", ".php"}
URL_RE = re.compile(r"https?://[^\s\"'<>)+]+|//[^\s\"'<>)+]+")
BROKEN_PREFIXES = [
    ("../index.htmlwp-content/", "../wp-content/"),
    ("../index.htmlwp-admin/", "../wp-admin/"),
    ("../index.html?action=", "../index.html?action="),
    ("index.htmlwp-content/", "wp-content/"),
    ("index.htmlwp-admin/", "wp-admin/"),
]

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (compatible; SupportForCrohnsRepair/1.0)"


def local_path_for(url: str) -> Path:
    parsed = urlparse(url if not url.startswith('//') else 'https:' + url)
    host = parsed.netloc or "supportforcrohns.org"
    path = (parsed.path or '/').lstrip('/') or 'index.html'
    if path.endswith('/'):
        path += 'index.html'
    if not Path(path).suffix:
        path += '.html'
    if parsed.query:
        digest = hashlib.md5(parsed.query.encode('utf-8')).hexdigest()[:12]
        suffix = Path(path).suffix or '.html'
        stem = Path(path).stem
        folder = Path(path).parent
        path = str(folder / f"{stem}__{digest}{suffix}")
    return ROOT / host / path


def relative_ref(current_file: Path, target: Path) -> str:
    return os.path.relpath(target, current_file.parent).replace('\\', '/')


def fetch_if_missing(url: str) -> Path | None:
    parsed = urlparse(url if not url.startswith('//') else 'https:' + url)
    if parsed.netloc not in ALLOWED:
        return None
    target = local_path_for(url)
    if target.exists():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = session.get(url if not url.startswith('//') else 'https:' + url, timeout=120)
        if not response.ok:
            return None
        target.write_bytes(response.content)
        return target
    except Exception:
        return None


def repair_text(path: Path, text: str) -> str:
    for src, dst in BROKEN_PREFIXES:
        text = text.replace(src, dst)

    replacements: dict[str, str] = {}
    for raw in set(URL_RE.findall(text)):
        parsed = urlparse(raw if not raw.startswith('//') else 'https:' + raw)
        if parsed.netloc not in ALLOWED:
            continue
        target = fetch_if_missing(raw)
        if target is None:
            continue
        replacements[raw] = relative_ref(path, target)

    for src, dst in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(src, dst)

    text = text.replace("href='//fonts.googleapis.com'", "href='fonts.googleapis.com/css__3019c91a9343.html'")
    text = text.replace('href="//fonts.googleapis.com"', 'href="fonts.googleapis.com/css__3019c91a9343.html"')
    text = re.sub(r'(src|href)="([^"]+?)&amp;format=xml"', r'\1="\2__xml_fix"', text)
    text = text.replace('__xml_fix', '&amp;format=xml')

    if path.name == 'index.html' and path.parent.name == 'contact':
        text = re.sub(r'<form action="[^"]*" method="post" class="wpcf7-form init"', '<form id="static-contact-form" action="#" method="post" class="wpcf7-form init"', text)
        text = text.replace('<input class="wpcf7-form-control wpcf7-submit has-spinner" type="submit" value="Submit" /><div class="wpcf7-response-output" aria-hidden="true"></div>', '<input class="wpcf7-form-control wpcf7-submit has-spinner" type="submit" value="Send Email" /><div class="wpcf7-response-output" aria-hidden="true"></div><p id="static-contact-note" style="margin-top:12px;font-size:14px;color:#144047;">This form opens your email app and drafts the message to info@supportforcrohns.org.</p>')
        script = """
<script>
(function () {
  var form = document.getElementById('static-contact-form');
  if (!form) return;
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var name = form.querySelector('[name="your-name"]').value.trim();
    var email = form.querySelector('[name="your-email"]').value.trim();
    var subject = form.querySelector('[name="your-subject"]').value.trim();
    var message = form.querySelector('[name="your-message"]').value.trim();
    var body = [
      'Name: ' + name,
      'Email: ' + email,
      '',
      message
    ].join('\n');
    window.location.href = 'mailto:info@supportforcrohns.org?subject=' + encodeURIComponent(subject || 'Support For Crohns Contact') + '&body=' + encodeURIComponent(body);
  });
}());
</script>
"""
        text = text.replace('</body>', script + '\n</body>')

    return text


changed = 0
for path in ROOT.rglob('*'):
    if path.suffix.lower() not in TEXT_EXTS:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    new_text = repair_text(path, text)
    if new_text != text:
        path.write_text(new_text, encoding='utf-8')
        changed += 1

# Explicitly fetch a few known missing media referenced by the public pages.
for url in [
    'https://supportforcrohns.org/wp-content/uploads/2024/08/create-a-banner-for-a-podcast-episode-titled-podca-e-5f7G2NRmSBu4wHYmDyWA-4KVwXH88S9aTYSqhFXzBww-1024x576.jpeg',
    'https://supportforcrohns.org/wp-content/uploads/2020/03/Blog-Banner-580x435.jpg',
    'https://supportforcrohns.org/wp-content/uploads/2020/03/Blog-Banner-175x175.jpg',
    'https://supportforcrohns.org/wp-content/uploads/2020/03/Blog-Banner-300x300.jpg',
    'https://supportforcrohns.org/wp-content/uploads/2020/03/Blog-Banner-180x180.jpg',
]:
    fetch_if_missing(url)

print(f'CHANGED={changed}')

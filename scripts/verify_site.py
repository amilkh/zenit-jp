#!/usr/bin/python3
"""Verify local links, images, and rendered pages before publishing."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        for name in ('href', 'src'):
            if attributes.get(name):
                self.values.append(attributes[name] or '')


def check_files() -> None:
    missing: list[str] = []
    for source in ROOT.rglob('*.html'):
        parser = References()
        parser.feed(source.read_text(encoding='utf-8'))
        for value in parser.values:
            if value.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            relative = value.split('#', 1)[0]
            target = (source.parent / relative).resolve()
            if relative and not target.exists():
                missing.append(f'{source.relative_to(ROOT)} -> {value}')
    if missing:
        raise SystemExit('Missing local references:\n' + '\n'.join(missing))


def check_browser() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.goto('http://127.0.0.1:8765/', wait_until='networkidle')
        page.evaluate("Array.from(document.images).forEach(img => { img.loading = 'eager'; img.src = img.src; })")
        page.wait_for_load_state('networkidle')
        height = page.evaluate('document.documentElement.scrollHeight')
        for y in range(0, height, 700):
            page.evaluate('(value) => window.scrollTo(0, value)', y)
            page.wait_for_timeout(80)
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(250)
        broken = page.evaluate("Array.from(document.images).filter(img => !img.complete || !img.naturalWidth).map(img => img.src)")
        if broken:
            raise SystemExit('Broken rendered images:\n' + '\n'.join(broken))
        page.screenshot(path='/tmp/zenit-static-verified.png', full_page=True)
        browser.close()


def main() -> None:
    check_files()
    check_browser()
    print('Verified local references and rendered images.')


if __name__ == '__main__':
    main()

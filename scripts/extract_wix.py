#!/usr/bin/python3
"""Capture the public ZenIT Wix site for a one-time static migration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright


BASE = "https://amilkh5.wixsite.com/my-site"
OUT = Path(__file__).resolve().parents[1] / "archive" / "source.json"


def sitemap_urls(name: str) -> list[str]:
    with urlopen(f"{BASE}/{name}", timeout=30) as response:
        root = ElementTree.fromstring(response.read())
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [node.text for node in root.findall("s:url/s:loc", namespace) if node.text]


def main() -> None:
    page_urls = sitemap_urls("pages-sitemap.xml")
    post_urls = sitemap_urls("blog-posts-sitemap.xml")
    urls = list(dict.fromkeys(page_urls + post_urls))
    records: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        for index, url in enumerate(urls, start=1):
            print(f"[{index}/{len(urls)}] {url}", flush=True)
            page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(3500)
            record = page.evaluate(
                """
                () => {
                  const visible = (el) => {
                    const style = getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
                  };
                  const content = document.querySelector('main') || document.querySelector('#SITE_PAGES') || document.body;
                  return {
                    url: location.href,
                    title: document.title,
                    text: content.innerText.trim(),
                    images: Array.from(content.querySelectorAll('img')).filter(visible).map((img) => ({
                      src: img.currentSrc || img.src,
                      alt: img.alt || '',
                      width: img.naturalWidth,
                      height: img.naturalHeight,
                      boxWidth: Math.round(img.getBoundingClientRect().width),
                      boxHeight: Math.round(img.getBoundingClientRect().height)
                    })),
                    links: Array.from(content.querySelectorAll('a[href]')).filter(visible).map((a) => ({
                      text: a.innerText.trim(),
                      href: a.href
                    })).filter((item) => item.text || item.href),
                    frames: Array.from(content.querySelectorAll('iframe')).filter(visible).map((frame) => frame.src)
                  };
                }
                """
            )
            records.append(record)
            time.sleep(0.2)
        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

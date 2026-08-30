#!/usr/bin/python3
"""Build the static ZenIT archive from the captured Wix content."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "archive" / "source.json"
ASSET_MAP = ROOT / "archive" / "assets.json"

NAV = (
    ('ABOUT', '#about'),
    ('TEAM', '#team'),
    ('EXPERIENCE', '#experience'),
    ('ARCHIVE', '#archive'),
    ('GALLERY', '#gallery'),
    ('VIDEOS', '#videos'),
    ('CONNECT', '#connect'),
)

EVENTS = (
    ('2019年12月15日（日）：ZenITプログラミング教室（初心者向け）', 'Sunday, December 15, 2019', '9:00 AM–12:00 PM'),
    ('NHKでのZenITの放送', 'Wednesday, October 9, 2019', '6:10 PM–7:00 PM'),
    ('2019年4月14日（日）：禅ITプログラミング教室（初心者向け）', 'Sunday, April 14, 2019', '9:30 AM–4:00 PM'),
    ('2019年1月27日（日）：禅ITプログラミング教室（初心者向け）', 'Sunday, January 27, 2019', '9:30 AM–4:00 PM'),
    ('2018年12月2日（日）：禅×プログラミング基礎ワークショップ（初心者向け）', 'Sunday, December 2, 2018', '1:00 PM–4:00 PM'),
)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def base_image(url: str) -> str:
    return url.split('/v1/', 1)[0]


def asset_path(url: str, mapping: dict[str, str], prefix: str = '') -> str:
    return prefix + mapping[base_image(url)]


def image_list(record: dict, mapping: dict[str, str], prefix: str = '', limit: int = 12) -> list[dict]:
    chosen: dict[str, dict] = {}
    for image in record['images']:
        original = base_image(image['src'])
        if original not in mapping:
            continue
        if image.get('width', 0) < 240 or image.get('height', 0) < 150:
            continue
        score = image.get('width', 0) * image.get('height', 0)
        if original not in chosen or score > chosen[original]['score']:
            chosen[original] = {
                'src': asset_path(image['src'], mapping, prefix),
                'alt': image.get('alt') or 'ZenIT archive photograph',
                'score': score,
            }
    return sorted(chosen.values(), key=lambda item: item['score'], reverse=True)[:limit]


def split_paragraphs(text: str) -> list[str]:
    return [re.sub(r'\s+', ' ', item).strip() for item in re.split(r'\n\s*\n', text) if item.strip()]


def post_lines(record: dict) -> list[str]:
    lines = [re.sub(r'\s+', ' ', line).strip() for line in record['text'].splitlines()]
    ignored_exact = {'All Posts', 'amilkh5', 'Get Started', 'ZenIT', '日本語', 'ABOUT', 'TEAM', 'EXPERIENCE', 'BLOG', 'CONNECT', 'GALLERY', 'VIDEOS'}
    cleaned: list[str] = []
    title = record['title'].replace(' | ZenIT', '')
    for line in lines:
        if not line or line in ignored_exact or line == title:
            continue
        if re.fullmatch(r'\d+ min read', line):
            continue
        if re.fullmatch(r'\d+ views?', line) or re.fullmatch(r'\d+ comments?', line):
            continue
        if line.startswith('This website was built on Wix'):
            continue
        cleaned.append(line)
    return cleaned


def post_date(lines: list[str]) -> str:
    pattern = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+20\d{2}$')
    return next((line for line in lines if pattern.match(line)), '2018–2019')


def slug_for(record: dict) -> str:
    path = urlparse(record['url']).path.rstrip('/').split('/')[-1]
    return re.sub(r'[^a-z0-9-]+', '-', path.lower()).strip('-') or 'post'


def header(prefix: str = '') -> str:
    nav = ''.join(f'<a href="{prefix}index.html{href}">{label}</a>' for label, href in NAV)
    return f'''<header class="site-header">
      <a class="brand" href="{prefix}index.html" aria-label="ZenIT home">ZenIT</a>
      <button class="menu-button" type="button" aria-label="Open navigation" aria-expanded="false">Menu</button>
      <nav class="site-nav" aria-label="Primary navigation">{nav}<a href="{prefix}ja.html" lang="ja">日本語</a></nav>
    </header>'''


def footer(prefix: str = '') -> str:
    return f'''<footer class="site-footer">
      <div><strong>ZenIT</strong><span>Static archive of the 2018–2019 project.</span></div>
      <div class="footer-links"><a href="mailto:info@zenit.jp">info@zenit.jp</a><a href="https://www.youtube.com/channel/UCGm_0jDeZ5CdThD9Kf9_opw">YouTube</a></div>
    </footer><script src="{prefix}assets/site.js"></script>'''


def document(title: str, body: str, prefix: str = '', description: str = 'ZenIT: making every workplace a retreat.') -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#07145b">
  <link rel="canonical" href="https://zenit.jp/">
  <link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>{header(prefix)}<main>{body}</main>{footer(prefix)}</body>
</html>'''


def build_posts(records: list[dict], mapping: dict[str, str]) -> list[dict]:
    posts_dir = ROOT / 'posts'
    posts_dir.mkdir(exist_ok=True)
    posts: list[dict] = []
    for record in records:
        if '/post/' not in record['url']:
            continue
        title = record['title'].replace(' | ZenIT', '')
        lines = post_lines(record)
        date = post_date(lines)
        body_lines = [line for line in lines if line != date]
        images = image_list(record, mapping, prefix='../', limit=16)
        lead = next((line for line in body_lines if len(line) > 55), 'A moment from the ZenIT archive.')
        gallery = ''.join(f'<figure><img src="{esc(item["src"])}" alt="{esc(item["alt"])}" loading="lazy"></figure>' for item in images)
        paragraphs = ''.join(f'<p>{esc(line)}</p>' for line in body_lines)
        slug = slug_for(record)
        article = f'''<article class="post shell">
          <a class="back-link" href="../index.html#archive">← Back to archive</a>
          <p class="eyebrow">ZENIT ARCHIVE</p><h1>{esc(title)}</h1><p class="post-date">{esc(date)}</p>
          <div class="post-copy">{paragraphs}</div>
          <div class="post-gallery">{gallery}</div>
        </article>'''
        (posts_dir / f'{slug}.html').write_text(document(f'{title} | ZenIT', article, '../', lead), encoding='utf-8')
        posts.append({'title': title, 'date': date, 'lead': lead, 'href': f'posts/{slug}.html', 'image': images[0]['src'][3:] if images else ''})
    return posts


def main() -> None:
    records = json.loads(SOURCE.read_text(encoding='utf-8'))
    mapping = json.loads(ASSET_MAP.read_text(encoding='utf-8'))
    by_url = {record['url']: record for record in records}
    home_record = by_url['https://amilkh5.wixsite.com/my-site']
    about_record = by_url['https://amilkh5.wixsite.com/my-site/about']
    team_record = by_url['https://amilkh5.wixsite.com/my-site/team']
    gallery_record = by_url['https://amilkh5.wixsite.com/my-site/gallery']

    home_image = image_list(home_record, mapping, limit=1)[0]['src']
    about_image = image_list(about_record, mapping, limit=1)[0]['src']
    gallery_images = image_list(gallery_record, mapping, limit=8)
    about_paragraphs = split_paragraphs(about_record['text'])[1:]
    posts = build_posts(records, mapping)

    team = (
        ('Amil Khanzada', {'src': 'assets/images/02976c_902087413f0e42bb972c6dc34a54f2ed~mv2.jpg'}, 'Founder. UC Berkeley Computer Science alumnus, Eiheiji Town Evolution Ambassador, and One Young World Peace Ambassador.'),
        ('Taisuke Fukuno', {'src': 'assets/images/02976c_af66d47a73af4beeb9b14044d980f642~mv2.jpg'}, 'Founder and chair of jig.jp, open-data advocate, and creator of IchigoJam.'),
        ('Hira Khanzada', {'src': 'assets/images/02976c_922d0f832c3d4f07b2d46d3e57b11cf0~mv2.jpg'}, 'Mental health therapist and UC Berkeley alumna focused on holistic healing and mindfulness.'),
        ('Hisamitsu Kawai', {'src': 'assets/images/02976c_6fd745bde3f14c378056e7b8e5535e57~mv2.jpg'}, 'Former Mayor of Eiheiji Town and Zen culture advocate.'),
    )
    team_cards = ''.join(f'''<article class="person-card"><img src="{esc(image['src'])}" alt="Portrait of {esc(name)}" loading="lazy"><div><h3>{esc(name)}</h3><p>{esc(bio)}</p></div></article>''' for name, image, bio in team)
    about_copy = ''.join(f'<p>{esc(paragraph)}</p>' for paragraph in about_paragraphs)
    event_cards = ''.join(f'''<article class="event-card"><p class="event-date">{esc(date)}</p><h3>{esc(title)}</h3><p>{esc(time)}</p></article>''' for title, date, time in EVENTS)
    post_cards = ''.join(f'''<article class="archive-card">{f'<img src="{esc(post["image"])}" alt="" loading="lazy">' if post['image'] else ''}<div><p class="event-date">{esc(post['date'])}</p><h3><a href="{esc(post['href'])}">{esc(post['title'])}</a></h3><p>{esc(post['lead'][:190])}</p></div></article>''' for post in posts)
    gallery = ''.join(f'<img src="{esc(image["src"])}" alt="{esc(image["alt"])}" loading="lazy">' for image in gallery_images)

    body = f'''
      <section class="hero" style="--hero-image:url('../{esc(home_image)}')"><div class="hero-overlay"><p class="eyebrow">ZENIT · 2018–2019 ARCHIVE</p><h1>Making every workplace a retreat</h1><p lang="ja">職場に禅の心を</p><a class="button" href="#about">Explore the project</a></div></section>
      <section class="archive-note shell"><p>This site preserves ZenIT’s workshops, people, and ideas from 2018–2019. The project explored how Zen practice and collaborative technology work could create calmer, more humane workplaces.</p></section>
      <section class="section shell" id="about"><div class="section-heading"><p class="eyebrow">ABOUT</p><h2>Peaceful work, ambitious idea</h2></div><div class="about-grid"><img src="{esc(about_image)}" alt="Temple architecture in Eiheiji" loading="lazy"><div class="long-copy">{about_copy}</div></div></section>
      <section class="section section-tint" id="team"><div class="shell"><div class="section-heading"><p class="eyebrow">TEAM</p><h2>People behind ZenIT</h2></div><div class="team-grid">{team_cards}</div></div></section>
      <section class="section shell" id="experience"><div class="section-heading"><p class="eyebrow">EXPERIENCE</p><h2>Workshops and broadcasts</h2></div><div class="events-grid">{event_cards}</div></section>
      <section class="section section-dark" id="archive"><div class="shell"><div class="section-heading"><p class="eyebrow">ARCHIVE</p><h2>Stories from the project</h2></div><div class="archive-grid">{post_cards}</div></div></section>
      <section class="section shell" id="gallery"><div class="section-heading"><p class="eyebrow">GALLERY</p><h2>Zen, programming, and community</h2></div><div class="gallery-grid">{gallery}</div></section>
      <section class="section video-section" id="videos"><div class="shell video-grid"><div><p class="eyebrow">VIDEOS</p><h2>ZenIT in practice</h2><p>Watch a workshop from the archive or visit the ZenIT YouTube channel.</p><a class="text-link" href="https://www.youtube.com/channel/UCGm_0jDeZ5CdThD9Kf9_opw">View the YouTube channel →</a></div><div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/jTU8EDfUNbM" title="ZenIT archive video" loading="lazy" allowfullscreen></iframe></div></div></section>
      <section class="section shell contact" id="connect"><p class="eyebrow">CONNECT</p><h2>ZenIT archive</h2><p>For questions about the project, write to <a href="mailto:info@zenit.jp">info@zenit.jp</a>.</p></section>
    '''
    (ROOT / 'index.html').write_text(document('ZenIT | Making every workplace a retreat', body), encoding='utf-8')

    japanese = f'''
      <section class="hero compact" style="--hero-image:url('../{esc(home_image)}')"><div class="hero-overlay"><p class="eyebrow">ZENIT · 2018–2019 アーカイブ</p><h1 lang="ja">職場に禅の心を</h1><p>Making every workplace a retreat</p></div></section>
      <section class="section shell"><div class="section-heading"><p class="eyebrow">禅ITについて</p><h2>禅とテクノロジーの協働</h2></div><div class="long-copy"><p>ZenITは、禅の実践とシリコンバレー式のペアワークを通じ、穏やかで創造的な働き方を探求したプロジェクトです。</p><p>このサイトは、2018年から2019年に行われたワークショップ、イベント、活動記録を保存するアーカイブです。</p><p><a class="text-link" href="index.html#archive">活動記録を見る →</a></p></div></section>
      <section class="section section-tint"><div class="shell"><div class="section-heading"><p class="eyebrow">お問い合わせ</p><h2>ZenITアーカイブ</h2></div><p><a href="mailto:info@zenit.jp">info@zenit.jp</a></p></div></section>
    '''
    (ROOT / 'ja.html').write_text(document('禅IT | 職場に禅の心を', japanese), encoding='utf-8')

    (ROOT / 'CNAME').write_text('zenit.jp\n', encoding='utf-8')
    (ROOT / '.nojekyll').write_text('', encoding='utf-8')


if __name__ == '__main__':
    main()

"""Fetch Atom/RSS candidates; selection and writing are performed by the agent."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
from email.utils import parsedate_to_datetime
from html import unescape
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET
from store import ROOT, JST, read, now

SOURCES = [('music','音楽','音楽ナタリー'), ('owarai','お笑い','お笑いナタリー'), ('eiga','映画・マンガ','映画ナタリー'), ('comic','映画・マンガ','コミックナタリー')]
NS = {'a': 'http://www.w3.org/2005/Atom'}

def parse(xml, category, name):
    root = ET.fromstring(xml)
    result = []
    for e in root.findall('a:entry', NS):
        links = e.findall('a:link', NS)
        link = next((x.get('href') for x in links if x.get('rel', 'alternate') == 'alternate'), '')
        result.append({'title': e.findtext('a:title', '', NS), 'url': link, 'published_at': e.findtext('a:published', '', NS) or e.findtext('a:updated', '', NS), 'excerpt': e.findtext('a:summary', '', NS), 'category': category, 'source_name': name})
    for e in root.findall('.//item'):
        raw = e.findtext('pubDate', '')
        try:
            stamp = parsedate_to_datetime(raw).isoformat()
        except (ValueError, TypeError):
            continue
        result.append({'title': e.findtext('title',''), 'url': e.findtext('link',''), 'published_at': stamp, 'excerpt': e.findtext('description',''), 'category':category, 'source_name':name})
    for p in result:
        p['excerpt'] = unescape(re.sub('<[^>]+>', '', p['excerpt']))[:1200]
    return result

def fetch(source):
    section, cat, name = source
    url = f'https://natalie.mu/{section}/feed/news'
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'HeiseiSubculture/1.0 (personal RSS reader)'})
        with urllib.request.urlopen(req, timeout=25) as response:
            rows = parse(response.read(2_000_000), cat, name)
        if not rows:
            raise ValueError('フィードに記事がありません')
        return rows, None
    except Exception as e:
        return [], f'{name}: {type(e).__name__}: {e}'

def collect(hours=48):
    cutoff = dt.datetime.now(JST) - dt.timedelta(hours=hours)
    seen = {p.get('source_url') for p in read()['posts']}
    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for batch, error in pool.map(fetch, SOURCES):
            if error: errors.append(error)
            for p in batch:
                try:
                    stamp = dt.datetime.fromisoformat(p['published_at'])
                    if stamp.tzinfo is None or stamp < cutoff or stamp > dt.datetime.now(JST) + dt.timedelta(minutes=5): continue
                except ValueError:
                    continue
                if p['url'] in seen or not p['url'].startswith('https://natalie.mu/'): continue
                seen.add(p['url'])
                if any(w in p['title'] for w in ['モーニング娘', 'ハロプロ', 'ハロー！', 'つんく', 'アンジュルム', 'Juice=Juice', 'BEYOOOOONDS', 'OCHA NORMA', 'つばきファクトリー']): p['category'] = 'アイドル'
                rows.append(p)
    if len(errors) == len(SOURCES):
        raise RuntimeError('全フィードの取得失敗: ' + '; '.join(errors))
    return {'collected_at': now(), 'errors': errors, 'candidates': sorted(rows, key=lambda p:p['published_at'], reverse=True)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--hours', type=int, default=168, help='RSS候補の範囲。過去記事は別途Web検索で発掘する')
    args = parser.parse_args()
    doc = collect(args.hours)
    Path(args.output).write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f"候補 {len(doc['candidates'])}件、取得エラー {len(doc['errors'])}件 → {args.output}")

"""Validated, atomic content storage. Standard library only."""
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/posts.json'
CATEGORIES = ['音楽', 'アイドル', '映画・マンガ', 'お笑い', '雑記']
JST = dt.timezone(dt.timedelta(hours=9))

def now():
    return dt.datetime.now(JST).isoformat(timespec='seconds')

def validate(p):
    if not isinstance(p, dict):
        raise ValueError('投稿の形式が不正です')
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', p.get('id', '')):
        raise ValueError('投稿IDが不正です')
    if p.get('type') not in ['news', 'thought'] or p.get('category') not in CATEGORIES:
        raise ValueError('投稿種別・カテゴリが不正です')
    for key, limit in [('title', 140), ('summary', 400), ('comment', 4000), ('source_name', 100), ('source_url', 2000), ('image_url', 2000), ('selection_reason', 300)]:
        if not isinstance(p.get(key, ''), str) or len(p.get(key, '')) > limit:
            raise ValueError(f'{key}の長さ・形式を確認してください')
    if not p.get('title', '').strip():
        raise ValueError('タイトルを入力してください')
    if p['type'] == 'thought' and not p.get('comment', '').strip():
        raise ValueError('つぶやきを入力してください')
    if p['type'] == 'news':
        if not p.get('summary', '').strip() or not p.get('source_name', '').strip():
            raise ValueError('ニュースには要約と出典名が必要です')
        u = urlsplit(p.get('source_url', ''))
        if u.scheme != 'https' or not u.hostname or u.username or u.password:
            raise ValueError('出典にはHTTPSのURLを指定してください')
    if p.get('image_url'):
        image = urlsplit(p['image_url'])
        if image.scheme != 'https' or not image.hostname or image.username or image.password:
            raise ValueError('画像にはHTTPSのURLを指定してください')
    for field in ['published_at', 'created_at']:
        d = dt.datetime.fromisoformat(p[field])
        if d.tzinfo is None:
            raise ValueError('日時にはタイムゾーンが必要です')
    if p.get('ai_generated') not in [True, False]:
        raise ValueError('AI生成表示が必要です')
    return p

def read():
    return json.loads(DATA.read_text()) if DATA.exists() else {'updated_at': None, 'posts': []}

@contextlib.contextmanager
def locked():
    with (ROOT / 'data/.lock').open('w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield

def atomic(path, content):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(content, encoding='utf-8')
    os.replace(tmp, path)

def save(document):
    ids, urls = set(), set()
    for p in document['posts']:
        validate(p)
        if p['id'] in ids:
            raise ValueError('投稿IDが重複しています')
        ids.add(p['id'])
        if p['type'] == 'news':
            if p['source_url'] in urls:
                raise ValueError('ニュースの出典URLが重複しています')
            urls.add(p['source_url'])
    if DATA.exists():
        atomic(ROOT / 'data/posts.backup.json', DATA.read_text())
    atomic(DATA, json.dumps(document, ensure_ascii=False, indent=2) + '\n')

def build():
    doc = read()
    for p in doc['posts']:
        validate(p)
    # JS assignment also works when the user opens index.html directly.
    content = json.dumps(doc, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    atomic(ROOT / 'site/feed.js', 'window.HEISEI_FEED = ' + content + ';\n')

if __name__ == '__main__':
    with locked():
        build()
    print('Built site/feed.js')

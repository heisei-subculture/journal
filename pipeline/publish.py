"""Merge an agent-curated batch without overwriting human comments."""
import argparse
import json
import datetime as dt
from pathlib import Path
from store import validate, locked, read, save, build, now, JST

def merge(document, batch):
    if not isinstance(batch, list) or len(batch) > 5:
        raise ValueError('1回のニュースは最大5件です')
    today = dt.datetime.now(JST).date()
    count = sum(p['type']=='news' and p.get('ai_generated') and p.get('selected_by') != 'user' and dt.datetime.fromisoformat(p['created_at']).astimezone(JST).date()==today for p in document['posts'])
    known = {p['id'] for p in document['posts']}
    urls = {p.get('source_url') for p in document['posts']}
    added = []
    for p in batch:
        validate(p)
        if p['type'] != 'news' or not p['ai_generated'] or p.get('comment'):
            raise ValueError('AI配信はニュースのみ。本人のコメントは生成しません')
        if dt.datetime.fromisoformat(p['created_at']).astimezone(JST).date() != today:
            raise ValueError('作成日は今日にしてください')
        if p['id'] in known or p['source_url'] in urls: continue
        added.append(p)
        known.add(p['id']); urls.add(p['source_url'])
    if count + len(added) > 5:
        raise ValueError('本日のAIニュースは合計最大5件です')
    if added:
        document = {**document, 'updated_at': now(), 'posts': added + document['posts']}
    return document, len(added)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('batch')
    args = parser.parse_args()
    with locked():
        document, count = merge(read(), json.loads(Path(args.batch).read_text()))
        if count: save(document)
        build()
    print(f'{count}件をローカルへ反映しました（外部公開なし）')

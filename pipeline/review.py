"""Local review queue; never published by the site packager."""
import json
from pathlib import Path
from store import ROOT, atomic, validate, read, save, build, now, locked
QUEUE = ROOT / 'data/review.json'
def read_queue():
    return json.loads(QUEUE.read_text()) if QUEUE.exists() else {'candidates': []}
def editor_queue():
    queue = read_queue()
    articles = [p for p in read()['posts'] if p['type'] == 'news']
    by_url = {p['source_url']: p for p in articles}
    candidates = []
    for candidate in queue['candidates']:
        post = by_url.pop(candidate['source_url'], None)
        if post is not None:
            candidate = {**candidate, **post, 'id': candidate['id'], 'review_status': 'approved'}
        candidates.append(candidate)
    candidates.extend({**p, 'review_status': 'approved'} for p in by_url.values())
    return {**queue, 'candidates': candidates}

def save_queue(queue):
    for p in queue['candidates']: validate(p)
    atomic(QUEUE, json.dumps(queue, ensure_ascii=False, indent=2)+'\n')
def stage(batch):
    q=read_queue(); known={p['source_url'] for p in q['candidates']}|{p.get('source_url') for p in read()['posts']}
    if len(batch)>10: raise ValueError('候補は1回最大10件です')
    added=0
    for p in batch:
        validate(p)
        if p['type']!='news' or p.get('comment'): raise ValueError('候補はニュースのみ。本人コメントは空欄にしてください')
        if p['source_url'] in known: continue
        q['candidates'].append({**p,'review_status':'pending'});known.add(p['source_url']);added+=1
    save_queue(q);return added
def decide(id, action):
    if action not in ('approve','reject','pending','withdraw'): raise ValueError('操作が不正です')
    q=read_queue();p=next((p for p in q['candidates'] if p['id']==id),None)
    if action == 'withdraw':
        doc = read()
        published = next((post for post in doc['posts'] if post['type'] == 'news' and
                          (post['id'] == id or (p and post['source_url'] == p['source_url']))), None)
        if published is None and (p is None or p.get('review_status') != 'approved'):
            raise ValueError('採用済みの記事だけ取り下げできます')
        if published is not None:
            if p is None:
                p = next((x for x in q['candidates'] if x['source_url'] == published['source_url']), None)
            if p is None:
                p = dict(published)
                q['candidates'].append(p)
            else:
                p.update({k: v for k, v in published.items() if k != 'id'})
        # Save the latest article and its comments before removing the published copy.
        p.update(review_status='pending', reviewed_at=now())
        save_queue(q)
        if published is not None:
            doc['posts'].remove(published)
            doc['updated_at'] = now()
            save(doc)
        build()
        return
    if p is None: raise ValueError('候補が見つかりません')
    if action=='approve':
        doc=read()
        if not any(x['id']==id or x.get('source_url')==p['source_url'] for x in doc['posts']):
            post={k:v for k,v in p.items() if k not in ('review_status','reviewed_at')}
            post.update(created_at=now(),selected_by='user',approved_at=now())
            doc['posts'].insert(0,post);doc['updated_at']=now();save(doc)
        build()
    elif p.get('review_status')=='approved': raise ValueError('掲載済み記事はここでは見送りにできません')
    p.update(review_status={'approve':'approved','reject':'rejected','pending':'pending'}[action],reviewed_at=now());save_queue(q)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('batch');args=parser.parse_args()
    with locked():count=stage(json.loads(Path(args.batch).read_text()))
    print(f'{count}件を確認待ちへ保存しました（掲載なし）')

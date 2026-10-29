"""Loopback-only editor and preview. Never deploy this editor as a public API."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import uuid
from urllib.parse import urlsplit
from store import ROOT, read, validate, save, locked, build, now

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'site'), **kwargs)

    def safe_host(self):
        return self.headers.get('Host') in ['127.0.0.1:8765', 'localhost:8765']

    def reply(self, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def do_GET(self):
        if not self.safe_host(): return self.reply(403, {'error':'Host not allowed'})
        if urlsplit(self.path).path == '/api/posts': return self.reply(200, read())
        return super().do_GET()

    def do_POST(self):
        if not self.safe_host() or self.headers.get('Origin') != 'http://' + self.headers.get('Host','') or self.headers.get('X-Heisei-Editor') != '1':
            return self.reply(403, {'error':'ローカル編集画面から保存してください'})
        if self.path != '/api/posts': return self.reply(404, {'error':'Not found'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 30000: raise ValueError('投稿サイズが不正です')
            p = json.loads(self.rfile.read(size))
            with locked():
                doc = read()
                old = next((x for x in doc['posts'] if x['id'] == p.get('id')), None)
                if p.get('id') and old is None: raise ValueError('編集対象が見つかりません')
                if old:
                    # Editor updates human commentary only; AI evidence remains intact.
                    post = {**old, 'comment': p.get('comment','')}
                    if old['type'] == 'thought': post.update(title=p.get('title',''), category=p.get('category',''))
                    post['edited_at'] = now()
                else:
                    post = {'id': 'note-' + uuid.uuid4().hex[:12], 'type':'thought', 'title':p.get('title',''), 'comment':p.get('comment',''), 'category':p.get('category','雑記'), 'published_at':now(), 'created_at':now(), 'ai_generated':False}
                validate(post)
                doc['posts'] = [post if x['id'] == post['id'] else x for x in doc['posts']] if old else [post] + doc['posts']
                doc['updated_at'] = now()
                save(doc); build()
            self.reply(200, {'ok':True, 'id':post['id']})
        except (ValueError, KeyError, TypeError) as e:
            self.reply(400, {'error':str(e)})

if __name__ == '__main__':
    with locked(): build()
    print('平成サブカル通信 http://127.0.0.1:8765\n編集室 http://127.0.0.1:8765/editor.html', flush=True)
    HTTPServer(('127.0.0.1',8765), Handler).serve_forever()

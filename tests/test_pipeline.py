import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from store import validate, now
from collect import parse
from publish import merge

def post(id='one'):
    return {'id':id,'type':'news','category':'音楽','title':'テスト','summary':'要約','comment':'','source_name':'媒体','source_url':'https://example.com/'+id,'published_at':'2007-01-01T00:00:00+09:00','created_at':now(),'ai_generated':True}

class PipelineTests(unittest.TestCase):
    def test_original_date_can_be_old(self):
        self.assertEqual(validate(post())['published_at'][:4], '2007')
    def test_script_url_rejected(self):
        p=post();p['source_url']='javascript:alert(1)'
        with self.assertRaises(ValueError): validate(p)
    def test_duplicate_keeps_human_comment(self):
        p=post();p['comment']='本人の言葉'
        doc,n=merge({'posts':[p],'updated_at':'unchanged'},[post()])
        self.assertEqual(n,0);self.assertEqual(doc['posts'][0]['comment'],'本人の言葉')
    def test_ai_cannot_write_personal_comment(self):
        p=post();p['comment']='懐かしい！'
        with self.assertRaises(ValueError): merge({'posts':[]},[p])
    def test_daily_limit_across_runs(self):
        existing=[post(str(i)) for i in range(4)]
        with self.assertRaises(ValueError):merge({'posts':existing},[post('a'),post('b')])
    def test_duplicates_within_batch(self):
        doc,n=merge({'posts':[]},[post(),post()])
        self.assertEqual(n,1)
    def test_atom_and_rss(self):
        atom='<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>曲</title><link href="https://example.com/a"/><updated>2026-10-30T00:00:00+09:00</updated><summary>&lt;b&gt;本文&lt;/b&gt;</summary></entry></feed>'
        rows=parse(atom,'音楽','媒体');self.assertEqual(rows[0]['excerpt'],'本文')
        rss='<rss><channel><item><title>曲</title><link>https://example.com/a</link><pubDate>Fri, 30 Oct 2026 00:00:00 +0900</pubDate><description>本文</description></item></channel></rss>'
        self.assertEqual(len(parse(rss,'音楽','媒体')),1)

if __name__ == '__main__': unittest.main()

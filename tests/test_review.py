import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pipeline'))
import review
import store
class ReviewTests(unittest.TestCase):
 def test_approve_only_once_and_keep_comments(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'data').mkdir();(root/'site').mkdir()
   p=copy.deepcopy(store.read()['posts'][0]);p['id']='test-review';p['comment']='本人のコメント'
   with patch.object(store,'ROOT',root),patch.object(store,'DATA',root/'data/posts.json'),patch.object(review,'QUEUE',root/'data/review.json'):
    store.save({'updated_at':None,'posts':[]});review.save_queue({'candidates':[{**p,'review_status':'pending'}]})
    review.decide(p['id'],'reject');self.assertEqual(store.read()['posts'],[])
    review.decide(p['id'],'pending');review.decide(p['id'],'approve');review.decide(p['id'],'approve')
    posts=store.read()['posts'];self.assertEqual(len(posts),1);self.assertEqual(posts[0]['comment'],'本人のコメント');self.assertEqual(posts[0]['selected_by'],'user')
    self.assertEqual(review.read_queue()['candidates'][0]['review_status'],'approved')
    self.assertNotIn('review_status',(root/'site/feed.js').read_text())
 def test_withdraw_preserves_latest_comment_and_can_reapprove(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'data').mkdir();(root/'site').mkdir()
   p=copy.deepcopy(next(x for x in store.read()['posts'] if x['type']=='news'));p['id']='withdraw-test';p['comment']=''
   with patch.object(store,'ROOT',root),patch.object(store,'DATA',root/'data/posts.json'),patch.object(review,'QUEUE',root/'data/review.json'):
    store.save({'updated_at':None,'posts':[]});review.save_queue({'candidates':[{**p,'review_status':'pending'}]})
    with self.assertRaises(ValueError):review.decide(p['id'],'withdraw')
    review.decide(p['id'],'approve')
    doc=store.read();doc['posts'][0]['comment']='採用後に書いたコメント';store.save(doc)
    review.decide(p['id'],'withdraw')
    self.assertEqual(store.read()['posts'],[])
    self.assertNotIn(p['id'],(root/'site/feed.js').read_text())
    candidate=review.read_queue()['candidates'][0]
    self.assertEqual(candidate['review_status'],'pending')
    self.assertEqual(candidate['comment'],'採用後に書いたコメント')
    self.assertEqual(candidate['summary'],p['summary'])
    review.decide(p['id'],'approve')
    self.assertEqual(len(store.read()['posts']),1)
    self.assertEqual(store.read()['posts'][0]['comment'],'採用後に書いたコメント')
 def test_legacy_article_can_be_withdrawn_and_approved(self):
  with tempfile.TemporaryDirectory() as folder:
   root = Path(folder)
   (root/'data').mkdir()
   (root/'site').mkdir()
   article = copy.deepcopy(next(x for x in store.read()['posts'] if x['type']=='news'))
   article.update(id='legacy', comment='掲載後の本人コメント')
   thought = dict(article, id='note', type='thought')
   with patch.object(store,'ROOT',root), patch.object(store,'DATA',root/'data/posts.json'), patch.object(review,'QUEUE',root/'data/review.json'):
    store.save({'updated_at':None,'posts':[article, thought]})
    self.assertEqual(review.editor_queue()['candidates'], [{**article,'review_status':'approved'}])
    self.assertFalse(review.QUEUE.exists())
    with self.assertRaises(ValueError): review.decide('note','withdraw')
    review.decide('legacy','withdraw')
    self.assertEqual(store.read()['posts'], [thought])
    candidate, = review.editor_queue()['candidates']
    self.assertEqual(candidate['review_status'], 'pending')
    self.assertEqual(candidate['comment'], article['comment'])
    review.decide('legacy','approve')
    self.assertEqual(len(review.editor_queue()['candidates']), 1)
    self.assertEqual(store.read()['posts'][0]['comment'], article['comment'])
 def test_withdraw_by_published_id_reuses_candidate_with_same_url(self):
  with tempfile.TemporaryDirectory() as folder:
   root = Path(folder)
   (root/'data').mkdir()
   (root/'site').mkdir()
   article = copy.deepcopy(next(x for x in store.read()['posts'] if x['type']=='news'))
   article.update(id='published', comment='最新のコメント')
   with patch.object(store,'ROOT',root), patch.object(store,'DATA',root/'data/posts.json'), patch.object(review,'QUEUE',root/'data/review.json'):
    store.save({'updated_at':None,'posts':[article]})
    review.save_queue({'candidates':[{**article,'id':'candidate','review_status':'approved','comment':''}]})
    candidate, = review.editor_queue()['candidates']
    self.assertEqual(candidate['id'], 'candidate')
    review.decide('published','withdraw')
    candidate, = review.editor_queue()['candidates']
    self.assertEqual((candidate['id'],candidate['review_status'],candidate['comment']), ('candidate','pending',article['comment']))
    self.assertEqual(store.read()['posts'], [])
 def test_invalid_action_does_not_write(self):
  with self.assertRaises(ValueError):review.decide('missing','delete')

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
 def test_invalid_action_does_not_write(self):
  with self.assertRaises(ValueError):review.decide('missing','delete')

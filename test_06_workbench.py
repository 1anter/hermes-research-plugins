import json,pathlib,tempfile,unittest,sqlite3
from suite_tools import ROOT,load,Context
class WorkbenchTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.t.cleanup);self.p=load('component-workbench');self.p._db_path=lambda:pathlib.Path(self.t.name)/'w.sqlite';self.c=Context();self.p.register(self.c);self.spec={'case1':{'output':10}};self.proposal={'candidate_id':'c1','author_id':'author','files':{'plugin.py':'x=1\n'}}
 def call(self,n,**a):return json.loads(self.c.tools[n]['handler'](a))
 def frozen(self):
  h=self.call('workbench_propose',**self.proposal)['data']['candidate_sha256'];self.call('workbench_validate',candidate_id='c1');self.assertTrue(self.call('workbench_freeze',candidate_id='c1',evaluation_spec_sha256=self.p.digest(self.p.canonical(self.spec)))['ok']);return h
 def review(self,h,**extra):
  args={'candidate_id':'c1','candidate_sha256':h,'verifier_id':'independent','evaluation_spec':self.spec,'actual_results':self.spec,'execution_artifact_sha256':'0'*64};args.update(extra);return self.call('workbench_review',**args)
 def test_complete_state_machine(self):
  h=self.frozen();r=self.review(h);self.assertTrue(r['data']['passed_against_committed_spec']);self.assertEqual(r['data']['execution_provenance'],'caller_attested_not_authenticated');s=self.call('workbench_status',candidate_id='c1')['data'];self.assertEqual(s['state'],'review_ready');self.assertEqual(len(s['reviews']),1)
 def test_invalid_syntax(self):
  self.call('workbench_propose',**{**self.proposal,'files':{'bad.py':'def :'}});self.assertFalse(self.call('workbench_validate',candidate_id='c1')['data']['passed']);self.assertFalse(self.call('workbench_freeze',candidate_id='c1',evaluation_spec_sha256='0'*64)['ok'])
 def test_no_freeze_before_validation(self):
  self.call('workbench_propose',**self.proposal);self.assertFalse(self.call('workbench_freeze',candidate_id='c1',evaluation_spec_sha256='0'*64)['ok'])
 def test_cannot_change_frozen(self):
  self.frozen();self.assertFalse(self.call('workbench_propose',**{**self.proposal,'files':{'plugin.py':'x=2'}})['ok'])
 def test_mismatched_spec(self):self.assertFalse(self.review(self.frozen(),evaluation_spec={'case2':2})['ok'])
 def test_wrong_candidate_hash(self):self.frozen();self.assertFalse(self.review('0'*64)['ok'])
 def test_same_verifier_rejected(self):self.assertFalse(self.review(self.frozen(),verifier_id='author')['ok'])
 def test_failed_review_preserved(self):
  h=self.frozen();self.assertFalse(self.review(h,actual_results={'case1':{'output':9}})['data']['passed_against_committed_spec']);self.review(h);s=self.call('workbench_status',candidate_id='c1')['data'];self.assertEqual(len(s['reviews']),2);self.assertFalse(s['reviews'][0]['passed_against_committed_spec'])
 def test_paths(self):
  for name in ('../outside.py','/absolute.py','a/../b.py','C:/x.py','x\\y.py','.env','auth.json','run.exe'):
   with self.subTest(name=name):self.assertFalse(self.call('workbench_propose',**{**self.proposal,'files':{name:'x=1'}})['ok'])
 def test_diff(self):
  self.call('workbench_propose',**self.proposal);self.call('workbench_propose',**{**self.proposal,'candidate_id':'c2','files':{'plugin.py':'x=2\n'}});d=self.call('workbench_diff',before_id='c1',after_id='c2')['data']['diff'];self.assertIn('-x=1',d);self.assertIn('+x=2',d)
 def test_no_execution_or_promotion(self):
  sentinel=pathlib.Path(self.t.name)/'should-not-exist';self.call('workbench_propose',**{**self.proposal,'files':{'plugin.py':f'open({str(sentinel)!r},"w").write("bad")'}});self.call('workbench_validate',candidate_id='c1');self.assertFalse(sentinel.exists());self.assertNotIn('workbench_promote',self.c.tools)
 def test_tamper_detected(self):
  self.frozen();c=sqlite3.connect(self.p._db_path());c.execute('UPDATE candidates SET files=?',('{}',));c.commit();c.close();self.assertFalse(self.call('workbench_status',candidate_id='c1')['ok'])
 def test_strict_boolean(self):
  h=self.frozen();self.assertFalse(self.review(h,actual_results={'case1':{'output':True}})['data']['passed_against_committed_spec'])
if __name__=='__main__':unittest.main(verbosity=2)

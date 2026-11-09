import json,pathlib,tempfile,unittest
from suite_tools import ROOT,load,Context
class LedgerTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.t.cleanup);self.p=load('evaluation-ledger');self.p._db_path=lambda:pathlib.Path(self.t.name)/'ledger.sqlite';self.c=Context();self.p.register(self.c)
 def call(self,n,a):return json.loads(self.c.tools[n]['handler'](a))
 def test_registration(self):self.assertEqual(len(self.c.hooks),3);self.assertEqual(len(self.c.tools),3)
 def test_dedup_and_usage(self):
  k={'session_id':'parent','api_request_id':'a','provider':'custom','model':'local','usage':{'input_tokens':10,'cache_read_tokens':100,'output_tokens':2,'reasoning_tokens':1}}
  self.p.observe('post_api_request',**k);self.p.observe('post_api_request',**k)
  self.p.observe('post_api_request',**{**k,'session_id':'child','api_request_id':'b'})
  r=self.p.report(['parent','parent','child']);self.assertEqual(r['usage_by_route']['custom/local']['calls'],2);self.assertEqual(r['usage_by_route']['custom/local']['fields']['input_tokens'],20)
 def test_unknown_usage(self):
  self.p.observe('post_api_request',session_id='p',api_request_id='a',model='local');r=self.p.report(['p']);self.assertEqual(r['usage_by_route']['unknown/local']['missing_usage_calls'],1)
 def test_privacy(self):
  self.p.observe('post_api_request',session_id='p',api_request_id='a',request={'secret':'DO_NOT_SAVE'},response='DO_NOT_SAVE',error_message='DO_NOT_SAVE');self.assertNotIn('DO_NOT_SAVE',json.dumps(self.p.report(['p'])))
 def test_conflicting_duplicate(self):
  self.p.append('x','s','k',{'a':1})
  with self.assertRaises(ValueError):self.p.append('x','s','k',{'a':2})
 def test_artifact_checks(self):
  a={'run_id':'r','artifact_id':'a','content':'{"a":1}'};saved=self.call('evaluation_artifact',a)['data'];r=self.call('evaluation_check',{'run_id':'r','artifact_id':'a','expected_sha256':saved['sha256'],'expected_json':{'a':1}});self.assertTrue(r['data']['passed']);r=self.call('evaluation_check',{'run_id':'r','artifact_id':'a','expected_sha256':'0'*64});self.assertFalse(r['data']['passed'])
 def test_strict_json_and_immutability(self):
  a={'run_id':'r','artifact_id':'a','content':'true'};h=self.call('evaluation_artifact',a)['data']['sha256'];self.assertFalse(self.call('evaluation_check',{'run_id':'r','artifact_id':'a','expected_sha256':h,'expected_json':1})['data']['passed']);self.assertFalse(self.call('evaluation_artifact',{**a,'content':'false'})['ok'])
 def test_classification(self):
  for code,want in [(401,'auth'),(403,'auth'),(429,'quota'),(503,'outage')]:self.assertEqual(self.p.category(code,status='error'),want)
  self.assertEqual(self.p.category(reason='safety_refusal'),'refusal');self.assertEqual(self.p.category(reason='timeout'),'timeout_cancellation_unconfirmed')
 def test_invalid_schema(self):self.assertFalse(self.call('evaluation_report',{'session_ids':[]})['ok'])
 def test_no_false_usage(self):
  self.p.observe('post_api_request',session_id='p',api_request_id='a',usage={'input_tokens':True,'output_tokens':-1,'secret':100});self.assertEqual(self.p.report(['p'])['usage_by_route']['unknown/unknown']['fields'],{})
if __name__=='__main__':unittest.main(verbosity=2)

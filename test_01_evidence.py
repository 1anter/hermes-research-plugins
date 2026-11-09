import datetime as dt,json,pathlib,tempfile,unittest
from suite_tools import ROOT,load,Context
class EvidenceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.tmp.cleanup);self.p=load('evidence-history');self.p._db_path=lambda:pathlib.Path(self.tmp.name)/'db.sqlite'
  self.base={'claim_key':'forecast','evidence_id':'r1','source_url':'https://example.test/a','passage':'Forecast: 100. café 中文.','published_at':'2025-01-01T00:00:00Z','value':100}
 def call(self,n,**a):return json.loads(self.p.handle(n,a))
 def captured(self):return self.call('evidence_capture',**self.base)['data']['evidence']
 def verify(self,**changes):
  a={'claim_key':'forecast','evidence_id':'r1','cutoff':'2099-01-01T00:00:00Z','quote':'100','expected_value':100};a.update(changes);return self.call('evidence_verify_support',**a)['data']
 def test_registration(self):
  c=Context();self.p.register(c);self.assertEqual(len(c.tools),5);self.assertIn('evidence_verify_support',c.tools)
 def test_real_clock_and_persistence(self):
  before=dt.datetime.now(dt.timezone.utc);r=self.captured();after=dt.datetime.now(dt.timezone.utc);self.assertLessEqual(before,dt.datetime.fromisoformat(r['observed_at'].replace('Z','+00:00')));self.assertLessEqual(dt.datetime.fromisoformat(r['observed_at'].replace('Z','+00:00')),after);self.assertEqual(len(self.call('evidence_history',claim_key='forecast')['data']),1)
 def test_success_is_not_semantic_proof(self):
  self.captured();r=self.verify();self.assertTrue(r['structural_checks_passed']);self.assertEqual(r['semantic_verdict'],'not_assessed');self.assertTrue(r['semantic_review_required'])
 def test_cutoff_rejects_late_discovery(self):
  self.captured();self.assertFalse(self.verify(cutoff='2025-02-01T00:00:00Z')['structural_checks_passed'])
 def test_false_quote(self):
  self.captured();self.assertFalse(self.verify(quote='999')['structural_checks_passed'])
 def test_wrong_value(self):
  self.captured();self.assertFalse(self.verify(expected_value=101)['structural_checks_passed'])
 def test_wrong_id(self):
  self.captured();self.assertFalse(self.verify(evidence_id='missing')['structural_checks_passed'])
 def test_missing_claim(self):self.assertFalse(self.verify()['structural_checks_passed'])
 def test_duplicate_and_conflict(self):
  self.captured();self.assertFalse(self.call('evidence_capture',**self.base)['data']['inserted']);changed={**self.base,'value':999};self.assertFalse(self.call('evidence_capture',**changed)['ok']);self.assertEqual(self.call('evidence_history',claim_key='forecast')['data'][0]['value'],100)
 def test_reject_backdate(self):self.assertFalse(self.call('evidence_capture',**self.base,observed_at='2020-01-01T00:00:00Z')['ok'])
 def test_invalid(self):
  for changes in [{'source_url':'file:///private'},{'source_url':'https://u:p@example.test'},{'published_at':'2025-01-01'},{'value':float('nan')},{'passage':''}]:
   with self.subTest(changes=changes):self.assertFalse(self.call('evidence_capture',**{**self.base,**changes})['ok'])
 def test_type_strict_value(self):
  self.base['value']=True;self.captured();self.assertFalse(self.verify(expected_value=1)['structural_checks_passed'])
 def test_stale_revision(self):
  self.captured();self.call('evidence_capture',**{**self.base,'evidence_id':'r2','published_at':'2025-02-01T00:00:00Z','value':120,'passage':'Forecast: 120.'});self.assertFalse(self.verify()['structural_checks_passed']);self.assertTrue(self.verify(evidence_id='r2',quote='120',expected_value=120)['structural_checks_passed'])
if __name__=='__main__':unittest.main(verbosity=2)

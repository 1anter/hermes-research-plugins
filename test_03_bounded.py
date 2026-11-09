import json,pathlib,tempfile,unittest,sqlite3
from suite_tools import ROOT,load,Context
class BoundTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(self.t.cleanup);self.p=load('bounded-results');self.p._db_path=lambda:pathlib.Path(self.t.name)/'r.sqlite';self.c=Context();self.p.register(self.c)
 def call(self,a):return json.loads(self.c.tools['bounded_read']['handler'](a))
 def test_small_passthrough(self):self.assertIsNone(self.p.bound('evidence_history','small'))
 def test_other_tools_untouched(self):self.assertIsNone(self.p.bound('terminal','x'*10000));self.assertIsNone(self.p.bound('bounded_read','x'*10000))
 def test_full_roundtrip(self):
  text='中文 café\n'*3000;r=self.p.bound('evidence_history',text);self.assertLessEqual(len(r.encode('utf-8')),4096);h=json.loads(r)['handle'];chunks=[];offset=0
  while offset is not None:
   page=self.call({'handle':h,'offset':offset,'max_characters':313})['data'];chunks.append(page['text']);offset=page['next_offset']
  self.assertEqual(''.join(chunks),text)
 def test_dedup(self):
  x='x'*6000;self.assertEqual(self.p.bound('evidence_history',x),self.p.bound('evidence_history',x))
 def test_error_preserved(self):
  r=json.loads(self.p.bound('evidence_history',json.dumps({'ok':False,'error':'refused','details':'x'*9000})));self.assertEqual(r['upstream_status'],'error');self.assertEqual(r['upstream_error'],'refused')
 def test_schema_and_unknown(self):
  for a in [{'handle':'../private'},{'handle':'0'*64},{'handle':'0'*64,'offset':-1},{'handle':'0'*64,'max_characters':True}]:self.assertFalse(self.call(a)['ok'])
 def test_end_and_overrun(self):
  h=self.p.store('hello');self.assertEqual(self.call({'handle':h,'offset':5})['data']['next_offset'],None);self.assertFalse(self.call({'handle':h,'offset':6})['ok'])
 def test_corruption(self):
  h=self.p.store('hello');c=sqlite3.connect(self.p._db_path());c.execute('UPDATE results SET text=?',('corrupt',));c.commit();c.close();self.assertFalse(self.call({'handle':h})['ok'])
 def test_registration(self):self.assertEqual(list(self.c.hooks),['transform_tool_result'])
if __name__=='__main__':unittest.main(verbosity=2)

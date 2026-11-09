import unittest
from suite_tools import load,Context

class ConfigContext(Context):
 def __init__(self,value):super().__init__();self.value=value
 def get_config(self,key,default=None):
  return self.value if key=='observe_usage' else default

class ConsentTests(unittest.TestCase):
 def setup_case(self,value):
  p=load('evaluation-ledger');events=[];p.observe=lambda kind,**kw:events.append((kind,kw));c=ConfigContext(value);p.register(c);return c,events
 def test_default_off(self):
  c,events=self.setup_case(None)
  for cb in c.hooks.values():cb(session_id='s',usage={'input_tokens':1})
  self.assertEqual(events,[])
 def test_false_off(self):
  c,events=self.setup_case(False);c.hooks['post_api_request'](session_id='s');self.assertEqual(events,[])
 def test_nonboolean_not_consent(self):
  for value in ['true','false',1,{},[]]:
   with self.subTest(value=value):
    c,events=self.setup_case(value);c.hooks['post_api_request'](session_id='s');self.assertEqual(events,[])
 def test_true_records(self):
  c,events=self.setup_case(True)
  for cb in c.hooks.values():cb(session_id='s')
  self.assertEqual([kind for kind,kw in events],['post_api_request','api_request_error','post_tool_call'])
 def test_declared_hooks_always_registered(self):
  for value in [False,True]:
   c,events=self.setup_case(value);self.assertEqual(len(c.hooks),3)
 def test_setting_snapshot_not_mutated_mid_session(self):
  c,events=self.setup_case(False);c.value=True;c.hooks['post_api_request'](session_id='s');self.assertEqual(events,[])

if __name__=='__main__':unittest.main(verbosity=2)

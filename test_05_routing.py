import unittest,copy,json
from suite_tools import load,Context
class RoutingTests(unittest.TestCase):
 def setUp(self):self.p=load('local-first-routing');self.r=self.p.LocalFirst();self.cfg={'provider':'custom','model':'DeepSeek-V4.1-Flash-1017','base_url':'http://localhost:1234/v1','fallback_providers':[{'provider':'paid'}]}
 def test_pinned(self):
  r=self.r.route_task({},self.cfg);self.assertEqual(r['model'],self.p.MODEL);self.assertEqual(r['provider'],'custom');self.assertEqual(r['fallback_providers'],[])
 def test_no_mutation(self):
  before=copy.deepcopy(self.cfg);self.r.route_task({},self.cfg);self.assertEqual(self.cfg,before)
 def test_safety_refusal(self):
  with self.assertRaisesRegex(self.p.DelegationRouteError,'SAFETY_REFUSAL'):self.r.route_task({'prior_outcome':'refusal'},self.cfg)
 def test_infrastructure(self):
  for outcome in ('auth','quota','outage','timeout'):
   with self.subTest(outcome=outcome),self.assertRaisesRegex(self.p.DelegationRouteError,'INFRASTRUCTURE_BLOCKED'):self.r.route_task({'prior_outcome':outcome},self.cfg)
 def test_review_not_cloud(self):
  for task in ({'work_kind':'ambiguous'},{'prior_outcome':'failed'}):
   with self.assertRaisesRegex(self.p.DelegationRouteError,'MANUAL_REVIEW_REQUIRED'):self.r.route_task(task,self.cfg)
 def test_config_pin(self):
  for cfg in ({},{'provider':'openai-codex','model':'gpt-6-astra'},{'provider':'custom','model':'other'}):
   with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):self.r.route_task({},cfg)
 def test_no_reexecution(self):
  with self.assertRaisesRegex(self.p.DelegationRouteError,'ALREADY_VERIFIED'):self.r.route_task({'prior_outcome':'verified'},self.cfg)
 def test_invalid_state(self):
  with self.assertRaises(self.p.DelegationRouteError):self.r.route_task({'prior_outcome':'skip-safety'},self.cfg)
 def test_registered_provider(self):
  c=Context();self.p.register(c);self.assertEqual(c.providers[0].name,'local-first');policy=json.loads(c.tools['local_route_policy']['handler']({}))['data'];self.assertFalse(policy['automatic_fallback'])
if __name__=='__main__':unittest.main(verbosity=2)

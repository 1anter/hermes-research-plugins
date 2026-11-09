import unittest,copy,json
from suite_tools import load,Context
BASE={'provider':'custom','model':'DeepSeek-V4.1-Flash-1017','base_url':'http://localhost:1234/v1','fallback_providers':[{'provider':'paid'}]}
class SettingsPinTests(unittest.TestCase):
 def setUp(self):self.p=load('local-first-routing');self.r=self.p.LocalFirst()
 def cfg(self,pins=None,**route):
  c=copy.deepcopy(BASE);c.update(route)
  if pins is not None:c['backends']={'local-first':pins}
  return c
 def custom(self,pins=None,**route):
  pins={'approved_provider':'local-alt','approved_model':'llama-local-8b'} if pins is None else pins
  route.setdefault('provider','local-alt');route.setdefault('model','llama-local-8b')
  return self.cfg(pins,**route)
 def test_settings_read_from_backend_block(self):
  c=self.custom();self.assertEqual(dict(self.r.settings(c)),{'approved_provider':'local-alt','approved_model':'llama-local-8b'})
  self.assertEqual(dict(self.r.settings(self.cfg())),{})
  for bad in ('nope',['x'],None):
   c=copy.deepcopy(BASE);c['backends']=bad;self.assertEqual(dict(self.r.settings(c)),{})
   c=copy.deepcopy(BASE);c['backends']={'local-first':bad};self.assertEqual(dict(self.r.settings(c)),{})
 def test_custom_pins_route(self):
  r=self.r.route_task({},self.custom())
  self.assertEqual((r['provider'],r['model']),('local-alt','llama-local-8b'))
  self.assertEqual(r['fallback_providers'],[]);self.assertEqual(r['label'],'bounded-local')
  self.assertEqual(r['base_url'],BASE['base_url']);self.assertNotIn('backends',r)
 def test_custom_pins_override_defaults(self):
  c=self.custom(provider='custom',model=self.p.MODEL)
  with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):self.r.route_task({},c)
 def test_wrong_provider_or_model_refused(self):
  for route in ({'provider':'custom'},{'model':'gpt-6-astra'},{'provider':'custom','model':'other'},{'provider':'paid','model':'llama-local-8b'}):
   c=self.custom(**route)
   with self.subTest(route=route),self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):self.r.route_task({},c)
 def test_missing_route_pin_refused(self):
  c=self.custom();del c['model']
  with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):self.r.route_task({},c)
  c=self.custom();del c['provider']
  with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):self.r.route_task({},c)
 def test_malformed_pins_refused(self):
  bad=('', '   ',None,5,True,['x'],{'x':1},b'custom')
  for key in ('approved_provider','approved_model'):
   for value in bad:
    pins={'approved_provider':'local-alt','approved_model':'llama-local-8b'};pins[key]=value
    with self.subTest(key=key,value=value),self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_INVALID'):self.r.route_task({},self.custom(pins))
 def test_task_cannot_override_pins(self):
  c=self.custom()
  task={'goal':'x','provider':'paid','model':'gpt-6-astra','approved_provider':'paid','approved_model':'gpt-6-astra'}
  r=self.r.route_task(task,c);self.assertEqual((r['provider'],r['model']),('local-alt','llama-local-8b'))
  self.assertEqual(r['fallback_providers'],[])
  with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_MISMATCH'):
   self.r.route_task({'provider':'local-alt','model':'llama-local-8b'},self.custom(provider='custom',model=self.p.MODEL))
 def test_defaults_when_pins_absent(self):
  for c in (self.cfg(),self.cfg({}),copy.deepcopy(BASE)):
   r=self.r.route_task({},c);self.assertEqual((r['provider'],r['model']),(self.p.PROVIDER,self.p.MODEL))
  r=self.r.route_task({},self.cfg({'approved_provider':'local-alt'},provider='local-alt'))
  self.assertEqual((r['provider'],r['model']),('local-alt',self.p.MODEL))
 def test_partial_pin_defaults_only_for_absent_key(self):
  c=self.cfg({'approved_model':'llama-local-8b'},provider='custom',model='llama-local-8b')
  r=self.r.route_task({},c);self.assertEqual((r['provider'],r['model']),(self.p.PROVIDER,'llama-local-8b'))
  c=self.cfg({'approved_model':''},provider='custom',model='llama-local-8b')
  with self.assertRaisesRegex(self.p.DelegationRouteError,'PIN_INVALID'):self.r.route_task({},c)
 def test_no_mutation(self):
  for c in (self.cfg(),self.custom(),self.cfg({'approved_provider':'  '})):
   before=copy.deepcopy(c)
   try:self.r.route_task({},c)
   except self.p.DelegationRouteError:pass
   self.assertEqual(c,before)
  c=self.custom();before=copy.deepcopy(c);r=self.r.route_task({},c);r['provider']='paid';self.assertEqual(c,before)
 def test_refusal_categories_retained_with_custom_pins(self):
  c=self.custom()
  with self.assertRaisesRegex(self.p.DelegationRouteError,'SAFETY_REFUSAL'):self.r.route_task({'prior_outcome':'refusal'},c)
  for outcome in ('auth','quota','outage','timeout'):
   with self.subTest(outcome=outcome),self.assertRaisesRegex(self.p.DelegationRouteError,'INFRASTRUCTURE_BLOCKED'):self.r.route_task({'prior_outcome':outcome},c)
  with self.assertRaisesRegex(self.p.DelegationRouteError,'ALREADY_VERIFIED'):self.r.route_task({'prior_outcome':'verified'},c)
  for task in ({'prior_outcome':'failed'},{'work_kind':'ambiguous'}):
   with self.subTest(task=task),self.assertRaisesRegex(self.p.DelegationRouteError,'MANUAL_REVIEW_REQUIRED'):self.r.route_task(task,c)
  with self.assertRaises(self.p.DelegationRouteError):self.r.route_task({'prior_outcome':'skip-safety'},c)
  with self.assertRaises(self.p.DelegationRouteError):self.r.route_task({'work_kind':'other'},c)
 def test_policy_describes_settings_not_credentials(self):
  c=Context();self.p.register(c)
  policy=json.loads(c.tools['local_route_policy']['handler']({}))['data']
  self.assertEqual(policy['settings_location'],'delegation.backends.local-first')
  self.assertEqual(policy['pin_fields'],['approved_provider','approved_model'])
  self.assertEqual(policy['default_provider'],self.p.PROVIDER);self.assertEqual(policy['default_model'],self.p.MODEL)
  self.assertFalse(policy['automatic_fallback']);self.assertFalse(policy['reads_credentials'])
  self.assertNotIn('api_key',policy);self.assertNotIn('base_url',policy)
if __name__=='__main__':unittest.main(verbosity=2)

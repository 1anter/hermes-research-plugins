"""Local route selection only. Core owns child lifecycle and cancellation."""
from agent.delegation_provider import DelegationProvider,DelegationRouteError
from .common import register_tools
NAME='local-first-routing';MODEL='DeepSeek-V4.1-Flash-1017';PROVIDER='custom'
SETTINGS_KEY='delegation.backends.local-first';PIN_KEYS=('approved_provider','approved_model')
class LocalFirst(DelegationProvider):
 @property
 def name(self):return 'local-first'
 def _pins(self,config):
  settings=self.settings(config)
  provider=settings.get('approved_provider',PROVIDER);model=settings.get('approved_model',MODEL)
  if not isinstance(provider,str) or not isinstance(model,str) or not provider.strip() or not model.strip():
   raise DelegationRouteError('PIN_INVALID: '+SETTINGS_KEY+'.approved_provider and approved_model must be nonblank strings; no fallback.')
  return provider,model
 def task_parameters(self,config):
  return {'work_kind':{'type':'string','enum':['bounded','ambiguous'],'description':'Only bounded work executes locally; ambiguous work requires manual planner review.'},'prior_outcome':{'type':'string','enum':['new','verified','failed','refusal','auth','quota','outage','timeout'],'description':'Declare prior outcome; failures require explicit review, not an automatic retry or provider switch.'}}
 def description(self,config):return 'Pinned local bounded execution. Approved pins come from '+SETTINGS_KEY+'; no cloud fallback. Escalations are returned as route refusals for manual review; this does not enforce deadlines.'
 def route_task(self,task,config):
  outcome=task.get('prior_outcome','new');kind=task.get('work_kind','bounded')
  if kind not in ('bounded','ambiguous') or outcome not in ('new','verified','failed','refusal','auth','quota','outage','timeout'):raise DelegationRouteError('Invalid declared route state.')
  if outcome=='refusal':raise DelegationRouteError('SAFETY_REFUSAL: no retry or alternate provider permitted.')
  if outcome in ('auth','quota','outage','timeout'):raise DelegationRouteError('INFRASTRUCTURE_BLOCKED: resolve the original condition; no fallback. Timeout is not proof of cancellation.')
  if outcome=='verified':raise DelegationRouteError('ALREADY_VERIFIED: do not rerun completed work.')
  if outcome=='failed' or kind=='ambiguous':raise DelegationRouteError('MANUAL_REVIEW_REQUIRED: preserve inputs and failure artifacts. No automatic cloud call.')
  provider,model=self._pins(config)
  if config.get('provider')!=provider or config.get('model')!=model:raise DelegationRouteError('PIN_MISMATCH: configure the approved local provider and model explicitly in '+SETTINGS_KEY+'.')
  route={k:config[k] for k in ('base_url','api_key','api_mode') if config.get(k)}
  route.update({'provider':provider,'model':model,'fallback_providers':[],'reasoning_effort':config.get('reasoning_effort','none'),'label':'bounded-local'})
  return route
DEFS={'local_route_policy':('Inspect the pinned routing policy without network requests or credentials.',{},[])}
def handle(name,a,**kw):return {'settings_location':SETTINGS_KEY,'pin_fields':list(PIN_KEYS),'default_provider':PROVIDER,'default_model':MODEL,'pin_source':'pins are read from config at '+SETTINGS_KEY+'; defaults apply only when a pin key is absent','automatic_fallback':False,'escalation':'manual_review_only','scope':'route selection; caller-declared outcome is not an authorization or retry-limit boundary','activation':'delegation.backend: local-first (not applied by this tool)','reads_credentials':False}
def register(ctx):register_tools(ctx,DEFS,handle);ctx.register_delegation_provider(LocalFirst())

"""Immutable local event/artifact ledger. No raw prompts, results or secrets in observers."""
import sqlite3,json,uuid,math
from .common import canonical,digest,now,data_dir,register_tools,TEXT,ID
NAME='evaluation-ledger'
def _db_path():return data_dir(NAME)/'ledger.sqlite'
from contextlib import contextmanager
@contextmanager
def db():
 c=sqlite3.connect(_db_path(),timeout=10);c.row_factory=sqlite3.Row
 try:
  c.executescript('CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, session TEXT, kind TEXT, payload TEXT NOT NULL); CREATE TABLE IF NOT EXISTS artifacts(run TEXT,id TEXT,content TEXT NOT NULL,hash TEXT NOT NULL,PRIMARY KEY(run,id));')
  with c:yield c
 finally:c.close()
def append(event_id,session,kind,payload):
 value=canonical(payload)
 with db() as c:
  old=c.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
  if old:
   if (old['session'],old['kind'],old['payload'])!=(session,kind,value):raise ValueError('conflicting event')
   return False
  c.execute('INSERT INTO events VALUES(?,?,?,?)',(event_id,session,kind,value));return True

def category(status_code=None,reason='',status=''):
 if reason in ('safety_refusal','content_filter','refused') or status=='blocked':return 'refusal'
 if status=='cancelled':return 'cancelled'
 if status_code in (401,403):return 'auth'
 if status_code==429:return 'quota'
 if status_code is not None and type(status_code) is int and status_code>=500:return 'outage'
 if reason in ('timeout','TimeoutError'):return 'timeout_cancellation_unconfirmed'
 return 'task_failure' if status=='error' else 'unknown'

def observe(kind,**kw):
 # Strict field allowlist: never retain request, response, args, error text or result.
 fields=('session_id','task_id','turn_id','api_request_id','tool_call_id','model','provider','response_model','tool_name','status','status_code','api_call_count','retry_count')
 payload={k:kw[k] for k in fields if type(kw.get(k)) in (str,int) and len(str(kw[k]))<=256}
 usage=kw.get('usage')
 payload['usage']={k:v for k,v in (usage.items() if isinstance(usage,dict) else []) if k in ('input_tokens','output_tokens','prompt_tokens','completion_tokens','cache_read_tokens','cache_write_tokens','reasoning_tokens','total_tokens') and type(v) is int and v>=0}
 payload['usage_available']=bool(payload['usage'])
 if kind=='api_request_error':payload['category']=category(kw.get('status_code'),kw.get('reason',''),'error')
 if kind=='post_tool_call':payload['category']='success' if kw.get('status')=='ok' else category(status=kw.get('status',''))
 session=str(kw.get('session_id') or 'unknown')
 correlation=kw.get('api_request_id') if kind!='post_tool_call' else kw.get('tool_call_id')
 payload['correlation_available']=bool(correlation)
 key=digest(canonical([kind,session,correlation])) if correlation else uuid.uuid4().hex
 return append(key,session,kind,payload)

def report(sessions):
 totals={};events=[]
 with db() as c:
  for session in sorted(set(sessions)):
   for row in c.execute('SELECT kind,payload FROM events WHERE session=? ORDER BY id',(session,)):
    p=json.loads(row['payload']);events.append({'kind':row['kind'],**p})
    if row['kind']=='post_api_request':
     key=str(p.get('provider','unknown'))+'/'+str(p.get('model','unknown'));group=totals.setdefault(key,{'calls':0,'missing_usage_calls':0,'fields':{}});group['calls']+=1
     if not p.get('usage_available'):group['missing_usage_calls']+=1
     for k,v in p.get('usage',{}).items():group['fields'][k]=group['fields'].get(k,0)+v
 return {'sessions':sorted(set(sessions)),'events':events,'usage_by_route':totals,'usage_semantics':'Reported fields summed separately; do not add cached/reasoning/total fields together. Unknown usage is not zero.','coverage':'Observer callbacks are best-effort. Include child session IDs explicitly. No claim of complete billing.'}

DEFS={
'evaluation_artifact':('Save immutable task-owned artifact text for deterministic checks.',{'run_id':ID,'artifact_id':ID,'content':TEXT},['run_id','artifact_id','content']),
'evaluation_check':('Compare saved artifact bytes to a supplied SHA-256 and optional exact JSON value. Does not prove source truth or scorer independence.',{'run_id':ID,'artifact_id':ID,'expected_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'expected_json':{}},['run_id','artifact_id','expected_sha256']),
'evaluation_report':('Read observed events and usage for explicit parent/child session IDs. No inferred monetary cost.',{'session_ids':{'type':'array','items':ID,'minItems':1,'maxItems':100}},['session_ids'])}
def handle(name,a,**kw):
 if name=='evaluation_report':return report(a['session_ids'])
 with db() as c:
  old=c.execute('SELECT content,hash FROM artifacts WHERE run=? AND id=?',(a['run_id'],a['artifact_id'])).fetchone()
  if name=='evaluation_artifact':
   h=digest(a['content'])
   if old and old['content']!=a['content']:raise ValueError('immutable artifact conflict')
   if not old:c.execute('INSERT INTO artifacts VALUES(?,?,?,?)',(a['run_id'],a['artifact_id'],a['content'],h))
   return {'sha256':h,'inserted':not bool(old)}
  if old is None:raise ValueError('unknown artifact')
  checks={'hash_matches':old['hash']==a['expected_sha256'],'stored_hash_valid':digest(old['content'])==old['hash']}
  if 'expected_json' in a:
   try:checks['exact_json_matches']=canonical(json.loads(old['content']))==canonical(a['expected_json'])
   except ValueError:checks['exact_json_matches']=False
 result={'checks':checks,'passed':all(checks.values()),'scope':'supplied artifact and acceptance specification only'}
 append(uuid.uuid4().hex,a['run_id'],'artifact_check',result);return result

def register(ctx):
 register_tools(ctx,DEFS,handle)
 # Collection is explicitly opt-in; only boolean True is consent. Snapshot at
 # registration so changing a setting cannot silently change an active session.
 enabled=ctx.get_config('observe_usage',False) is True
 for kind in ('post_api_request','api_request_error','post_tool_call'):
  def callback(_kind=kind,**kwargs):
   if enabled:return observe(_kind,**kwargs)
  ctx.register_hook(kind,callback)

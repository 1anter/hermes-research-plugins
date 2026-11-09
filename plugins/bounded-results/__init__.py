"""Transforms only a fixed research-tool allowlist. Not a safety guard or redactor."""
import json,sqlite3
from .common import canonical,digest,data_dir,register_tools,TEXT
NAME='bounded-results';LIMIT=4096;MAX_STORE=8000000
ALLOW={'evidence_history','evidence_compare','evidence_as_of','evidence_verify_support','evaluation_report','memory_search'}
def _db_path():return data_dir(NAME)/'results.sqlite'
def store(text):
 h=digest(text);c=sqlite3.connect(_db_path(),timeout=10)
 try:
  with c:
   c.execute('CREATE TABLE IF NOT EXISTS results(hash TEXT PRIMARY KEY,text TEXT NOT NULL)')
   c.execute('INSERT OR IGNORE INTO results VALUES(?,?)',(h,text))
 finally:c.close()
 return h

def bound(tool_name,result,**kw):
 if tool_name not in ALLOW or not isinstance(result,str) or len(result.encode('utf-8'))<=LIMIT:return None
 if len(result.encode('utf-8'))>MAX_STORE:return None # Explicit host fail-open policy; not universal size enforcement.
 h=store(result)
 status={'upstream_status':'unclassified','upstream_error':None}
 try:
  parsed=json.loads(result)
  if isinstance(parsed,dict):
   status['upstream_status']='error' if parsed.get('ok') is False or 'error' in parsed else 'not_marked_error'
   error=parsed.get('error');status['upstream_error']=str(error)[:200] if error is not None else None
 except ValueError:pass
 envelope={'truncated':True,'handle':h,'sha256':h,'original_bytes':len(result.encode('utf-8')),'original_characters':len(result),'offset_unit':'unicode_code_points','next_action':'Use bounded_read to retrieve further chunks before concluding absence of evidence.','preview':'',**status}
 # Bound the serialized envelope, not just its preview. Unicode is never split.
 lo,hi=0,min(len(result),LIMIT)
 while lo<hi:
  mid=(lo+hi+1)//2;envelope['preview']=result[:mid]
  if len(canonical(envelope).encode('utf-8'))<=LIMIT:lo=mid
  else:hi=mid-1
 envelope['preview']=result[:lo]
 return canonical(envelope)
DEFS={'bounded_read':('Retrieve an exact chunk of a stored full tool result. Handle is a content hash, not a path. Offsets count Unicode code points; next_offset=null means complete.',{'handle':{'type':'string','pattern':'^[0-9a-f]{64}$'},'offset':{'type':'integer','minimum':0},'max_characters':{'type':'integer','minimum':1,'maximum':4096}},['handle'])}
def handle(name,a,**kw):
 c=sqlite3.connect(_db_path(),timeout=10)
 try:row=c.execute('SELECT text FROM results WHERE hash=?',(a['handle'],)).fetchone()
 finally:c.close()
 if row is None:raise ValueError('unknown handle')
 text=row[0]
 if digest(text)!=a['handle']:raise ValueError('corrupt result')
 offset=a.get('offset',0);size=a.get('max_characters',1024)
 if offset>len(text):raise ValueError('offset beyond result')
 chunk=text[offset:offset+size];end=offset+len(chunk)
 return {'text':chunk,'offset':offset,'next_offset':end if end<len(text) else None,'total_characters':len(text),'sha256':a['handle'],'offset_unit':'unicode_code_points'}
def register(ctx):
 register_tools(ctx,DEFS,handle);ctx.register_hook('transform_tool_result',bound)

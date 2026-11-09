"""Review-only candidate state machine. Never executes or promotes submitted code."""
import ast,json,re,sqlite3,pathlib,difflib
from contextlib import contextmanager
from .common import canonical,digest,data_dir,register_tools,TEXT,ID
NAME='component-workbench';SHA={'type':'string','pattern':'^[0-9a-f]{64}$'}
def _db_path():return data_dir(NAME)/'workbench.sqlite'
@contextmanager
def db():
 c=sqlite3.connect(_db_path(),timeout=10);c.row_factory=sqlite3.Row
 try:
  c.executescript('CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, author TEXT NOT NULL, files TEXT NOT NULL, hash TEXT NOT NULL, state TEXT NOT NULL, spec_hash TEXT); CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY AUTOINCREMENT, candidate TEXT NOT NULL, payload TEXT NOT NULL);')
  with c:yield c
 finally:c.close()
def valid_files(files):
 if not isinstance(files,dict) or not 1<=len(files)<=32:raise ValueError('invalid file count')
 for name,text in files.items():
  parts=name.split('/')
  if any(not re.fullmatch(r'[A-Za-z0-9_.-]+',p) or p in ('.','..') for p in parts) or '\\' in name or ':' in name:raise ValueError('unsafe relative filename')
  if parts[-1] in ('.env','auth.json') or not isinstance(text,str):raise ValueError('secret store or nontext not allowed')
  if pathlib.PurePosixPath(name).suffix not in ('.py','.json','.yaml','.yml','.md','.txt'):raise ValueError('unsupported source type')
 if len(canonical(files).encode('utf-8'))>8000000:raise ValueError('candidate too large')
 return files
def inspect_files(files):
 checks=[]
 for name,text in sorted(files.items()):
  try:
   if name.endswith('.py'):ast.parse(text,filename=name)
   elif name.endswith('.json'):canonical(json.loads(text))
   elif name.endswith(('.yaml','.yml')):
    import yaml
    yaml.safe_load(text)
   checks.append({'file':name,'passed':True})
  except Exception as exc:checks.append({'file':name,'passed':False,'error':type(exc).__name__})
 return {'passed':bool(checks) and all(c['passed'] for c in checks),'checks':checks,'scope':'Syntax/data parsing only, not code execution or semantic correctness.'}
def get(c,id):
 row=c.execute('SELECT * FROM candidates WHERE id=?',(id,)).fetchone()
 if row is None:raise ValueError('unknown candidate')
 if digest(row['files'])!=row['hash']:raise ValueError('candidate hash mismatch')
 return row
DEFS={
'workbench_propose':('Save an immutable candidate file map. No code is executed or installed.',{'candidate_id':ID,'author_id':ID,'files':{'type':'object','minProperties':1,'maxProperties':32,'additionalProperties':{'type':'string','maxLength':1000000}}},['candidate_id','author_id','files']),
'workbench_validate':('Run actual Python AST / JSON / safe YAML parsing checks. This is only static development validation.',{'candidate_id':ID},['candidate_id']),
'workbench_freeze':('Freeze a syntax-valid candidate and commit a SHA-256 of an externally prepared evaluation specification. Freeze does not reveal the specification.',{'candidate_id':ID,'evaluation_spec_sha256':SHA},['candidate_id','evaluation_spec_sha256']),
'workbench_review':('Compare supplied actual outputs to a previously committed evaluation spec. Stores a review, never promotes code. Verifier identity and output execution provenance are caller attestations, not authenticated.',{'candidate_id':ID,'candidate_sha256':SHA,'verifier_id':ID,'evaluation_spec':{'type':'object','minProperties':1},'actual_results':{'type':'object'},'execution_artifact_sha256':SHA},['candidate_id','candidate_sha256','verifier_id','evaluation_spec','actual_results','execution_artifact_sha256']),
'workbench_status':('Inspect candidate state and all recorded reviews, including failures. No live activation or promotion tool exists.',{'candidate_id':ID},['candidate_id']),
'workbench_diff':('Show a unified diff between two stored immutable candidates.',{'before_id':ID,'after_id':ID},['before_id','after_id'])}
def handle(name,a,**kw):
 with db() as c:
  if name=='workbench_propose':
   text=canonical(valid_files(a['files']));h=digest(text)
   prior=c.execute('SELECT * FROM candidates WHERE id=?',(a['candidate_id'],)).fetchone()
   if prior:
    if prior['hash']!=h or prior['author']!=a['author_id']:raise ValueError('immutable candidate conflict')
    return {'candidate_sha256':h,'state':prior['state'],'inserted':False}
   c.execute('INSERT INTO candidates VALUES(?,?,?,?,?,NULL)',(a['candidate_id'],a['author_id'],text,h,'proposed'));return {'candidate_sha256':h,'state':'proposed','inserted':True}
  if name=='workbench_diff':
   b=json.loads(get(c,a['before_id'])['files']);n=json.loads(get(c,a['after_id'])['files']);parts=[]
   for file in sorted(set(b)|set(n)):parts.extend(difflib.unified_diff(b.get(file,'').splitlines(True),n.get(file,'').splitlines(True),fromfile='before/'+file,tofile='after/'+file))
   return {'diff':''.join(parts)}
  row=get(c,a['candidate_id']);files=json.loads(row['files'])
  if name=='workbench_validate':
   result=inspect_files(files)
   if row['state'] in ('proposed','validated'):c.execute('UPDATE candidates SET state=? WHERE id=?',('validated' if result['passed'] else 'proposed',a['candidate_id']))
   return result
  if name=='workbench_freeze':
   if row['state']!='validated':raise ValueError('must pass development validation before freezing')
   if not inspect_files(files)['passed']:raise ValueError('development checks failed')
   c.execute('UPDATE candidates SET state=?,spec_hash=? WHERE id=?',('frozen',a['evaluation_spec_sha256'],a['candidate_id']));return {'candidate_sha256':row['hash'],'state':'frozen','evaluation_spec_sha256':a['evaluation_spec_sha256']}
  if name=='workbench_review':
   if row['state'] not in ('frozen','review_ready','review_failed'):raise ValueError('candidate not frozen')
   if a['candidate_sha256']!=row['hash'] or digest(canonical(a['evaluation_spec']))!=row['spec_hash']:raise ValueError('freeze/spec mismatch')
   if a['verifier_id']==row['author']:raise ValueError('separate verifier label required')
   matches=canonical(a['evaluation_spec'])==canonical(a['actual_results'])
   review={'passed_against_committed_spec':matches,'verifier_id':a['verifier_id'],'candidate_sha256':row['hash'],'evaluation_spec_sha256':row['spec_hash'],'execution_artifact_sha256':a['execution_artifact_sha256'],'execution_provenance':'caller_attested_not_authenticated','promotion':'not_performed_requires_external_human_review'}
   c.execute('INSERT INTO reviews(candidate,payload) VALUES(?,?)',(a['candidate_id'],canonical(review)))
   c.execute('UPDATE candidates SET state=? WHERE id=?',('review_ready' if matches else 'review_failed',a['candidate_id']));return review
  return {'candidate_sha256':row['hash'],'state':row['state'],'evaluation_spec_sha256':row['spec_hash'],'files':sorted(files),'reviews':[json.loads(r[0]) for r in c.execute('SELECT payload FROM reviews WHERE candidate=? ORDER BY id',(a['candidate_id'],))],'promotion':'No model-callable promotion or live-write operation.'}
def register(ctx):register_tools(ctx,DEFS,handle)

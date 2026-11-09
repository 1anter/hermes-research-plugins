"""Native Hermes adapter. No network, subprocesses, credentials, or model calls.
Source passages are untrusted data. Temporal modes are not interchangeable.
"""
import datetime as dt
import json
from urllib.parse import urlsplit
from .evidence_store import EvidenceStore, timestamp

NAME='evidence-history'
COMMON={'claim_key':{'type':'string','description':'Stable identity of the claim, e.g. company:metric.'}}
MODE={'type':'string','enum':['known_to_system','published_by'],'description':'known_to_system filters both publication and actual capture time; published_by is retrospective and does not prove historical possession.'}
DEFINITIONS={
'evidence_capture':('Save a user-provided source passage verbatim. Does NOT fetch or verify the URL. Observation time is stamped by this tool and cannot be backdated. Same ID/content is idempotent; a revision needs a new ID.',{**COMMON,'evidence_id':{'type':'string'},'source_url':{'type':'string'},'passage':{'type':'string'},'published_at':{'type':'string','description':'Timezone-aware ISO timestamp; caller-supplied publication metadata.'},'value':{'description':'Optional structured claim value; not independently verified.','type':['object','array','string','number','boolean','null']}},['claim_key','evidence_id','source_url','passage','published_at']),
'evidence_as_of':('Retrieve the latest eligible publication with exact passage and source. Missing evidence returns null, not a fabricated answer.',{**COMMON,'cutoff':{'type':'string'},'mode':MODE},['claim_key','cutoff']),
'evidence_history':('List every captured revision for a claim, preserving source passages and timestamps.',COMMON,['claim_key']),
'evidence_compare':('Compare selected evidence at two cutoffs. changed means selected evidence identity changed, NOT a proven semantic contradiction.',{**COMMON,'earlier':{'type':'string'},'later':{'type':'string'},'mode':MODE},['claim_key','earlier','later'])}

DEFINITIONS['evidence_verify_support']=(
    'Check source identity, selected revision, exact quote, timestamp eligibility and optional structured value. Never establishes semantic entailment or authenticates the source.',
    {**COMMON,'evidence_id':{'type':'string'},'cutoff':{'type':'string'},'quote':{'type':'string'},'expected_value':{'type':['object','array','string','number','boolean','null']}},
    ['claim_key','evidence_id','cutoff','quote'])

def verify_support(store,args):
    selected=store.query_as_of(args['claim_key'],args['cutoff'],mode='known_to_system')
    checks={'eligible_evidence':selected is not None,
            'selected_revision':bool(selected and selected['evidence_id']==args['evidence_id']),
            'verbatim_quote':bool(selected and args['quote'] in selected['passage'])}
    if 'expected_value' in args:
        canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
        checks['structured_value_matches']=bool(selected and canonical(args['expected_value'])==canonical(selected['value']))
    return {'structural_checks_passed':all(checks.values()),'checks':checks,'semantic_verdict':'not_assessed',
            'semantic_review_required':True,'source_authenticity':'not_verified',
            'evidence':selected,'failed_checks':[k for k,v in checks.items() if not v]}

def _db_path():
    from plugins.plugin_storage import plugin_data_dir
    return plugin_data_dir(NAME)/'evidence.sqlite'

def handle(name,args,**kwargs):
    store=None
    try:
        if name not in DEFINITIONS:raise ValueError('unknown evidence operation')
        _,props,required=DEFINITIONS[name]
        if not isinstance(args,dict) or set(args)-set(props) or any(k not in args for k in required):raise ValueError('missing or unsupported arguments')
        for key in props:
            if key in args and key not in ('value','expected_value') and (not isinstance(args[key],str) or not args[key].strip()):raise ValueError(key+' must be nonempty text')
        if name=='evidence_capture':
            u=urlsplit(args['source_url'])
            if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:raise ValueError('source_url must be an HTTP(S) URL without credentials')
            published=timestamp(args['published_at'])
            # Validate arbitrary JSON values before any state change.
            json.dumps(args.get('value'),allow_nan=False,sort_keys=True)
        store=EvidenceStore(_db_path())
        if name=='evidence_verify_support':
            return json.dumps({'ok':True,'data':verify_support(store,args)},ensure_ascii=False,allow_nan=False)
        if name=='evidence_capture':
            observed=dt.datetime.now(dt.timezone.utc).isoformat()
            existing=next((r for r in store.history(args['claim_key']) if r['evidence_id']==args['evidence_id']),None)
            if existing is not None:observed=existing['observed_at']
            data=store.ingest(**args,observed_at=observed)
            return json.dumps({'ok':True,'data':data,'provenance':'User-supplied passage/publication metadata; URL not fetched or authenticated.'},ensure_ascii=False,allow_nan=False)
        if name=='evidence_history':data=store.history(args['claim_key'])
        elif name=='evidence_as_of':data=store.query_as_of(**args)
        else:data=store.compare(**args)
        return json.dumps({'ok':True,'data':data,'temporal_mode':args.get('mode','known_to_system')},ensure_ascii=False,allow_nan=False)
    except Exception as exc:
        return json.dumps({'ok':False,'error':type(exc).__name__,'message':str(exc)},ensure_ascii=False)
    finally:
        if store is not None:store.close()

def register(ctx):
    for name,(description,properties,required) in DEFINITIONS.items():
        schema={'name':name,'description':description,'parameters':{'type':'object','properties':properties,'required':required,'additionalProperties':False}}
        def handler(args,_name=name,**kwargs):
            return handle(_name,args,**kwargs)
        ctx.register_tool(name=name,toolset='evidence_history',schema=schema,handler=handler,check_fn=lambda:True)

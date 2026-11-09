"""Small schema-checked native tool registration helper (bundled per plugin)."""
import json,hashlib,datetime as dt,math
import jsonschema
TEXT={'type':'string','minLength':1,'maxLength':1000000}
ID={'type':'string','pattern':'^[A-Za-z0-9_.:-]{1,128}$'}
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def timestamp(s):
 t=dt.datetime.fromisoformat(s.replace('Z','+00:00'))
 if t.tzinfo is None or t.utcoffset() is None:raise ValueError('timezone required')
 return t.astimezone(dt.timezone.utc).isoformat(timespec='microseconds')
def data_dir(name):
 from plugins.plugin_storage import plugin_data_dir
 return plugin_data_dir(name)
def register_tools(ctx,definitions,handler):
 for name,(description,props,required) in definitions.items():
  params={'type':'object','properties':props,'required':required,'additionalProperties':False}
  def wrapped(args,_name=name,_schema=params,**kwargs):
   try:
    canonical(args);jsonschema.validate(args,_schema);return canonical({'ok':True,'data':handler(_name,args,**kwargs)})
   except Exception as exc:return canonical({'ok':False,'error':type(exc).__name__,'message':'Operation rejected or failed; success is not asserted.'})
  ctx.register_tool(name=name,toolset=name.split('_')[0],schema={'name':name,'description':description,'parameters':params},handler=wrapped,check_fn=lambda:True)

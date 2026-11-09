"""Build/test helpers, never installed into the active profile."""
import importlib.util,json,pathlib,sys,subprocess,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
PLUGINS=ROOT/'plugins'
def load(name):
    module_name='suite_'+name.replace('-','_')
    spec=importlib.util.spec_from_file_location(module_name,PLUGINS/name/'__init__.py',submodule_search_locations=[str(PLUGINS/name)])
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec);sys.modules[module_name]=module;spec.loader.exec_module(module);return module
class Context:
    def __init__(self):self.tools={};self.hooks={};self.engines=[];self.providers=[]
    def register_tool(self,**kwargs):
        assert kwargs['name'] not in self.tools
        self.tools[kwargs['name']]=kwargs
    def get_config(self,key,default=None):return default
    def register_hook(self,name,callback):self.hooks[name]=callback
    def register_context_engine(self,engine):self.engines.append(engine)
    def register_delegation_provider(self,provider):self.providers.append(provider)
def doctor(name):
    results=[]
    for args in [['doctor',str(PLUGINS/name),'--ci'],['validate',str(PLUGINS/name),'--json']]:
        p=subprocess.run(['hermes','plugins',*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        results.append({'command':['hermes','plugins',*args],'exit_code':p.returncode,'output':p.stdout+p.stderr})
    (ROOT/'checks').mkdir(exist_ok=True)
    (ROOT/'checks'/(name+'-native.json')).write_text(json.dumps(results,indent=2),encoding='utf-8')
    assert all(r['exit_code']==0 for r in results),results
    return results
if __name__=='__main__':
    print(json.dumps(doctor(sys.argv[1]),indent=2))

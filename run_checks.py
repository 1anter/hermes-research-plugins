"""Reproducible checks; never installs/enables plugins or makes model calls."""
import argparse,hashlib,io,json,pathlib,subprocess,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('--skip-native',action='store_true');a=p.parse_args()
 checks=ROOT/'checks';checks.mkdir(exist_ok=True);out=io.StringIO()
 result=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.TestLoader().discover(str(ROOT),pattern='test_*.py'))
 (checks/'tests.txt').write_text(out.getvalue(),encoding='utf-8');rows=[]
 if not a.skip_native:
  for folder in sorted((ROOT/'plugins').iterdir()):
   for operation,args in [('doctor',['--ci']),('validate',['--json'])]:
    proc=subprocess.run(['hermes','plugins',operation,str(folder),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    (checks/(folder.name+'-'+operation+'.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
    row={'plugin':folder.name,'operation':operation,'exit_code':proc.returncode}
    if operation=='validate' and proc.returncode==0:
     try:row['warnings']=json.loads(proc.stdout).get('warnings',[])
     except ValueError:row['parse_error']=True
    rows.append(row)
 summary={'passed':result.wasSuccessful() and all(x['exit_code']==0 and not x.get('parse_error') for x in rows),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'native':rows,'native_skipped':a.skip_native,'independent_certification':False,'inference_calls':0}
 (checks/'acceptance.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2));return 0 if summary['passed'] else 1
if __name__=='__main__':sys.exit(main())

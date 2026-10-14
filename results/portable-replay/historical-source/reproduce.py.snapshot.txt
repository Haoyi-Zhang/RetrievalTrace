#!/usr/bin/env python3
"""Serial bounded reproduction; semantic outputs compared independently of time."""
from __future__ import annotations
import argparse,json,os,pathlib,subprocess,sys,time
try:
    import resource
except ImportError:
    resource=None  # Certificate checks and runner regressions also run on Windows.
ROOT=pathlib.Path(__file__).resolve().parent
GROUPS={'core':[('tests',),('optimized-tests',),('examples',),('supports',)],
        'relational': [('grid',str(i)) for i in range(4)],
        'cutoff':[('cutoff',),('larger',)],
        'graphs':[('graphs',),('scaling',)]}

RAW={'grid':['grid-{i}.csv'],'cutoff':['uniform-cutoffs.csv'],'graphs':['graph-pairs.csv','graph-inputs.json'],
     'larger':['larger-cases.json'],'scaling':['encoding-scaling.csv','binary-horizons.json','worst-cost-branches.json'],
     'examples':['examples/*.json','observation-erasure.json']}

def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k!='measurement'}
    if isinstance(x,list):return [clean(v) for v in x]
    return x

def limits():
    if resource is None:
        raise RuntimeError('bounded runner requires POSIX resource limits')
    resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(2700,2700))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def run(group,out,compare):
    out.mkdir(parents=True,exist_ok=True)
    if group=='cutoff' and any(not (out/f'grid-{i}.csv').exists() for i in range(4)):
        run('relational',out,compare)
    records=[]
    for task in GROUPS[group]:
        name=task[0]
        if name in ('tests','optimized-tests'):
            command=[sys.executable]+(['-O'] if name=='optimized-tests' else [])+['-m','unittest','discover','-s','tests','-v']
            result_file=None
        else:
            command=[sys.executable,'experiments/campaign.py',name,'--out',str(out)]
            if name=='grid':command+=['--initial',task[1]]
            result_file=out/(('grid-'+task[1] if name=='grid' else name)+'.json')
        before=resource.getrusage(resource.RUSAGE_CHILDREN);start=time.monotonic()
        env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONHASHSEED='0',PYTHONDONTWRITEBYTECODE='1')
        timed_out=False
        try:
            result=subprocess.run(command,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                  preexec_fn=limits,timeout=2700)
        except subprocess.TimeoutExpired as error:
            # TimeoutExpired.output may be bytes even with text=True. Preserve
            # all captured output and record failure before propagating the gate.
            output=error.output or ''
            if isinstance(output,bytes):output=output.decode('utf8',errors='replace')
            result=subprocess.CompletedProcess(command,124,stdout=output)
            timed_out=True
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        ident='-'.join(task);(out/(ident+'.log')).write_text(result.stdout,encoding='utf8')
        record=dict(task=ident,command=['python' if a==sys.executable else a for a in command],
                    exit_code=result.returncode,wall_seconds=time.monotonic()-start,
                    child_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                    cumulative_child_peak_rss_kib=after.ru_maxrss)
        if timed_out:record['timed_out']=True
        # The per-task peak is measured within the task JSON. RUSAGE_CHILDREN
        # ru_maxrss above is a cumulative maximum, not the new child's own peak.
        records.append(record)
        (out/('execution-'+group+'.json')).write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
        if result.returncode:raise RuntimeError(f'{ident} failed; see {ident}.log')
        if result_file:
            current=json.loads(result_file.read_text(encoding='utf8'));
            if current.get('mismatches'):raise RuntimeError(f'{ident} has semantic mismatches')
            reference=ROOT/'results/current'/result_file.name
            if compare and reference.resolve()!=result_file.resolve():
                if not reference.exists():raise RuntimeError(f'missing retained reference {reference.name}')
                if clean(current)!=clean(json.loads(reference.read_text(encoding='utf8'))):raise RuntimeError(f'{ident} differs from retained semantic results')
                for pattern in RAW.get(name,[]):
                    pattern=pattern.format(i=task[1] if name=='grid' else '')
                    actuals=sorted(out.glob(pattern));expected=sorted((ROOT/'results/current').glob(pattern))
                    if [p.relative_to(out) for p in actuals]!=[p.relative_to(ROOT/'results/current') for p in expected]:raise RuntimeError(f'{ident} raw output set differs')
                    for actual,golden in zip(actuals,expected):
                        if actual.read_bytes()!=golden.read_bytes():raise RuntimeError(f'{ident} raw output differs: {actual.name}')
        print(json.dumps(dict(group=group,task=ident,status='passed',child_cpu_seconds=record['child_cpu_seconds'])),flush=True)
    return records

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--group',choices=[*GROUPS,'all'],default='all');p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--record',action='store_true',help='record initial reference campaign instead of comparing existing semantic outputs');a=p.parse_args()
    if os.name!='posix' or resource is None:p.error('bounded runner requires POSIX resource limits')
    out=a.out.resolve(); groups=list(GROUPS) if a.group=='all' else [a.group]
    for group in groups:run(group,out,not a.record)
    records=[]
    for group in GROUPS:
        file=out/('execution-'+group+'.json')
        if file.exists():records.extend(json.loads(file.read_text(encoding='utf8')))
    summary=dict(completed_commands=len(records),all_recorded_commands_successful=all(r['exit_code']==0 for r in records),
                 child_cpu_seconds=sum(r['child_cpu_seconds'] for r in records),
                 cumulative_child_peak_rss_kib=max((r['cumulative_child_peak_rss_kib'] for r in records),default=0))
    (out/'execution-summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (RuntimeError,OSError,subprocess.TimeoutExpired) as error: print(str(error),file=sys.stderr);sys.exit(1)

"""Reconcile every retained study row and paired cost; render nothing."""
import argparse,csv,hashlib,json,pathlib,statistics

def main():
    p=argparse.ArgumentParser();p.add_argument('directory',type=pathlib.Path);a=p.parse_args();d=a.directory
    summary=json.loads((d/'summary.json').read_text());cases=[json.loads(s) for s in (d/'cases.jsonl').read_text().splitlines()]
    if len(cases)!=summary['contracts'] or sum(len(c['results']) for c in cases)!=summary['decisions']:raise ValueError('case census')
    results={(c['case'],r['cutoff']):r for c in cases for r in c['results']}
    for r in results.values():
        if (r['status']=='valid')!=r['oracle']:raise ValueError('retained decision mismatch')
    for name,binding in summary['files'].items():
        data=(d/name).read_bytes()
        if len(data)!=binding['bytes'] or hashlib.sha256(data).hexdigest()!=binding['sha256']:raise ValueError('raw binding '+name)
    checks=0
    with (d/'world-checks.csv').open(newline='') as stream:
        for r in csv.DictReader(stream):
            if r['cost_relation']!=r['adjacent_relation']:raise ValueError('pointwise adjacency')
            if (int(r['case']),int(r['cutoff'])) not in results:raise ValueError('world case foreign key')
            checks+=1
    if checks!=summary['world_decision_checks']:raise ValueError('world census')
    with (d/'costs.csv').open(newline='') as stream:rows=list(csv.DictReader(stream))
    pairs={}
    for r in rows:
        key=(int(r['case']),int(r['cutoff']));pairs.setdefault(key,{}).setdefault(r['method'],[]).append(r)
        if r['status']!=results[key]['status']:raise ValueError('cost verdict mismatch')
        if sum(int(r[k]) for k in ('admission_ns','construction_ns','serialization_ns','replay_ns'))!=int(r['total_ns']):raise ValueError('cost phase accounting')
    derived=[]
    for (case,K),arms in sorted(pairs.items()):
        if set(arms)!={'certificate','ordinary-adjacent'} or any(len(v)!=5 for v in arms.values()):raise ValueError('paired cohort')
        cert=statistics.median(int(r['total_ns']) for r in arms['certificate'])
        ordinary=statistics.median(int(r['total_ns']) for r in arms['ordinary-adjacent'])
        derived.append(dict(case=case,cutoff=K,status=results[case,K]['status'],mode=results[case,K]['certificate']['mode'],
            certificate_median_ns=cert,ordinary_median_ns=ordinary,certificate_over_ordinary=cert/ordinary))
    with (d/'paired-costs.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(derived[0]));writer.writeheader();writer.writerows(derived)
    groups={}
    for mode in sorted({r['mode'] for r in derived}):
        r=[x for x in derived if x['mode']==mode];ratios=[x['certificate_over_ordinary'] for x in r]
        groups[mode]=dict(cases=len(r),valid=sum(x['status']=='valid' for x in r),
            median_ratio=statistics.median(ratios),minimum_ratio=min(ratios),maximum_ratio=max(ratios),
            faster=sum(v<1 for v in ratios),equal=sum(v==1 for v in ratios),slower=sum(v>1 for v in ratios))
    native=None
    if (d/'managed-world-decisions.jsonl').is_file():
        nrows=[json.loads(s) for s in (d/'managed-world-decisions.jsonl').read_text().splitlines()]
        if len(nrows)!=len(cases):raise ValueError('managed case census')
        for case,nrow in zip(cases,nrows):
            expected=[r['oracle'] for r in case['results']]
            if nrow!={'id':case['case'],'worlds':case['worlds'],'valid':expected}:raise ValueError('managed semantic mismatch')
        nsummary=json.loads((d/'managed-summary.json').read_text())
        if nsummary['cases']!=len(cases) or nsummary['worlds']!=sum(c['worlds'] for c in cases) or nsummary['decisions']!=checks or nsummary['mismatches']!=0:raise ValueError('managed summary mismatch')
        native=dict(cases=len(nrows),worlds=nsummary['worlds'],world_cutoff_checks=checks,
            sha256=hashlib.sha256((d/'managed-world-decisions.jsonl').read_bytes()).hexdigest(),scope=nsummary['scope'])
    out=dict(contracts=len(cases),decisions=len(results),world_checks=checks,cost_rows=len(rows),cost_pairs=len(derived),groups=groups,managed=native,
             no_claim='Timings are controlled generated finite Python computations, not deployment or retrieval gains.')
    (d/'analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':main()

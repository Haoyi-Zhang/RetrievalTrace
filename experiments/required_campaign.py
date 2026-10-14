"""Owned finite availability study, explicit inputs and negative results retained.

No retriever, LLM, corpus, network, solver or external implementation is invoked.
The ordinary comparator has the same contract, deterministic small-world
reduction, identity/rank fast paths and exact packet/cost semantics. It recomputes
ordinary adjacent reachability in place of the representative/local-row rule.
"""
import argparse, csv, hashlib, itertools, json, pathlib, random, sys, time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from src.required_schema import admit, worlds, PROTOCOL
from src.required_producer import produce
from src.required_replay import verify
from src.retry_producer import bad_pair as legacy_bad_pair
from tests.oracle import all_retry_worlds, retry_packets, retry_refines

def wire(x):return json.dumps(x,sort_keys=True,separators=(',',':'))

def raw(n,e,oo,B,M,H=7):
    return dict(protocol=PROTOCOL,required_outcomes=M,capsule=dict(bits=n,initial=e,horizon=H,
        outcomes=[dict(id=str(i),add=a,failure=f) for i,(a,f) in enumerate(oo)],feedback=list(B),
        query_cost=[2,0,1],feedback_cost=[0,3,1]))

def inputs():
    atoms=list(itertools.product(range(2),(None,'f','g')))
    for e in range(2):
        for signature in range(1,1<<len(atoms)):
            oo=[a for i,a in enumerate(atoms) if signature>>i&1]
            for mask in range(1<<len(oo)):
                M=[i for i in range(len(oo)) if mask>>i&1]
                for B in itertools.product((1,2,3),repeat=2):
                    yield 'one-bit-complete',raw(1,e,oo,B,M),[1]
    for e,Mmask,B in itertools.product(range(4),range(8),itertools.product((1,2,3),repeat=4)):
        yield 'two-bit-join-complete',raw(2,e,[(1,None),(2,None),(3,None)],B,[i for i in range(3) if Mmask>>i&1]),[1]
    gen=random.Random(49049)
    for i in range(512):
        n=2+i%3;N=1<<n;m=3+i%4;oo=[(gen.randrange(N),gen.choice((None,None,'f','g'))) for _ in range(m)]
        B=[gen.choice((1,2)) for _ in range(N)]
        for j in gen.sample(range(N),i%3):B[j]=3
        M=[j for j in range(m) if gen.randrange(3)==0]
        yield 'seeded-49049',raw(n,gen.randrange(N),oo,B,M),[1,2,3]

def ordinary(x,K):
    c=admit(x)
    if K==c['horizon']:return 'valid'
    D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
    if K>=D:return 'valid'
    for R,B in worlds(c,K):
        if not retry_refines(retry_packets(c,R,B,K+1),retry_packets(c,R,B,K)):return 'invalid'
    return 'valid'

def measured(x,K,method):
    encoded=wire(x);start=time.perf_counter_ns();cpu=time.process_time_ns()
    decoded=json.loads(encoded);admit(decoded);t1=time.perf_counter_ns()
    p=produce(decoded,K) if method=='certificate' else dict(status=ordinary(decoded,K))
    t2=time.perf_counter_ns();payload=wire(p).encode();received=json.loads(payload);t3=time.perf_counter_ns()
    status=verify(decoded,K,received) if method=='certificate' else ordinary(decoded,K)
    if status!=received['status']:raise RuntimeError('measurement replay disagreement')
    end=time.perf_counter_ns()
    return dict(method=method,status=status,input_bytes=len(encoded.encode()),certificate_bytes=len(payload),
        admission_ns=t1-start,construction_ns=t2-t1,serialization_ns=t3-t2,replay_ns=end-t3,
        total_ns=end-start,process_cpu_ns=time.process_time_ns()-cpu)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();cpu=time.process_time()
    families={};decisions=world_checks=executions=rescued=0;selected=[];mismatches=[]
    with (a.out/'cases.jsonl').open('w',encoding='utf8',newline='\n') as cases, (a.out/'world-checks.csv').open('w',newline='',encoding='utf8') as wfile:
        writer=csv.writer(wfile);writer.writerow(['case','cutoff','retrieval_mask','feedback','source_packets','target_packets','cost_relation','adjacent_relation'])
        for case,(family,x,cutoffs) in enumerate(inputs()):
            c=admit(x);facts={K:True for K in cutoffs};adjacent={K:True for K in cutoffs};nc=0;N=1<<c['bits']
            for R,B in all_retry_worlds(c):
                if not set(c['required_outcomes'])<=set(R):continue
                nc+=1
                horizons=sorted({c['horizon'],*cutoffs,*[K+1 for K in cutoffs]})
                packets={h:retry_packets(c,R,B,h) for h in horizons};executions+=len(horizons)
                for K in cutoffs:
                    truth=retry_refines(packets[c['horizon']],packets[K]);adj=retry_refines(packets[K+1],packets[K])
                    facts[K]&=truth;adjacent[K]&=adj;world_checks+=1
                    writer.writerow([case,K,sum(1<<i for i in R),''.join(map(str,B)),len(packets[c['horizon']]),len(packets[K]),int(truth),int(adj)])
                    if truth!=adj:mismatches.append([case,K,'pointwise adjacency'])
            results=[]
            for K in cutoffs:
                cert=produce(x,K);status=verify(x,K,cert);decisions+=1
                if (status=='valid')!=facts[K]:mismatches.append([case,K,'certificate'])
                projected=legacy_bad_pair(c) is None if K==1 else None
                rescued+=int(K==1 and facts[K] and not projected)
                results.append(dict(cutoff=K,status=status,oracle=facts[K],legacy_unrestricted_collapse=projected,certificate=cert))
                # Fixed modular selection, independent of measured costs or verdict.
                if family=='seeded-49049' and (case-15696)%17==0:selected.append((case,x,K))
            families.setdefault(family,dict(cases=0,worlds=0,valid=0,invalid=0))
            s=families[family];s['cases']+=1;s['worlds']+=nc
            s['valid']+=sum(v for v in facts.values());s['invalid']+=sum(not v for v in facts.values())
            cases.write(wire(dict(case=case,family=family,input=x,worlds=nc,results=results))+'\n')
    measurements=[]
    # Alternating order reduces one fixed order effect; no speedup threshold gate.
    for case,x,K in selected:
        for repeat in range(5):
            order=('ordinary-adjacent','certificate') if repeat%2==0 else ('certificate','ordinary-adjacent')
            for method in order:measurements.append(dict(case=case,cutoff=K,repeat=repeat,**measured(x,K,method)))
    with (a.out/'costs.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(measurements[0]));writer.writeheader();writer.writerows(measurements)
    files={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in a.out.iterdir() if p.is_file()}
    summary=dict(protocol=PROTOCOL,families=families,contracts=sum(s['cases'] for s in families.values()),
        decisions=decisions,world_decision_checks=world_checks,operational_executions=executions,
        newly_valid_under_stronger_contract=rescued,cost_cases=len(selected),cost_rows=len(measurements),
        wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,files=files,mismatches=mismatches,
        clocks={k:vars(time.get_clock_info(k)) for k in ('perf_counter','process_time')},
        measurement_scope='One Python process; per-arm admission/construction/JSON/replay and total CPU/wall. No process-tree RSS, deployment latency, network or retrieval workload.',
        comparator='Same required contract and deterministic optional-support reduction; common identity/rank paths. Ordinary adjacent reachability recomputed after receipt; not a separately certified implementation.')
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    print(wire(summary));return int(bool(mismatches))

if __name__=='__main__':sys.exit(main())

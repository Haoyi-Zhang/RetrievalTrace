"""Source-backed finite campaign. Standard library only; one process per task.

All counts describe explicit finite families, not real workload diversity.
The generator is part of the scientific input and is fixed before evaluation.
"""
from __future__ import annotations
import argparse,csv,itertools,json,pathlib,random,sys,time,resource,copy
from math import comb
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from src.schema import retry,graph,load
from src.retry_producer import produce as rp,bad_pair
from src.retry_replay import verify as rv
from src.graph_producer import produce as gp,census,cover,effects
from src.graph_replay import verify as gv
from src.adapter import expand
from tests.oracle import retry_packets,retry_refines,all_retry_worlds,graph_traces,graph_refines

ROOT=pathlib.Path(__file__).resolve().parents[1]

def write_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf8')

def size(cert):return len(json.dumps(cert,sort_keys=True,separators=(',',':')).encode('utf8'))

def capsule(n,initial,signature,B,H=5):
    oo=[]
    for i in range(2*(1<<n)):
        if signature>>i&1: oo.append(dict(id=f'o{i}',add=i%(1<<n),failure=None if i<(1<<n) else 'f'))
    return dict(bits=n,initial=initial,horizon=H,outcomes=oo,feedback=list(B),query_cost=[1,0],feedback_cost=[0,1])

def grid(initial,out):
    tables=list(itertools.product((1,2,3),repeat=4)); executions=0; count=0
    records=[];pair_checks=0;mismatches=[]
    for sig in range(1,256):
        for b,B in enumerate(tables):
            c=capsule(2,initial,sig,B); R=range(len(c['outcomes'])); values=[]; executions_by_horizon=[]
            for H in range(1,6):
                packets=retry_packets(c,R,B,H); executions+=1;executions_by_horizon.append(packets)
                values.append(sum(1<<({'ok':0,'fail:f':1,'exhausted':2}[label]*4+e) for label,e in {(x[0],x[1]) for x in packets}))
            for H in range(2,6):
                for K in range(1,H):
                    pair_checks+=1
                    if retry_refines(executions_by_horizon[H-1],executions_by_horizon[K-1]) != (values[H-1]==values[K-1]):
                        mismatches.append([initial,sig,b,H,K])
            records.append([initial,sig,b,*values]); count+=1
    with (out/f'grid-{initial}.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['initial','signature','feedback','H1','H2','H3','H4','H5']);w.writerows(records)
    return dict(contracts=count,operational_executions=executions,cost_packet_equivalence_checks=pair_checks,initial=initial,mismatches=mismatches)

def cutoff(out):
    tables=list(itertools.product((1,2,3),repeat=4)); bindex={b:i for i,b in enumerate(tables)}
    collapse_checks=adjacent_checks=rank_checks=small_checks=0; valid_cutoffs=[0,0,0]
    rowcount=0; mismatches=[]; raw=[]
    for initial in range(4):
        vals=[[None]*81 for _ in range(256)]
        with (out/f'grid-{initial}.csv').open() as f:
            for row in csv.DictReader(f):
                vals[int(row['signature'])][int(row['feedback'])]=[int(row[f'H{i}']) for i in range(1,6)]
        # A full-world packet set is not a universal contract decision.
        # Upward propagation computes conjunction over all nonempty restrictions.
        direct=[[[True]*81 for _ in range(256)] for _ in range(3)]
        for sig in range(1,256):
            for b in range(81):
                v=vals[sig][b]
                for K in range(1,4): direct[K-1][sig][b]=v[K]==v[K-1]
                for K in range(1,4):
                    for H in range(K+2,6):
                        adjacent_checks+=1
                        if (v[H-1]==v[K-1])!=(v[K]==v[K-1]): mismatches.append(['adjacent',initial,sig,b,H,K])
                D=max(1,2-initial.bit_count()+int(sig>=16))
                for K in range(D,5):
                    for H in range(K+1,6):
                        rank_checks+=1
                        if v[H-1]!=v[K-1]: mismatches.append(['rank',initial,sig,b,H,K])
        uniform=copy.deepcopy(direct)
        for K in range(3):
            # Every removal of one retrieval atom, keeping nonempty components.
            for sig in range(1,256):
                for bit in range(8):
                    sub=sig&~(1<<bit)
                    if sub and sub!=sig:
                        for b in range(81): uniform[K][sig][b] &= uniform[K][sub][b]
            # Remove one ambiguous feedback option; product order by #ambiguities.
            for b in sorted(range(81),key=lambda i:tables[i].count(3)):
                for e in range(4):
                    if tables[b][e]==3:
                        for val in (1,2):
                            small=list(tables[b]);small[e]=val; sb=bindex[tuple(small)]
                            for sig in range(1,256):uniform[K][sig][b] &= uniform[K][sig][sb]
        # Independently compute the downset contribution of every small,
        # deterministic counterworld via a bitset of invalid supersignatures.
        deterministic=[b for b,B in enumerate(tables) if 3 not in B]
        for sig in range(1,256):
            for b,B in enumerate(tables):
                c=capsule(2,initial,sig,B)
                expected=bad_pair(c) is None
                for H in range(2,6):
                    collapse_checks+=1
                    # Adjacent equivalence is separately checked; the universe
                    # closure already includes every relation restriction.
                    if expected!=uniform[0][sig][b]:mismatches.append(['collapse',initial,sig,b,H])
                cert=rp(c,1)
                if (rv(c,1,cert)=='valid')!=expected:mismatches.append(['collapse-replay',initial,sig,b])
                flags=[]
                for K in range(1,4):
                    small=True; sub=sig
                    while sub:
                        if sub.bit_count()<=K+1:
                            for db in deterministic:
                                if all(v&~w==0 for v,w in zip(tables[db],B)) and not direct[K-1][sub][db]:
                                    small=False;break
                        if not small:break
                        sub=(sub-1)&sig
                    small_checks+=1
                    actual=uniform[K-1][sig][b];valid_cutoffs[K-1]+=actual;flags.append(int(actual))
                    if small!=actual:mismatches.append(['small-world',initial,sig,b,K])
                raw.append([initial,sig,b,*flags]);rowcount+=1
    with (out/'uniform-cutoffs.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['initial','signature','feedback','K1','K2','K3']);w.writerows(raw)
    return dict(contracts=rowcount,collapse_comparisons=collapse_checks,collapse_certificate_replays=rowcount,
                adjacent_comparisons=adjacent_checks,small_world_comparisons=small_checks,rank_comparisons=rank_checks,
                valid_uniform_cutoffs=valid_cutoffs,mismatches=mismatches)

def tree_family(depth):
    if depth==0:return [('stop',0),('stop',1)]
    prev=tree_family(depth-1)
    return [('stop',0),('stop',1)]+[('call',key,a,b) for key in (0,1) for a in prev for b in prev]

def tree_nodes(tree):
    nodes=[]
    def add(t):
        here=len(nodes);nodes.append(None)
        if t[0]=='stop':nodes[here]=dict(kind='stop',label=str(t[1]),returned=0)
        else:
            a=add(t[2]);b=add(t[3]);nodes[here]=dict(kind='call',key=t[1],next=[a,b])
        return here
    add(tree);return nodes

def graphs(out):
    programs=[tree_nodes(t) for t in tree_family(2)]
    base=dict(resources=['a','b'],tokens=[],initial=0,labels=['0','1'],modules=[
        dict(key='a',requires=0,adds=[0,0],cost=[1,0]),dict(key='b',requires=0,adds=[0,0],cost=[0,1])])
    worlds=list(itertools.product((1,2,3),repeat=2)); semantics=[]
    for p in programs:
        c=dict(base,source=p,target=p)
        semantics.append([graph_traces(c,'source',w) for w in worlds])
    records=[];good=bad=0;mismatches=[]; min_bytes=10**12;max_bytes=0
    for i,P in enumerate(programs):
        for j,Q in enumerate(programs):
            c=dict(base,source=P,target=Q); cert=gp(c); got=gv(c,cert)=='valid'
            want=all(graph_refines(S,T) for S,T in zip(semantics[i],semantics[j]))
            if got!=want:mismatches.append([i,j,got,want])
            good+=got;bad+=not got; sz=size(cert);min_bytes=min(min_bytes,sz);max_bytes=max(max_bytes,sz)
            records.append([i,j,int(got),sz])
    with (out/'graph-pairs.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['source','target','valid','certificate_bytes']);w.writerows(records)
    write_json(out/'graph-inputs.json',dict(declaration=base,programs=programs))
    return dict(programs=len(programs),ordered_pairs=len(records),worlds_per_program=len(worlds),
                cached_program_world_executions=len(programs)*len(worlds),valid=good,invalid=bad,replayed=len(records),
                minimum_certificate_bytes=min_bytes,maximum_certificate_bytes=max_bytes,mismatches=mismatches)

def supports(out):
    supports=list(itertools.product(range(4),repeat=2)); worlds=list(itertools.product(range(1,4),repeat=2))
    masks=[]
    for s in supports:masks.append(sum(1<<i for i,w in enumerate(worlds) if all(a&~b==0 for a,b in zip(s,w))))
    enabled=[0]*65536
    for fam in range(1,65536):
        bit=fam&-fam;enabled[fam]=enabled[fam^bit]|masks[bit.bit_length()-1]
    mismatches=[];valid=0;tree_replays=0
    # Complete minimal-world predicate vs all-world predicate for all families.
    for i,s in enumerate(supports):
        minimum=sum(1<<j for j,w in enumerate(worlds) if all((b==a if a else b in (1,2)) for a,b in zip(s,w)))
        for family,covered in enumerate(enabled):
            left=minimum&~covered==0;right=masks[i]&~covered==0
            valid+=left
            if left!=right:mismatches.append([i,family])
        # Exercise actual cover-tree producer across 258 selected families
        # including both endpoints; exhaustive combinatorial comparison above
        # does not claim a million full graph-certificate replays.
        for family in range(0,65536,255):
            cand=[(j,list(supports[j])) for j in range(16) if family>>j&1]
            tree,bad=cover(list(s),cand,[2,2]);tree_replays+=1
            if (bad is None)!=(minimum&~enabled[family]==0):mismatches.append(['tree',i,family])
    return dict(challenged_supports=16,candidate_families=65536,comparisons=16*65536,valid_covers=valid,
                cover_search_checks=tree_replays,mismatches=mismatches)

def larger(out):
    records=[];summary={}; mismatches=[]
    for kind,count,seed in [('boolean',384,271828),('relational',192,271829),('cutoff',240,271830)]:
        gen=random.Random(seed);worlds_total=valid=0; modes={}
        for case in range(count):
            n=3+case%2;N=1<<n;m=2+case%4;initial=gen.randrange(N)
            oo=[dict(id=f'o{i}',add=gen.randrange(N),failure='f' if gen.randrange(4)==0 else None) for i in range(m)]
            B=[1+gen.randrange(2) for _ in range(N)]
            ambiguous=0 if kind=='boolean' else case%(3 if kind=='cutoff' else 4)
            for e in gen.sample(range(N),ambiguous):B[e]=3
            H=9 if kind=='cutoff' else 2+case%7; K=1+case%4 if kind=='cutoff' else 1
            c=dict(bits=n,initial=initial,horizon=H,outcomes=oo,feedback=B,query_cost=[1,0],feedback_cost=[0,1])
            cert=rp(c,K);got=rv(c,K,cert)=='valid';truth=True;nc=0
            for R,W in all_retry_worlds(c):
                truth &= retry_refines(retry_packets(c,R,W,H),retry_packets(c,R,W,K));nc+=1
            if got!=truth:mismatches.append([kind,case])
            worlds_total+=nc;valid+=got;modes[cert['mode']]=modes.get(cert['mode'],0)+1
            records.append(dict(family=kind,case=case,input=c,cutoff=K,status=cert['status'],worlds=nc,certificate=cert))
        summary[kind]=dict(cases=count,seed=seed,world_comparisons=worlds_total,operational_executions=2*worlds_total,
                           valid=valid,invalid=count-valid,modes=modes)
    write_json(out/'larger-cases.json',records)
    return dict(families=summary,cases=len(records),world_comparisons=sum(s['world_comparisons'] for s in summary.values()),mismatches=mismatches)

def scaling(out):
    rows=[];mismatches=[]
    base=load(ROOT/'inputs/examples/ordered.json')
    for H in range(1,13):
        c=dict(base,horizon=H); expanded=expand(c);generic=gp(expanded);compact=rp(c,1)
        if gv(expanded,generic)!='valid' or rv(c,1,compact)!='valid':mismatches.append(H)
        rows.append([H,len(expanded['source']),len(census(graph(expanded),'source')),size(expanded),size(generic),size(compact)])
    with (out/'encoding-scaling.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['horizon','source_nodes','source_paths','input_bytes','explicit_bytes','compact_bytes']);w.writerows(rows)
    huge=[]
    for exponent in (1,2,4,8,12,16,24,32,48,60):
        H=2**exponent;c=dict(base,horizon=H);p=rp(c,1);rv(c,1,p)
        # Also force distance mode at a horizon much larger than its finite row.
        d=load(ROOT/'inputs/examples/distance.json');d['horizon']=max(3,H);q=rp(d,2);rv(d,2,q)
        huge.append(dict(horizon=H,collapse_bytes=size(p),distance_horizon=d['horizon'],distance_bytes=size(q),worst=[H,H]))
    write_json(out/'binary-horizons.json',huge)
    return dict(rows=12,last=dict(zip(['horizon','source_nodes','source_paths','input_bytes','explicit_bytes','compact_bytes'],rows[-1])),binary_cases=len(huge),mismatches=mismatches)

def examples(out):
    items=[]
    for name,K in [('ordered',1),('distance',2),('sharp',2),('failure',1),('ambiguous',1),('huge',2)]:
        c=load(ROOT/'inputs/examples'/f'{name}.json');p=rp(c,K);s=rv(c,K,p);write_json(out/'examples'/f'{name}-certificate.json',p);items.append([name,K,s])
    c=load(ROOT/'inputs/examples/graph.json');p=gp(c);gv(c,p);write_json(out/'examples/graph-certificate.json',p)
    from src.cutoff_search import produce_least
    from src.cutoff_replay import verify_least
    minima=[]
    for name in ('ordered','distance','sharp','failure','ambiguous','huge'):
        c=load(ROOT/'inputs/examples'/f'{name}.json');p=produce_least(c);K=verify_least(c,p)
        write_json(out/'examples'/f'{name}-least.json',p);minima.append([name,K])
    return dict(retry_cases=items,graph_status='valid',least_cutoffs=minima,mismatches=[])

def main():
    p=argparse.ArgumentParser();p.add_argument('task',choices=['grid','cutoff','graphs','supports','larger','scaling','examples']);p.add_argument('--initial',type=int,default=0);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);start=time.monotonic();cpu=time.process_time()
    result=grid(a.initial,a.out) if a.task=='grid' else globals()[a.task](a.out)
    name=f'grid-{a.initial}' if a.task=='grid' else a.task
    result['measurement']=dict(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_json(a.out/(name+'.json'),result)
    print(json.dumps(dict(task=name,**{k:v for k,v in result.items() if k not in ['families','retry_cases']}),sort_keys=True))
    return 1 if result.get('mismatches') else 0
if __name__=='__main__':sys.exit(main())

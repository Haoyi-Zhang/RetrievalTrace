"""Required-availability certificates; no original campaign or protocol is changed."""
from .required_schema import admit, worlds, PROTOCOL
from .schema import integer
from .retry_producer import distance_row, bounded_paths

def bad_pair(c):
    oo=c['outcomes'];M=c['required_outcomes'];e0=c['initial']
    success={e0|oo[i]['add'] for i in M if oo[i]['failure'] is None}
    failure={(oo[i]['failure'],e0|oo[i]['add']) for i in M if oo[i]['failure'] is not None}
    for i,a in enumerate(oo):
        A=e0|a['add']
        if a['failure'] is not None or not c['feedback'][A]&1:continue
        for j,b in enumerate(oo):
            B=e0|b['add'];J=A|B
            if b['failure'] is None:
                if J in (A,B) or J in success:continue
                action='stop' if c['feedback'][J]&2 else 'exhausted'
            else:
                if J==B or (b['failure'],J) in failure:continue
                action='failure'
            return i,j,action,J
    return None

def produce(raw,K,max_worlds=200000,max_cells=2000000):
    c=admit(raw);K=integer(K,'cutoff',1,c['horizon'])
    base=dict(protocol=PROTOCOL,required_outcomes=c['required_outcomes'],horizon=c['horizon'],cutoff=K)
    if K==c['horizon']:return dict(base,status='valid',mode='identity')
    if K==1:
        pair=bad_pair(c)
        if pair is None:return dict(base,status='valid',mode='collapse')
        a,b,action,J=pair
        return dict(base,status='invalid',mode='collapse',witness=dict(
            retrieval=sorted(set(c['required_outcomes']+[a,b])),feedback=c['feedback'],
            first=a,second=b,action=action,evidence=J,
            runs=[[a,1],[b,c['horizon']-1 if action=='exhausted' else 1]]))
    D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
    if K>=D:return dict(base,status='valid',mode='rank',rank=D)
    rows=[]
    for R,B in worlds(c,K,max_worlds,max_cells):
        row,terminals=distance_row(c,R,B)
        if any(d is not None and d>K for d in row['distance']) or any(v>K for v in terminals.values()):
            short=bounded_paths(c,R,B,K);long=bounded_paths(c,R,B,K+1)
            missing=sorted(set(long)-set(short))
            if not missing:raise RuntimeError('required distance/adjacency disagreement')
            packet=missing[0]
            return dict(base,status='invalid',mode='distance',witness=dict(
                retrieval=R,feedback=B,path=long[packet],packet=list(packet)))
        rows.append(row)
    return dict(base,status='valid',mode='distance',rows=rows)

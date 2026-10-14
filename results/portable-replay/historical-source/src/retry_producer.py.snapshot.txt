"""Certificate search. The consumer does not import this module."""
from __future__ import annotations
from collections import deque
from itertools import combinations, product
from math import comb
from .schema import retry, integer, Unknown

MAX_WORLDS = 200000
MAX_CELLS = 2000000

def bad_pair(c):
    e0=c['initial']; oo=c['outcomes']; candidates=[]
    for i,a in enumerate(oo):
        A=e0|a['add']
        if a['failure'] is not None or not c['feedback'][A]&1:
            continue
        for j,b in enumerate(oo):
            B=e0|b['add']; J=A|B
            if b['failure'] is not None and J != B:
                candidates.append((0,i,j,'failure',J))
            elif b['failure'] is None and J != A and J != B:
                action='stop' if c['feedback'][J]&2 else 'exhausted'
                candidates.append((0 if action=='stop' else 1,i,j,action,J))
    return min(candidates) if candidates else None

def worlds(c,K, max_worlds=MAX_WORLDS, max_cells=MAX_CELLS):
    m=len(c['outcomes']); size=1<<c['bits']
    choices=[tuple(b for b in (1,2) if mask&b) for mask in c['feedback']]
    count=sum(comb(m,i) for i in range(1,min(K+1,m)+1))
    for cs in choices: count*=len(cs)
    if count>max_worlds or count*size>max_cells:
        raise Unknown(f'distance mode requires {count} worlds and {count*size} cells')
    for size_r in range(1,min(K+1,m)+1):
        for R in combinations(range(m),size_r):
            for B in product(*choices):
                yield list(R),list(B)

def distance_row(c,R,B):
    N=1<<c['bits']; d=[None]*N; parents=[None]*N; todo=deque()
    for i in R:
        o=c['outcomes'][i]; e=c['initial']|o['add']
        if o['failure'] is None and B[e]==1 and d[e] is None:
            d[e]=1; parents[e]=[-1,i]; todo.append(e)
    while todo:
        e=todo.popleft()
        for i in R:
            o=c['outcomes'][i]; v=e|o['add']
            if o['failure'] is None and B[v]==1 and d[v] is None:
                d[v]=d[e]+1; parents[v]=[e,i]; todo.append(v)
    terminals={}
    for e,length in [(c['initial'],0)]+[(e,v) for e,v in enumerate(d) if v is not None]:
        for i in R:
            o=c['outcomes'][i]; v=e|o['add']; f=o['failure']
            if f is not None or B[v]==2:
                key=(('fail:'+f) if f is not None else 'ok',v)
                terminals[key]=min(terminals.get(key,length+1),length+1)
    return {'retrieval':R,'feedback':B,'distance':d,'parents':parents},terminals

def bounded_paths(c,R,B,H):
    current={c['initial']:[]}; terminals={}
    for step in range(1,H+1):
        following={}
        for e,path in current.items():
            for i in R:
                o=c['outcomes'][i]; v=e|o['add']; p=path+[i]
                if o['failure'] is not None:
                    terminals.setdefault(('fail:'+o['failure'],v),p)
                elif B[v]==2:
                    terminals.setdefault(('ok',v),p)
                elif step==H:
                    terminals.setdefault(('exhausted',v),p)
                else:
                    following.setdefault(v,p)
        current=following
    return terminals

def produce(raw,K,max_worlds=MAX_WORLDS,max_cells=MAX_CELLS):
    c=retry(raw); K=integer(K,'cutoff',1,c['horizon'])
    base={'cutoff':K,'horizon':c['horizon']}
    if K==c['horizon']:
        return dict(base,status='valid',mode='identity')
    if K==1:
        pair=bad_pair(c)
        if pair is None:
            return dict(base,status='valid',mode='collapse')
        _,a,b,action,J=pair
        return dict(base,status='invalid',mode='collapse',
                    witness={'retrieval':[a,b],'feedback':c['feedback'],
                             'first':a,'second':b,'action':action,'evidence':J,
                             'runs':[[a,1],[b,c['horizon']-1 if action=='exhausted' else 1]]})
    rank=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
    if K>=rank:
        return dict(base,status='valid',mode='rank',rank=rank)
    rows=[]
    for R,B in worlds(c,K,max_worlds,max_cells):
        row,ts=distance_row(c,R,B)
        if any(v is not None and v>K for v in row['distance']) or any(v>K for v in ts.values()):
            shorter=bounded_paths(c,R,B,K); longer=bounded_paths(c,R,B,K+1)
            missing=[t for t in longer if t not in shorter]
            if not missing:
                raise RuntimeError('distance / adjacent construction disagreed')
            label,e=min(missing)
            return dict(base,status='invalid',mode='distance',witness={
                'retrieval':R,'feedback':B,'path':longer[(label,e)],'packet':[label,e]})
        rows.append(row)
    return dict(base,status='valid',mode='distance',rows=rows)

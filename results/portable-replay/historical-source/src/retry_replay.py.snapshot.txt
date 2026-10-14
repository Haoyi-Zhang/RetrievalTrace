"""Local retry certificate consumer. No producer or shortest-path imports.

Distance labels are checked by parent descent and all-edge inequalities, not by
rerunning BFS. Invalid adjacent traces are replayed against complete target
state sets. The consumer is not hardened for use as a hostile network service.
"""
from __future__ import annotations
from itertools import combinations,product
from math import comb
from .schema import retry,require,integer,Unknown,identical

def _expected_worlds(c,K,max_worlds,max_cells):
    m=len(c['outcomes']); a=sum(v==3 for v in c['feedback'])
    count=(1<<a)*sum(comb(m,s) for s in range(1,min(m,K+1)+1))
    if count>max_worlds or count*(1<<c['bits'])>max_cells:
        raise Unknown('universal certificate exceeds the declared replay ceiling')
    for s in range(1,min(m,K+1)+1):
        for R in combinations(range(m),s):
            for B in product(*[[v for v in (1,2) if allowed&v] for allowed in c['feedback']]):
                yield list(R),list(B)

def _world(c,w,deterministic=True):
    require(type(w) is dict,'world must be an object')
    R=w.get('retrieval'); B=w.get('feedback')
    require(type(R) is list and R,'retrieval world must be nonempty')
    for i in R: integer(i,'outcome index',0,len(c['outcomes'])-1)
    require(len(set(R))==len(R),'duplicate retrieval index')
    require(type(B) is list and len(B)==len(c['feedback']),'feedback world width mismatch')
    for value,allowed in zip(B,c['feedback']):
        integer(value,'feedback world',1,3)
        require(value&~allowed==0,'feedback world exceeds declaration')
        if deterministic: require(value in (1,2),'singleton feedback required')
    return R,B

def _row(c,row,R,B,K):
    require(type(row) is dict,'distance row must be an object')
    # Validate serialized world metadata before comparing it with the expected
    # world.  Python aliases bool/int and int/float under ==, so ordinary list
    # equality is not a safe certificate-binding check.
    row_R,row_B=_world(c,{'retrieval':row.get('retrieval'),'feedback':row.get('feedback')})
    require(identical(row_R,R) and identical(row_B,B),
            'missing, reordered, or wrong universal world')
    n=1<<c['bits']; d=row.get('distance'); parent=row.get('parents')
    require(type(d) is list and len(d)==n and type(parent) is list and len(parent)==n,'distance row dimensions')
    for e,label in enumerate(d):
        if label is None:
            require(parent[e] is None,'infinite label has a parent')
            continue
        integer(label,'distance',1,n)
        require(label<=K,'continuation distance exceeds cutoff')
        p=parent[e]
        require(type(p) is list and len(p)==2,'finite label requires parent')
        u=integer(p[0],'parent vertex',-1,n-1); i=integer(p[1],'parent outcome',0,len(c['outcomes'])-1)
        require(i in R,'parent uses disabled outcome')
        o=c['outcomes'][i]
        require(o['failure'] is None and B[e]==1,'parent is not a continuing edge')
        require((c['initial'] if u==-1 else u)|o['add']==e,'parent evidence is wrong')
        if u==-1: require(label==1,'root parent requires distance one')
        else: require(d[u] is not None and type(d[u]) is int and d[u]+1==label,'parent must descend by one')
    # Root edges and every edge from a finite vertex; closure checks infinity too.
    for u,base in [(-1,0)]+[(e,v) for e,v in enumerate(d) if v is not None]:
        owned=c['initial'] if u==-1 else u
        for i in R:
            o=c['outcomes'][i]; e=owned|o['add']
            if o['failure'] is None and B[e]==1:
                require(d[e] is not None and d[e]<=base+1,'distance inequality or reachability closure failed')
    # All exact terminal minima, grouped by label and returned evidence.
    best={}
    for owned,base in [(c['initial'],0)]+[(e,v) for e,v in enumerate(d) if v is not None]:
        for i in R:
            o=c['outcomes'][i]; e=owned|o['add']
            if o['failure'] is not None: packet=('fail:'+o['failure'],e)
            elif B[e]==2: packet=('ok',e)
            else: continue
            best[packet]=min(best.get(packet,base+1),base+1)
    require(all(v<=K for v in best.values()),'terminal distance exceeds cutoff')

def _target_packets(c,R,B,K):
    active={c['initial']}; done=set()
    for t in range(K):
        nxt=set()
        for e in active:
            for i in R:
                o=c['outcomes'][i]; value=e|o['add']
                if o['failure'] is not None: done.add(('fail:'+o['failure'],value))
                elif B[value]==2: done.add(('ok',value))
                elif t==K-1: done.add(('exhausted',value))
                else: nxt.add(value)
        active=nxt
    return done

def verify(raw,K,cert,max_worlds=200000,max_cells=2000000):
    c=retry(raw); K=integer(K,'cutoff',1,c['horizon'])
    require(type(cert) is dict,'certificate must be an object')
    require(type(cert.get('cutoff')) is int and cert['cutoff']==K and
            type(cert.get('horizon')) is int and cert['horizon']==c['horizon'],'horizon/cutoff binding failed')
    status=cert.get('status'); mode=cert.get('mode')
    require(status in ('valid','invalid'),'unknown verdict')
    if mode=='identity':
        require(status=='valid' and K==c['horizon'],'invalid identity')
    elif mode=='collapse':
        require(K==1 and c['horizon']>1,'collapse precondition')
        if status=='valid':
            for first in c['outcomes']:
                A=c['initial']|first['add']
                if first['failure'] is not None or c['feedback'][A] not in (1,3): continue
                for last in c['outcomes']:
                    B=c['initial']|last['add']
                    if last['failure'] is not None:
                        require(A|B==B,'failure absorption does not hold')
                    else:
                        require(A|B in (A,B),'success values are incomparable')
        else:
            w=cert.get('witness'); R,B=_world(c,w,False)
            a=integer(w.get('first'),'first',0,len(c['outcomes'])-1)
            b=integer(w.get('second'),'second',0,len(c['outcomes'])-1)
            require(len(R)==2 and set(R)=={a,b},'collapse witness needs exactly its two outcomes')
            first=c['outcomes'][a]; last=c['outcomes'][b]
            A=c['initial']|first['add']; C=c['initial']|last['add']; J=A|C
            require(first['failure'] is None and B[A]&1,'first step cannot continue')
            action=w.get('action')
            if last['failure'] is not None:
                require(action=='failure' and J!=C,'not a failure counterexample')
            else:
                require(J not in (A,C),'not an incomparable success counterexample')
                require((action=='stop' and B[J]&2) or (action=='exhausted' and B[J]&1),'terminal feedback unavailable')
            integer(w.get('evidence'),'witness evidence',0,(1<<c['bits'])-1)
            require(w['evidence']==J,'wrong witness evidence')
            runs=w.get('runs'); expected=[[a,1],[b,c['horizon']-1 if action=='exhausted' else 1]]
            require(runs==expected and all(type(v) is int for r in runs for v in r),'incorrect compressed trace')
    elif mode=='rank':
        D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
        require(status=='valid' and type(cert.get('rank')) is int and cert['rank']==D and K>=D,'rank certificate fails')
    elif mode=='distance':
        require(K<c['horizon'],'distance precondition')
        if status=='valid':
            rows=cert.get('rows'); require(type(rows) is list,'universal rows required')
            j=0
            for R,B in _expected_worlds(c,K,max_worlds,max_cells):
                require(j<len(rows),'missing universal row')
                _row(c,rows[j],R,B,K); j+=1
            require(j==len(rows),'extra universal rows')
        else:
            w=cert.get('witness'); R,B=_world(c,w)
            require(len(R)<=K+1,'counterworld exceeds bound')
            path=w.get('path'); require(type(path) is list and len(path)==K+1,'adjacent witness length')
            # Since rank bounds all valid finite inputs, an enormous K cannot
            # have a valid negative certificate; reject before bounded replay.
            D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
            require(K<D,'rank bound rules out this negative certificate')
            e=c['initial']; packet=None
            for j,i in enumerate(path):
                integer(i,'path outcome',0,len(c['outcomes'])-1); require(i in R,'path uses disabled outcome')
                o=c['outcomes'][i]; e|=o['add']
                if o['failure'] is not None: packet=('fail:'+o['failure'],e)
                elif B[e]==2: packet=('ok',e)
                elif j==K: packet=('exhausted',e)
                if packet is not None: require(j==K,'counterexample terminates too early')
            require(type(w.get('packet')) is list and identical(w['packet'],list(packet)),'wrong terminal packet')
            require(packet not in _target_packets(c,R,B,K),'target has a matching packet')
    else:
        require(False,'unknown certificate mode')
    return status

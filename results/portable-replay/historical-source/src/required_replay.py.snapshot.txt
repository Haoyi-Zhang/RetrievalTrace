"""Local required-availability consumer; imports no producer or graph search.

Existing typed distance-row and bounded negative replay are trusted components.
The required-world census and collapse obligations are checked here separately.
"""
from itertools import combinations, product
from math import comb
from .required_schema import admit, PROTOCOL
from .schema import require, integer, identical, Unknown
from .retry_replay import _world, _row, _target_packets

def _expected(c,K,max_worlds,max_cells):
    required=set(c['required_outcomes']);rest=sorted(set(range(len(c['outcomes'])))-required)
    start=0 if required else 1; end=min(K+1,len(rest))
    count=(2**c['feedback'].count(3))*sum(comb(len(rest),s) for s in range(start,end+1))
    if count>max_worlds or count*2**c['bits']>max_cells:raise Unknown('required replay census exceeds ceiling')
    for size in range(start,end+1):
        for extra in combinations(rest,size):
            for feedback in product(*[[v for v in (1,2) if v&mask] for mask in c['feedback']]):
                yield sorted(required|set(extra)),list(feedback)

def _pair_missing(c,first,last):
    oo=c['outcomes'];A=c['initial']|oo[first]['add'];B=c['initial']|oo[last]['add'];J=A|B
    if oo[first]['failure'] is not None or not c['feedback'][A]&1:return False
    enabled=set(c['required_outcomes'])|{first,last}
    if oo[last]['failure'] is None:
        return not any(oo[i]['failure'] is None and c['initial']|oo[i]['add']==J for i in enabled)
    return not any(oo[i]['failure']==oo[last]['failure'] and c['initial']|oo[i]['add']==J for i in enabled)

def verify(raw,K,cert,max_worlds=200000,max_cells=2000000):
    c=admit(raw);K=integer(K,'cutoff',1,c['horizon'])
    require(type(cert) is dict,'required certificate must be an object')
    require(cert.get('protocol')==PROTOCOL and identical(cert.get('required_outcomes'),c['required_outcomes']),
            'required contract binding failed')
    require(type(cert.get('horizon')) is int and cert['horizon']==c['horizon'] and
            type(cert.get('cutoff')) is int and cert['cutoff']==K,'horizon/cutoff binding failed')
    status=cert.get('status');mode=cert.get('mode');require(status in ('valid','invalid'),'unknown verdict')
    D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
    if mode=='identity':require(status=='valid' and K==c['horizon'],'identity precondition')
    elif mode=='rank':require(status=='valid' and K>=D and type(cert.get('rank')) is int and cert['rank']==D,'rank fails')
    elif mode=='collapse':
        require(K==1 and c['horizon']>1,'collapse precondition')
        if status=='valid':
            for a in range(len(c['outcomes'])):
                for b in range(len(c['outcomes'])):require(not _pair_missing(c,a,b),'required representative absent')
        else:
            w=cert.get('witness');R,B=_world(c,w,False)
            a=integer(w.get('first'),'first',0,len(c['outcomes'])-1)
            b=integer(w.get('second'),'second',0,len(c['outcomes'])-1)
            require(R==sorted(set(c['required_outcomes']+[a,b])),'wrong required pair world')
            require(_pair_missing(c,a,b),'pair has a required representative')
            oo=c['outcomes'];A=c['initial']|oo[a]['add'];J=A|oo[b]['add'];action=w.get('action')
            require(B[A]&1,'first step cannot continue')
            if oo[b]['failure'] is not None:require(action=='failure','failure action required')
            else:require((action=='stop' and B[J]&2) or (action=='exhausted' and B[J]&1),'terminal feedback unavailable')
            integer(w.get('evidence'),'evidence',0,(1<<c['bits'])-1);require(w['evidence']==J,'wrong evidence')
            expected=[[a,1],[b,c['horizon']-1 if action=='exhausted' else 1]]
            require(identical(w.get('runs'),expected),'incorrect compressed runs')
    elif mode=='distance':
        require(K<c['horizon'],'distance precondition')
        if status=='valid':
            rows=cert.get('rows');require(type(rows) is list,'rows required');count=0
            for R,B in _expected(c,K,max_worlds,max_cells):
                require(count<len(rows),'missing required world row');_row(c,rows[count],R,B,K);count+=1
            require(count==len(rows),'extra required world rows')
        else:
            w=cert.get('witness');R,B=_world(c,w)
            require(set(c['required_outcomes'])<=set(R),'required availability omitted')
            require(len(set(R)-set(c['required_outcomes']))<=K+1,'too many optional outcomes')
            require(K<D,'rank excludes this negative')
            path=w.get('path');require(type(path) is list and len(path)==K+1,'adjacent trace length')
            e=c['initial'];packet=None
            for step,i in enumerate(path):
                integer(i,'path outcome',0,len(c['outcomes'])-1);require(i in R,'disabled outcome')
                o=c['outcomes'][i];e|=o['add']
                if o['failure'] is not None:packet=('fail:'+o['failure'],e)
                elif B[e]==2:packet=('ok',e)
                elif step==K:packet=('exhausted',e)
                if packet is not None:require(step==K,'early terminal')
            require(identical(w.get('packet'),list(packet)),'incorrect terminal packet')
            require(packet not in _target_packets(c,R,B,K),'matching target packet exists')
    else:require(False,'unknown required certificate mode')
    return status

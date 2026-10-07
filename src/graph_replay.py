"""Separate census replay and cover-tree verification; no producer imports."""
from __future__ import annotations
from collections import deque
from .schema import graph,require,integer,Unknown,path_budget,identical

def _routes(c,side,limit):
    # Breadth-first execution, then canonical route ordering. This is independent
    # of the producer's depth-first census and does not read supplied trace data.
    path_budget(c[side],limit)
    work=deque([(0,(),tuple(0 for _ in c['resources']),tuple(0 for _ in c['modules']),())]); rows=[]
    while work:
        at,word,charge,used,route=work.popleft(); node=c[side][at]; kind=node['kind']
        if kind=='stop':
            rows.append({'route':[list(p) for p in route+((at,-1),)],
                         'observation':[list(word),node['label'],node['returned']],
                         'cost':list(charge),'support':list(used)})
            if len(rows)>limit: raise Unknown('replay census ceiling')
            continue
        if kind=='emit':
            work.append((node['next'],word+(node['symbol'],),charge,used,route+((at,0),)))
        else:
            for branch,dest in enumerate(node['next']):
                ch=charge; su=used
                if kind=='call':
                    key=node['key']; ch=tuple(charge[j]+c['modules'][key]['cost'][j] for j in range(len(charge)))
                    tmp=list(used); tmp[key]=tmp[key]|(2**branch); su=tuple(tmp)
                work.append((dest,word,ch,su,route+((at,branch),)))
        if len(work)+len(rows)>limit*1000:
            raise Unknown('replay frontier ceiling')
    rows.sort(key=lambda x:x['route'])
    return rows

def _matches(a,b,direction):
    if a['observation']!=b['observation']: return False
    for i in range(len(a['cost'])):
        if direction=='safety' and a['cost'][i]>b['cost'][i]: return False
        if direction=='coverage' and b['cost'][i]>a['cost'][i]: return False
    return True

def _packet_groups(rows):
    # Reconstructed locally by replay; no producer or supplied index is trusted.
    if any(type(row['observation'][1]) is not str for row in rows): return None
    groups={}
    for position in range(len(rows)):
        observation=rows[position]['observation']
        packet=(tuple(observation[0]),observation[1],observation[2])
        groups.setdefault(packet,[]).append((position,rows[position]))
    return groups

def _tree(tree,fixed,candidates,alphabets,budget):
    todo=[(tree,fixed)]
    while todo:
        budget[0]-=1
        if budget[0]<0: raise Unknown('replay cover ceiling')
        node,known=todo.pop(); require(type(node) is dict,'cover node must be object')
        if 'leaf' in node:
            require(set(node)=={'leaf'},'ambiguous cover node')
            j=integer(node['leaf'],'leaf trace index')
            require(j in candidates,'leaf is not compatible')
            require(all(x&~y==0 for x,y in zip(candidates[j]['support'],known)),'leaf support not covered')
        else:
            require(set(node)=={'key','children'},'malformed split')
            k=integer(node['key'],'split key',0,len(known)-1)
            require(known[k]==0,'split key is already fixed')
            children=node['children']
            require(type(children) is list and len(children)==alphabets[k],'split must cover every outcome')
            for i,child in enumerate(children):
                nxt=known.copy(); nxt[k]=1<<i; todo.append((child,nxt))

def verify(raw,cert,max_paths=100000,max_tree=200000):
    c=graph(raw); require(type(cert) is dict,'certificate must be object')
    S=_routes(c,'source',max_paths); T=_routes(c,'target',max_paths)
    status=cert.get('status'); require(status in ('valid','invalid'),'unknown verdict')
    alphabet=[len(m['adds']) for m in c['modules']]
    if status=='valid':
        require(identical(cert.get('source'),S) and identical(cert.get('target'),T),'incomplete or incorrect census')
        require(type(cert.get('covers')) is dict,'missing covers')
        for direction,left,right in [('safety',T,S),('coverage',S,T)]:
            trees=cert['covers'].get(direction)
            require(type(trees) is list and len(trees)==len(left),'missing trace obligation')
            groups=_packet_groups(right)
            for challenge,tree in zip(left,trees):
                observation=challenge['observation']
                packet=(tuple(observation[0]),observation[1],observation[2])
                bucket=enumerate(right) if groups is None or type(observation[1]) is not str else groups.get(packet,())
                cand={j:r for j,r in bucket if _matches(challenge,r,direction)}
                _tree(tree,challenge['support'].copy(),cand,alphabet,[max_tree])
    else:
        direction=cert.get('direction'); require(direction in ('safety','coverage'),'wrong challenge direction')
        left,right=(T,S) if direction=='safety' else (S,T)
        i=integer(cert.get('challenge'),'challenge',0,len(left)-1); a=left[i]
        world=cert.get('world'); require(type(world) is list and len(world)==len(alphabet),'world dimension')
        for w,n in zip(world,alphabet): integer(w,'world component',1,(1<<n)-1)
        require(all(s&~w==0 for s,w in zip(a['support'],world)),'challenge disabled')
        observation=a['observation']
        packet=(tuple(observation[0]),observation[1],observation[2])
        groups=_packet_groups(right)
        opposite=enumerate(right) if groups is None or type(observation[1]) is not str else groups.get(packet,())
        require(not any(_matches(a,b,direction) and all(s&~w==0 for s,w in zip(b['support'],world)) for _,b in opposite),
                'negative world has a compatible opposite trace')
    return status

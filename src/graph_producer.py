"""Explicit structural-census and support-cover certificate producer."""
from __future__ import annotations
from .schema import graph,Unknown,path_budget

MAX_PATHS=100000
MAX_TREE=200000

def census(c,side,max_paths=MAX_PATHS):
    nodes=c[side]; path_budget(nodes,max_paths); mods=c['modules']; out=[]
    stack=[(0,c['initial'],[],[0]*len(c['resources']),[0]*len(mods),[])]
    while stack:
        v,e,word,cost,support,route=stack.pop(); node=nodes[v]; kind=node['kind']
        if kind=='stop':
            out.append(dict(route=route+[[v,-1]],observation=[word,node['label'],node['returned']],cost=cost,support=support))
            if len(out)>max_paths: raise Unknown('structural census path ceiling reached')
        elif kind=='emit':
            stack.append((node['next'],e,word+[node['symbol']],cost,support,route+[[v,0]]))
        else:
            for edge in reversed(range(len(node['next']))):
                ee=e; cc=cost; ss=support
                if kind=='call':
                    k=node['key']; m=mods[k]; ee=e|m['adds'][edge]
                    cc=[a+b for a,b in zip(cost,m['cost'])]; ss=support.copy(); ss[k]|=1<<edge
                stack.append((node['next'][edge],ee,word,cc,ss,route+[[v,edge]]))
    return out

def compatible(challenge,candidate,direction):
    if challenge['observation']!=candidate['observation']: return False
    small,large=(challenge,candidate) if direction=='safety' else (candidate,challenge)
    return all(a<=b for a,b in zip(small['cost'],large['cost']))

def _observation_index(rows):
    # This is a fresh index of the complete census, not a reduced census.
    # Original indices and equal-observation route multiplicity are retained.
    # Admission permits an equal string subclass as a stop label. Preserve the
    # old scan for such Python-only inputs (including unhashable subclasses).
    if any(type(row['observation'][1]) is not str for row in rows): return None
    index={}
    for j,row in enumerate(rows):
        word,label,evidence=row['observation']
        index.setdefault((tuple(word),label,evidence),[]).append((j,row))
    return index

def cover(support,candidates,alphabets,max_nodes=MAX_TREE):
    counter=[0]
    def solve(fixed):
        counter[0]+=1
        if counter[0]>max_nodes: raise Unknown('cover-tree ceiling reached')
        for idx,s in candidates:
            if all(x&~y==0 for x,y in zip(s,fixed)):
                return {'leaf':idx},None
        unused=[k for k,x in enumerate(fixed) if not x]
        if not unused: return None,fixed
        k=unused[0]; children=[]
        for i in range(alphabets[k]):
            nxt=fixed.copy(); nxt[k]=1<<i
            tree,bad=solve(nxt)
            if bad is not None: return None,bad
            children.append(tree)
        return {'key':k,'children':children},None
    return solve(list(support))

def produce(raw,max_paths=MAX_PATHS,max_tree=MAX_TREE):
    c=graph(raw); S=census(c,'source',max_paths); T=census(c,'target',max_paths)
    indices={'safety':_observation_index(S),'coverage':_observation_index(T)}
    alphabet=[len(m['adds']) for m in c['modules']]
    challenges=[]
    for direction,left,right in [('safety',T,S),('coverage',S,T)]:
        for i,t in enumerate(left): challenges.append((len(t['route']),direction,i,t,right))
    trees={'safety':[None]*len(T),'coverage':[None]*len(S)}
    for _,direction,i,t,right in sorted(challenges,key=lambda q:q[:3]):
        word,label,evidence=t['observation']
        index=indices[direction]
        bucket=enumerate(right) if index is None or type(label) is not str else index.get((tuple(word),label,evidence),())
        candidates=[(j,r['support']) for j,r in bucket if compatible(t,r,direction)]
        tree,bad=cover(t['support'],candidates,alphabet,max_tree)
        if bad is not None:
            return {'status':'invalid','direction':direction,'challenge':i,'world':bad}
        trees[direction][i]=tree
    return {'status':'valid','source':S,'target':T,'covers':trees}

def effects(raw,side):
    c=graph(raw); nodes=c[side]; dim=len(c['resources']); n=len(nodes)
    must=[None]*n; costs=[None]*n; counts=[0]*n
    must[0]=c['initial']; costs[0]=[0]*dim; counts[0]=1
    labels=set(); worst=[0]*dim; paths=0
    for v,node in enumerate(nodes):
        if not counts[v]: continue
        if node['kind']=='stop':
            labels.add(node['label']); paths+=counts[v]
            worst=[max(a,b) for a,b in zip(worst,costs[v])]; continue
        if node['kind']=='emit': edges=[(node['next'],0,[0]*dim)]
        elif node['kind']=='choose': edges=[(j,0,[0]*dim) for j in node['next']]
        else:
            m=c['modules'][node['key']]; edges=[(j,a,m['cost']) for j,a in zip(node['next'],m['adds'])]
        for j,a,w in edges:
            e=must[v]|a; co=[x+y for x,y in zip(costs[v],w)]
            must[j]=e if must[j] is None else must[j]&e
            costs[j]=co if costs[j] is None else [max(x,y) for x,y in zip(costs[j],co)]
            counts[j]+=counts[v]
    return {'must':must,'prefix_cost':costs,'prefix_paths':counts,'terminal_paths':paths,'labels':sorted(labels),'worst':worst}

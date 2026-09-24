"""Finite retry-to-forward-DAG expansion, for the declared Boolean semantics.

Used only for bounded correspondence tests and the explicit representation
baseline. The specialized checker never invokes this adapter on a huge horizon.
"""
from .schema import retry,Unknown

def expand(raw,target_horizon=1,max_horizon=12):
    c=retry(raw)
    if c['horizon']>max_horizon or not 1<=target_horizon<=c['horizon']:
        raise Unknown('adapter explicitly bounded to small horizons')
    n=c['bits']; N=1<<n; modules=[]
    modules.append(dict(key='retrieval',requires=0,adds=[o['add'] for o in c['outcomes']],cost=c['query_cost']))
    actions=[]
    for e,mask in enumerate(c['feedback']):
        allowed=[a for a in (1,2) if mask&a]; actions.append(allowed)
        modules.append(dict(key=f'feedback:{e}',requires=e,adds=[0]*len(allowed),cost=c['feedback_cost']))
    def program(H):
        # Build symbolic states first; order by phase and attempt to ensure every
        # real edge points forward. Keep only reachable states of the full world.
        start=('r',0,c['initial']); queue=[start]; edges={}; leaves=set()
        for state in queue:
            if state in edges: continue
            phase,t,e=state; dest=[]
            if phase=='r':
                for o in c['outcomes']:
                    value=e|o['add']
                    if o['failure'] is not None: d=('t','fail:'+o['failure'],value); leaves.add(d)
                    else: d=('b',t,value)
                    dest.append(d)
            else:
                for a in actions[e]:
                    if a==2: d=('t','ok',e); leaves.add(d)
                    elif t==H-1: d=('t','exhausted',e); leaves.add(d)
                    else: d=('r',t+1,e)
                    dest.append(d)
            edges[state]=dest
            queue.extend(d for d in dest if d[0]!='t' and d not in edges)
        states=sorted(edges,key=lambda s:(s[1],s[0]=='b',s[2]))+sorted(leaves)
        index={s:i for i,s in enumerate(states)}; nodes=[]
        for state in states:
            phase,t,e=state
            if phase=='t': nodes.append(dict(kind='stop',label=t,returned=e))
            else: nodes.append(dict(kind='call',key=0 if phase=='r' else e+1,next=[index[d] for d in edges[state]]))
        return nodes
    return dict(resources=[f'resource:{i}' for i in range(len(c['query_cost']))],
                tokens=[f'evidence:{i}' for i in range(n)],initial=c['initial'],
                labels=['ok','exhausted']+sorted({'fail:'+o['failure'] for o in c['outcomes'] if o['failure'] is not None}),
                modules=modules,source=program(c['horizon']),target=program(target_horizon))

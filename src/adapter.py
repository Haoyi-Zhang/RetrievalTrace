"""Finite retry-to-forward-DAG expansion, for the declared Boolean semantics.

Used only for bounded correspondence tests and the explicit representation
baseline. The specialized checker never invokes this adapter on a huge horizon.
"""
from collections import deque
from .schema import (retry,Unknown,integer,GRAPH_MAX_MODULES,
                     GRAPH_MAX_OUTCOMES,GRAPH_MAX_NODES)

def expand(raw,target_horizon=1,max_horizon=12):
    c=retry(raw)
    # This is an input binding, not a resource failure.  Validate it before any
    # state construction so values such as 1.5 cannot evade the final-attempt
    # equality and cause an unbounded symbolic expansion.
    target_horizon=integer(target_horizon,'target_horizon',1,c['horizon'])
    max_horizon=integer(max_horizon,'max_horizon',1)
    if c['horizon']>max_horizon:
        raise Unknown('adapter explicitly bounded to small horizons')

    # The expansion preserves every nominal feedback key and every retrieval
    # outcome.  If that exact representation exceeds the admitted graph schema,
    # return UNKNOWN rather than merging keys or deleting branches.
    module_count=1+(1<<c['bits'])
    if module_count>GRAPH_MAX_MODULES:
        raise Unknown('adapter expansion exceeds the graph module ceiling')
    if len(c['outcomes'])>GRAPH_MAX_OUTCOMES:
        raise Unknown('adapter retrieval module exceeds the graph outcome ceiling')

    n=c['bits']; N=1<<n; modules=[]
    modules.append(dict(key='retrieval',requires=0,adds=[o['add'] for o in c['outcomes']],cost=c['query_cost']))
    actions=[]
    for e,mask in enumerate(c['feedback']):
        allowed=[a for a in (1,2) if mask&a]; actions.append(allowed)
        modules.append(dict(key=f'feedback:{e}',requires=e,adds=[0]*len(allowed),cost=c['feedback_cost']))

    def program(H):
        # Build only unique symbolic states.  Every admitted state becomes one
        # graph node, so enforcing the node ceiling during discovery bounds the
        # construction before a schema-invalid graph can be returned.
        start=('r',0,c['initial'])
        queue=deque([start]); discovered={start}; edges={}; leaves=set()

        def admit(dest):
            if dest[0]=='t':
                leaves.add(dest)
            elif dest not in discovered:
                discovered.add(dest); queue.append(dest)
            if len(discovered)+len(leaves)>GRAPH_MAX_NODES:
                raise Unknown('adapter expansion exceeds the graph node ceiling')

        while queue:
            state=queue.popleft(); phase,t,e=state; dest=[]
            if phase=='r':
                for o in c['outcomes']:
                    value=e|o['add']
                    if o['failure'] is not None: d=('t','fail:'+o['failure'],value)
                    else: d=('b',t,value)
                    dest.append(d); admit(d)
            else:
                for a in actions[e]:
                    if a==2: d=('t','ok',e)
                    elif t==H-1: d=('t','exhausted',e)
                    else: d=('r',t+1,e)
                    dest.append(d); admit(d)
            edges[state]=dest

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

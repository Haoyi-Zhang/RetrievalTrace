"""Direct finite operational oracle, not using certificate or theorem modules."""
from itertools import product

def retry_packets(c,R,B,H):
    active={c['initial']}; result=set()
    for step in range(1,H+1):
        following=set()
        for owned in active:
            for idx in R:
                outcome=c['outcomes'][idx]; value=owned|outcome['add']
                failure=outcome['failure']
                if failure is not None:
                    cost=tuple(step*q+(step-1)*b for q,b in zip(c['query_cost'],c['feedback_cost']))
                    result.add(('fail:'+failure,value,cost))
                else:
                    cost=tuple(step*(q+b) for q,b in zip(c['query_cost'],c['feedback_cost']))
                    if B[value]&2: result.add(('ok',value,cost))
                    if B[value]&1:
                        if step==H: result.add(('exhausted',value,cost))
                        else: following.add(value)
        active=following
    return result

def retry_refines(source,target):
    def match(s,t):
        return s[:2]==t[:2] and all(b<=a for a,b in zip(s[2],t[2]))
    return all(any(match(s,t) for s in source) for t in target) and all(any(match(s,t) for t in target) for s in source)

def all_retry_worlds(c):
    for mask in range(1,1<<len(c['outcomes'])):
        R=[i for i in range(len(c['outcomes'])) if mask>>i&1]
        for B in product(*[[v for v in (1,2,3) if v&~allowed==0] for allowed in c['feedback']]):
            yield R,list(B)

def graph_traces(c,side,world):
    work=[(0,c['initial'],(),tuple(0 for _ in c['resources']))]; terminals=set()
    while work:
        pc,owned,word,cost=work.pop(); node=c[side][pc]
        if node['kind']=='stop': terminals.add((word,node['label'],node['returned'],cost))
        elif node['kind']=='emit': work.append((node['next'],owned,word+(node['symbol'],),cost))
        elif node['kind']=='choose':
            for dest in node['next']: work.append((dest,owned,word,cost))
        else:
            m=c['modules'][node['key']]
            for index,dest in enumerate(node['next']):
                if world[node['key']]>>index&1:
                    work.append((dest,owned|m['adds'][index],word,tuple(a+b for a,b in zip(cost,m['cost']))))
    return terminals

def graph_refines(S,T):
    def match(s,t): return s[:3]==t[:3] and all(y<=x for x,y in zip(s[3],t[3]))
    return all(any(match(s,t) for s in S) for t in T) and all(any(match(s,t) for t in T) for s in S)


def componentwise_attained_worst(packets):
    """Return the operational coordinatewise maximum and whether one trace attains it."""
    if not packets:
        raise ValueError('at least one terminal packet is required')
    width=len(next(iter(packets))[2])
    worst=tuple(max(packet[2][i] for packet in packets) for i in range(width))
    return worst,any(packet[2]==worst for packet in packets)

def erase_exhaustion_evidence(packets):
    """Project exhausted observations to their tag while preserving costs."""
    return {(('exhausted',) if tag=='exhausted' else (tag,evidence),cost)
            for tag,evidence,cost in packets}

def projected_refines(source,target):
    """Two-sided cost-compatible refinement for already projected observations."""
    def match(s,t):
        return s[0]==t[0] and all(b<=a for a,b in zip(s[1],t[1]))
    return (all(any(match(s,t) for s in source) for t in target) and
            all(any(match(s,t) for t in target) for s in source))

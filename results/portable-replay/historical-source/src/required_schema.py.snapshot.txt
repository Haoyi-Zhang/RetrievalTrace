"""Explicit availability contract. Legacy capsule admission is unchanged."""
from itertools import combinations, product
from math import comb
from .schema import retry, require, integer, Unknown

PROTOCOL='required-outcomes-v1'

def admit(raw):
    require(type(raw) is dict and set(raw)=={'protocol','required_outcomes','capsule'},
            'required contract needs exactly protocol, required_outcomes, capsule')
    require(raw['protocol']==PROTOCOL,'unsupported required-outcome protocol')
    c=retry(raw['capsule']); M=raw['required_outcomes']
    require(type(M) is list,'required_outcomes must be a list')
    for i in M:integer(i,'required outcome',0,len(c['outcomes'])-1)
    require(M==sorted(set(M)),'required indices must be distinct and increasing')
    c['required_outcomes']=list(M)
    return c

def worlds(c,K=None,max_worlds=200000,max_cells=2000000,all_feedback=False):
    """Producer/oracle enumeration; consumer implements its own census."""
    M=c['required_outcomes']; optional=[i for i in range(len(c['outcomes'])) if i not in M]
    lo=0 if M else 1;hi=len(optional) if K is None or all_feedback else min(K+1,len(optional))
    choices=[tuple(b for b in ((1,2,3) if all_feedback else (1,2)) if not b&~v) for v in c['feedback']]
    count=sum(comb(len(optional),s) for s in range(lo,hi+1))
    for row in choices:count*=len(row)
    if count>max_worlds or count*(1<<c['bits'])>max_cells:raise Unknown('required world census exceeds ceiling')
    for s in range(lo,hi+1):
        for extra in combinations(optional,s):
            for B in product(*choices):yield sorted(M+list(extra)),list(B)

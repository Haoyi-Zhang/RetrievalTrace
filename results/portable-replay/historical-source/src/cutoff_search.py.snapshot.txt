"""Search the least valid positive cutoff; replay needs no search history."""
from __future__ import annotations
from .schema import retry
from .retry_producer import produce

def produce_least(raw):
    c=retry(raw); H=c['horizon']
    D=max(1,c['bits']-c['initial'].bit_count()+int(any(o['failure'] is not None for o in c['outcomes'])))
    low,high=1,min(H,D)
    while low<high:
        mid=(low+high)//2
        if produce(c,mid)['status']=='valid':high=mid
        else:low=mid+1
    return dict(kind='least-cutoff',horizon=H,cutoff=low,
                upper=produce(c,low),lower=None if low==1 else produce(c,low-1))

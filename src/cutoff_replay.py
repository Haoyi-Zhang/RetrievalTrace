"""Replay extremality using only two ordinary certificates, not the search."""
from __future__ import annotations
from .schema import retry,integer,require
from .retry_replay import verify

def verify_least(raw,certificate):
    c=retry(raw); p=certificate
    require(isinstance(p,dict) and set(p)=={'kind','horizon','cutoff','upper','lower'},'least-cutoff fields')
    require(p['kind']=='least-cutoff','least-cutoff kind')
    H=integer(p['horizon'],'horizon',1);require(H==c['horizon'],'horizon binding')
    K=integer(p['cutoff'],'cutoff',1);require(K<=H,'cutoff exceeds source')
    require(verify(c,K,p['upper'])=='valid','upper cutoff must be valid')
    if K==1:require(p['lower'] is None,'cutoff one has no positive predecessor')
    else:require(verify(c,K-1,p['lower'])=='invalid','predecessor must be invalid')
    return K

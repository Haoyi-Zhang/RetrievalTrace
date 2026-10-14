"""Owned finite graph regression with a literal, independent world oracle.

Standalone from any directory, or included by ordinary unittest discovery.
No historical code, private-stage path, campaign driver or timing is used.
"""
from __future__ import annotations
import copy
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.graph_producer import produce
from src.graph_replay import verify
from src.schema import Invalid,Unknown


def stop(label='ok',returned=0):
    return dict(kind='stop',label=label,returned=returned)


def cases():
    programs=[[stop(label,e)] for label in ('ok','fail') for e in range(4)]
    programs += [[dict(kind='emit',symbol=s,next=1),stop()] for s in ('','a','ab','λ')]
    programs += [[dict(kind='emit',symbol='a',next=1),
                  dict(kind='emit',symbol='b',next=2),stop()],
                 [dict(kind='emit',symbol='ab',next=1),stop()]]
    for key in (0,1):
        for first,last in ((stop(),stop()),(stop(),stop('fail')),(stop(returned=1),stop(returned=3))):
            programs.append([dict(kind='call',key=key,next=[1,2]),first,last])
    programs += [[dict(kind='call',key=0,next=[1,1]),
                  dict(kind='call',key=0,next=[2,2]),stop()],
                 [dict(kind='choose',next=[1,1,1]),stop()],
                 [dict(kind='choose',next=[1,2]),dict(kind='call',key=0,next=[3,3]),
                  dict(kind='call',key=1,next=[3,3]),stop()]]
    for prices in (([0,0],[0,0]),([2,0],[0,2])):
        for source,target in itertools.product(programs,repeat=2):
            yield dict(resources=['q','b'],tokens=['same-origin','same-origin'],initial=3,
                       labels=['ok','fail'],modules=[
                           dict(key='a',adds=[1,2],cost=prices[0]),
                           dict(key='b',adds=[1,2],cost=prices[1]),
                           dict(key='unused',adds=[0,0],cost=[0,0])],
                       source=copy.deepcopy(source),target=copy.deepcopy(target))
    # Late match in an equal-packet bucket: neither coordinate can be borrowed
    # from a different source trace to dominate the target (1,1).
    raw=dict(resources=['q','b'],tokens=[],initial=0,
        labels=['ok','fail'],modules=[dict(key=str(i),adds=[0],cost=c)
                                     for i,c in enumerate(([2,0],[0,2],[1,1]))],
        source=[dict(kind='choose',next=[1,2]),dict(kind='call',key=0,next=[3]),
                dict(kind='call',key=1,next=[3]),stop()],
        target=[dict(kind='call',key=2,next=[1]),stop()])
    yield raw
    raw=copy.deepcopy(raw)
    raw['source'][0]['next'].append(3)  # zero-cost packet is still not a witness
    yield raw
    raw=copy.deepcopy(raw)
    raw['source'][0]['next'].append(4)
    raw['source'].extend([dict(kind='call',key=2,next=[5]),stop()])
    yield raw
    # Acquisition, repeated nominal key and real evidence ownership.
    yield dict(resources=['q'],tokens=['a','b'],initial=0,labels=['ok'],
        modules=[dict(key='fetch',adds=[1,3],cost=[1])],
        source=[dict(kind='call',key=0,next=[1,1]),dict(kind='call',key=0,next=[2,3]),
                stop(returned=1),stop(returned=3)],
        target=[dict(kind='call',key=0,next=[1,2]),stop(returned=1),stop(returned=3)])


def literal_routes(raw,side):
    """Enumerate literal branch sequences, preserving parallel-edge multiplicity."""
    rows=[]
    def visit(pc,word,charge,choices,route):
        n=raw[side][pc]; kind=n['kind']
        if kind=='stop':
            rows.append(dict(route=route+[[pc,-1]],
                observation=[word,n['label'],n.get('returned',0)],cost=charge,
                support=[sum(2**i for i in sorted(s)) for s in choices]))
        elif kind=='emit':
            visit(n['next'],word+[n['symbol']],charge,choices,route+[[pc,0]])
        else:
            for edge,dest in enumerate(n['next']):
                cc=list(charge); ss=[set(s) for s in choices]
                if kind=='call':
                    k=n['key']; ss[k].add(edge)
                    cc=[cc[i]+raw['modules'][k]['cost'][i] for i in range(len(cc))]
                visit(dest,word,cc,ss,route+[[pc,edge]])
    visit(0,[],[0]*len(raw['resources']),[set() for _ in raw['modules']],[])
    return rows


def used(row,raw):
    return [{i for i in range(len(m['adds'])) if row['support'][k]//(2**i)%2}
            for k,m in enumerate(raw['modules'])]


def literal_certificate(raw):
    """Apply the stated tree rules using literal outcome sets, not bit tests/indexes."""
    S=literal_routes(raw,'source'); T=literal_routes(raw,'target')
    covers=dict(safety=[None]*len(T),coverage=[None]*len(S))
    obligations=sorted((len(t['route']),d,i,t,right)
        for d,left,right in [('safety',T,S),('coverage',S,T)] for i,t in enumerate(left))
    for _,d,i,t,right in obligations:
        eligible=[]
        for j,r in enumerate(right):
            if t['observation']!=r['observation']: continue
            target,source=(t,r) if d=='safety' else (r,t)
            if all(target['cost'][k]<=source['cost'][k] for k in range(len(t['cost']))):
                eligible.append((j,used(r,raw)))
        def rule(fixed):
            for j,support in eligible:
                if all(support[k].issubset(fixed[k]) for k in range(len(fixed))):
                    return dict(leaf=j),None
            remaining=[k for k,values in enumerate(fixed) if not values]
            if not remaining: return None,[sum(2**o for o in sorted(s)) for s in fixed]
            key=remaining[0]; children=[]
            for outcome in range(len(raw['modules'][key]['adds'])):
                following=[set(s) for s in fixed]; following[key]={outcome}
                tree,bad=rule(following)
                if bad is not None: return None,bad
                children.append(tree)
            return dict(key=key,children=children),None
        tree,bad=rule(used(t,raw))
        if bad is not None: return dict(status='invalid',direction=d,challenge=i,world=bad)
        covers[d][i]=tree
    return dict(status='valid',source=S,target=T,covers=covers)


def literal_verdict(raw):
    """All nonempty product worlds; direct route execution and whole-vector witnesses."""
    def traces(side,world):
        result=[]
        def run(pc,word,charge):
            n=raw[side][pc]
            if n['kind']=='stop':
                result.append((word,n['label'],n.get('returned',0),charge)); return
            if n['kind']=='emit': run(n['next'],word+(n['symbol'],),charge); return
            for edge,dest in enumerate(n['next']):
                if n['kind']=='call':
                    k=n['key']
                    if edge not in world[k]: continue
                    cc=tuple(charge[i]+raw['modules'][k]['cost'][i] for i in range(len(charge)))
                else: cc=charge
                run(dest,word,cc)
        run(0,(),tuple(0 for _ in raw['resources']))
        return result
    domains=[]
    for m in raw['modules']:
        domains.append([set(s) for size in range(1,len(m['adds'])+1)
                        for s in itertools.combinations(range(len(m['adds'])),size)])
    for world in itertools.product(*domains):
        S,T=traces('source',world),traces('target',world)
        def match(s,t): return s[:3]==t[:3] and all(t[3][k]<=s[3][k] for k in range(len(s[3])))
        if not all(any(match(s,t) for s in S) for t in T): return 'invalid'
        if not all(any(match(s,t) for t in T) for s in S): return 'invalid'
    return 'valid'


def boundary_case():
    return dict(resources=['q'],tokens=[],initial=0,labels=['ok'],
        modules=[dict(key='a',adds=[0,0],cost=[0])],source=[stop()],
        target=[dict(kind='call',key=0,next=[1,1]),stop()])


def mutations(raw,cert):
    out=[]
    if cert['status']=='valid':
        for side in ('source','target'):
            p=copy.deepcopy(cert); p[side].pop(); out.append(p)
            p=copy.deepcopy(cert); p[side][0]['observation'][2]=True; out.append(p)
        p=copy.deepcopy(cert); p['covers']['safety'].pop(); out.append(p)
        p=copy.deepcopy(cert); p['covers']['coverage'][0]={'leaf':True}; out.append(p)
        p=copy.deepcopy(cert); p['covers']['coverage'][0]={'key':0,'children':[]}; out.append(p)
    else:
        for value in (True,-1,1000):
            p=copy.deepcopy(cert); p['challenge']=value; out.append(p)
        p=copy.deepcopy(cert); p['world']=[0]*len(raw['modules']); out.append(p)
        p=copy.deepcopy(cert); p['world']=[True]*len(raw['modules']); out.append(p)
    return out+[None,{},dict(status='not-a-verdict')]


class ObservationRegression(unittest.TestCase):
    def test_complete_packets_and_independent_all_worlds(self):
        for raw in cases():
            expected=literal_certificate(raw)
            self.assertEqual(produce(raw),expected)
            self.assertEqual(expected['status'],literal_verdict(raw))
            self.assertEqual(verify(raw,expected),expected['status'])

    def test_caps_and_parallel_routes(self):
        raw=boundary_case(); expected=literal_certificate(raw)
        self.assertEqual(len(expected['target']),2)
        self.assertEqual(expected['covers']['coverage'][0],
                         dict(key=0,children=[dict(leaf=0),dict(leaf=1)]))
        for paths in (0,1):
            with self.assertRaises(Unknown): produce(raw,max_paths=paths)
            with self.assertRaises(Unknown): verify(raw,expected,max_paths=paths)
        for nodes in (0,1,2):
            with self.assertRaises(Unknown): produce(raw,max_tree=nodes)
            with self.assertRaises(Unknown): verify(raw,expected,max_tree=nodes)
        self.assertEqual(produce(raw,max_paths=2,max_tree=3),expected)
        self.assertEqual(verify(raw,expected,max_paths=2,max_tree=3),'valid')

    def test_rejects_corrupt_census_cover_and_negative(self):
        raw=boundary_case(); cert=produce(raw)
        for p in mutations(raw,cert):
            with self.assertRaises(Invalid): verify(raw,p)
        for change in ('omit','duplicate'):
            p=copy.deepcopy(cert); children=p['covers']['coverage'][0]['children']
            if change=='omit': children.pop()
            else: children[1]=copy.deepcopy(children[0])
            with self.assertRaises(Invalid): verify(raw,p)
        raw=copy.deepcopy(raw); raw['target']=[stop()]
        p=dict(status='invalid',direction='coverage',challenge=0,world=[3])
        with self.assertRaisesRegex(Invalid,'compatible opposite trace'): verify(raw,p)
        raw=list(cases())[-2]  # a matching (1,1) source route is late in the bucket
        p=dict(status='invalid',direction='safety',challenge=0,world=[1,1,1])
        with self.assertRaisesRegex(Invalid,'compatible opposite trace'): verify(raw,p)

    def test_input_admission_precedes_certificate_admission(self):
        for field,value in [('resources',[]),('initial',True),('modules',None),('source',[]),('labels',[])]:
            raw=boundary_case(); raw[field]=value
            with self.assertRaises(Invalid): produce(raw)
            with self.assertRaises(Invalid): verify(raw,None)
        raw=boundary_case(); raw['target'][0]['next']=[True,1]
        with self.assertRaises(Invalid): produce(raw)
        with self.assertRaises(Invalid): verify(raw,{})
        class UnhashableLabel(str):
            __hash__=None
        raw=boundary_case(); raw['target'][1]['label']=UnhashableLabel('ok')
        self.assertEqual(verify(raw,produce(raw)),'valid')

    def test_call_local_index_after_mutation_between_calls(self):
        raw=boundary_case(); self.assertEqual(verify(raw,produce(raw)),'valid')
        raw['labels'].append('new'); raw['target'][1]['label']='new'
        self.assertEqual(verify(raw,produce(raw)),'invalid')
        raw['target'][1]['label']='ok'
        self.assertEqual(verify(raw,produce(raw)),'valid')


if __name__=='__main__': unittest.main()

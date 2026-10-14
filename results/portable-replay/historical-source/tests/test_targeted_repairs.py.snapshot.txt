"""Regression tests for coverage, certificate typing, and adapter admission."""
from __future__ import annotations
import copy,unittest
from unittest.mock import patch
from pathlib import Path
from src.schema import retry,graph,load,Invalid,Unknown
from src.retry_producer import produce as retry_produce
from src.retry_replay import verify as retry_verify
from src.graph_producer import produce as graph_produce
from src.graph_replay import verify as graph_verify
from src.adapter import expand
from tests.oracle import (retry_packets,componentwise_attained_worst,
                          erase_exhaustion_evidence,projected_refines)

ROOT=Path(__file__).resolve().parents[1]

def example(name):
    return load(ROOT/'inputs/examples'/f'{name}.json')

def stop():
    return dict(kind='stop',label='ok',returned=0)

def split_graph():
    # Source needs no outcome; target has one matching trace for each possible
    # outcome.  Its coverage proof therefore contains one real binary split.
    return dict(resources=['q'],tokens=[],initial=0,labels=['ok'],
                modules=[dict(key='binary',requires=0,adds=[0,0],cost=[0])],
                source=[stop()],
                target=[dict(kind='call',key=0,next=[1,1]),stop()])

def adapter_case(bits=0,outcomes=1,horizon=2):
    return dict(bits=bits,initial=0,horizon=horizon,
                outcomes=[dict(id=f's{i}',failure=None,add=0) for i in range(outcomes)],
                feedback=[1]*(1<<bits),query_cost=[1,0],feedback_cost=[0,1])

def cost_case(branch):
    q=[2,1,0]; b=[1,0,3]; H=4
    if branch=='continuing-success':
        raw=dict(bits=0,initial=0,horizon=H,
                 outcomes=[dict(id='s',failure=None,add=0)],feedback=[1],
                 query_cost=q,feedback_cost=b)
        R=[0]; B=[1]; expected=[H*(x+y) for x,y in zip(q,b)]
    elif branch=='immediate-success':
        raw=dict(bits=0,initial=0,horizon=H,
                 outcomes=[dict(id='s',failure=None,add=0),dict(id='f',failure='f',add=0)],feedback=[2],
                 query_cost=q,feedback_cost=b)
        R=[0,1]; B=[2]; expected=[x+y for x,y in zip(q,b)]
    elif branch=='all-failures':
        raw=dict(bits=0,initial=0,horizon=H,
                 outcomes=[dict(id='f0',failure='f0',add=0),dict(id='f1',failure='f1',add=0)],feedback=[1],
                 query_cost=q,feedback_cost=b)
        R=[0,1]; B=[1]; expected=q
    else:
        raise ValueError(branch)
    return retry(raw),R,B,H,tuple(expected)

class DistanceRowMetadataTests(unittest.TestCase):
    def certificate(self):
        c=example('distance'); p=retry_produce(c,2)
        self.assertEqual(retry_verify(c,2,p),'valid')
        return c,p
    def test_original_certificate_remains_valid(self):
        self.certificate()
        c=example('sharp'); p=retry_produce(c,2)
        self.assertEqual(retry_verify(c,2,p),'invalid')
        p['witness']['packet'][1]=float(p['witness']['packet'][1])
        with self.assertRaises(Invalid): retry_verify(c,2,p)
    def test_retrieval_boolean_alias_is_malformed(self):
        c,p=self.certificate(); p['rows'][0]['retrieval']=[False]
        with self.assertRaises(Invalid): retry_verify(c,2,p)
    def test_feedback_boolean_alias_is_malformed(self):
        c,p=self.certificate(); p['rows'][0]['feedback'][0]=True
        with self.assertRaises(Invalid): retry_verify(c,2,p)
    def test_feedback_float_alias_is_malformed(self):
        c,p=self.certificate(); p['rows'][0]['feedback'][0]=1.0
        with self.assertRaises(Invalid): retry_verify(c,2,p)

class CoverSplitMutationTests(unittest.TestCase):
    def certificate(self):
        c=split_graph(); p=graph_produce(c)
        self.assertEqual(graph_verify(c,p),'valid')
        self.assertIn('children',p['covers']['coverage'][0])
        return c,p
    def test_missing_split_child_is_rejected(self):
        c,p=self.certificate(); p['covers']['coverage'][0]['children'].pop()
        with self.assertRaises(Invalid): graph_verify(c,p)
    def test_duplicated_split_child_is_rejected(self):
        c,p=self.certificate(); children=p['covers']['coverage'][0]['children']
        children[1]=copy.deepcopy(children[0])
        with self.assertRaises(Invalid): graph_verify(c,p)

class WorstVectorOracleTests(unittest.TestCase):
    def check(self,branch):
        c,R,B,H,expected=cost_case(branch)
        packets=retry_packets(c,R,B,H)
        actual,attained=componentwise_attained_worst(packets)
        self.assertEqual(actual,expected)
        self.assertTrue(attained)
    def test_continuing_success_branch(self): self.check('continuing-success')
    def test_immediate_success_branch(self): self.check('immediate-success')
    def test_all_failures_branch(self): self.check('all-failures')

class ObservationErasureBoundaryTests(unittest.TestCase):
    def test_three_atom_adjacent_passes_but_larger_fails(self):
        raw=dict(bits=3,initial=0,horizon=3,
                 outcomes=[dict(id=f's{i}',failure=None,add=1<<i) for i in range(3)],
                 feedback=[1]*7+[2],query_cost=[1,0],feedback_cost=[0,1])
        c=retry(raw); R=[0,1,2]; B=[1]*7+[2]
        p1=erase_exhaustion_evidence(retry_packets(c,R,B,1))
        p2=erase_exhaustion_evidence(retry_packets(c,R,B,2))
        p3=erase_exhaustion_evidence(retry_packets(c,R,B,3))
        self.assertTrue(projected_refines(p2,p1))
        self.assertFalse(projected_refines(p3,p1))

class AdapterAdmissionTests(unittest.TestCase):
    def test_fractional_target_horizon_is_malformed_before_expansion(self):
        with self.assertRaises(Invalid): expand(adapter_case(),1.5)
    def test_boolean_target_horizon_is_malformed(self):
        with self.assertRaises(Invalid): expand(adapter_case(),True)
    def test_four_bits_fit_nominal_module_boundary(self):
        raw=adapter_case(bits=4); retry(raw); graph(expand(raw))
    def test_five_bits_return_unknown_at_nominal_module_boundary(self):
        raw=adapter_case(bits=5); retry(raw)
        with self.assertRaises(Unknown): expand(raw)
    def test_thirty_two_retrieval_outcomes_fit_graph_boundary(self):
        raw=adapter_case(outcomes=32); retry(raw); graph(expand(raw))
    def test_thirty_three_retrieval_outcomes_return_unknown(self):
        raw=adapter_case(outcomes=33); retry(raw)
        with self.assertRaises(Unknown): expand(raw)
    def test_node_budget_accepts_limit_and_rejects_limit_plus_one(self):
        raw=adapter_case()  # source has exactly five unique graph nodes
        with patch('src.adapter.GRAPH_MAX_NODES',5): graph(expand(raw))
        with patch('src.adapter.GRAPH_MAX_NODES',4):
            with self.assertRaises(Unknown): expand(raw)

if __name__=='__main__':
    unittest.main()

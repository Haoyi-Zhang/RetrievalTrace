from __future__ import annotations
import copy,itertools,json,pathlib,unittest
from src.schema import retry,graph,Invalid,Unknown,load
from src.retry_producer import produce as rp,distance_row
from src.retry_replay import verify as rv
from src.graph_producer import produce as gp,effects,census
from src.graph_replay import verify as gv
from src.adapter import expand
from tests.oracle import retry_packets,retry_refines,all_retry_worlds,graph_traces,graph_refines

ROOT=pathlib.Path(__file__).resolve().parents[1]
def example(name): return load(ROOT/'inputs/examples'/f'{name}.json')
def stop(label='ok',returned=0): return dict(kind='stop',label=label,returned=returned)
def simple_graph(): return dict(resources=['q'],tokens=[],initial=0,labels=['ok','fail'],modules=[dict(key='a',adds=[0,0],cost=[1])],source=[stop()],target=[stop()])

class RetryCases(unittest.TestCase):
    def test_ordered_collapse(self):
        c=example('ordered'); self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_incomparable_collapse(self):
        c=example('sharp'); self.assertEqual(rv(c,1,rp(c,1)),'invalid')
    def test_rank(self):
        c=example('sharp'); p=rp(c,3); self.assertEqual(p['mode'],'rank'); self.assertEqual(rv(c,3,p),'valid')
    def test_distance(self):
        c=example('distance'); p=rp(c,2); self.assertEqual(p['mode'],'distance'); self.assertEqual(rv(c,2,p),'valid')
    def test_adjacent_negative(self):
        c=example('sharp'); p=rp(c,2); self.assertEqual(rv(c,2,p),'invalid')
    def test_huge_distance(self):
        c=example('huge'); p=rp(c,2); self.assertEqual(rv(c,2,p),'valid'); self.assertLess(len(json.dumps(p)),10000)
    def test_failure_absorption(self):
        c=example('failure'); self.assertEqual(rv(c,1,rp(c,1)),'invalid')
    def test_absorbed_failure(self):
        c=example('failure'); c['outcomes'][-1]['add']=1; self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_ambiguous_feedback(self):
        c=example('ambiguous'); self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_stop_at_union(self):
        c=example('sharp'); c['feedback']=[2]*8; c['feedback'][1]=1
        p=rp(c,1); self.assertEqual(p['witness']['action'],'stop'); self.assertEqual(rv(c,1,p),'invalid')
    def test_identity(self):
        c=example('ordered'); self.assertEqual(rv(c,10,rp(c,10)),'valid')
    def test_zero_bits_positive_root(self):
        c=dict(bits=0,initial=0,horizon=8,outcomes=[dict(id='s',failure=None,add=0)],feedback=[1])
        row,_=distance_row(retry(c),[0],[1]); self.assertEqual(row['distance'],[1]); self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_initial_full(self):
        c=example('sharp'); c['initial']=7; self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_failure_only(self):
        c=example('failure'); c['outcomes']=c['outcomes'][-1:]; self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_duplicate_payload_ids(self):
        c=example('ordered'); c['outcomes'][1]['add']=1; self.assertEqual(rv(c,1,rp(c,1)),'valid')
    def test_zero_cost(self):
        c=example('distance'); c['query_cost']=[0]; c['feedback_cost']=[0]; self.assertEqual(rv(c,2,rp(c,2)),'valid')
    def test_rank_failure_sharp(self):
        c=example('sharp'); c['outcomes'].append(dict(id='f',failure='f',add=0))
        self.assertEqual(rv(c,3,rp(c,3)),'invalid'); self.assertEqual(rv(c,4,rp(c,4)),'valid')
    def test_small_operational_all_worlds(self):
        for name,K in [('ambiguous',1),('distance',2),('sharp',2),('failure',1)]:
            c=retry(example(name)); expected=True
            for R,B in all_retry_worlds(c):
                expected &= retry_refines(retry_packets(c,R,B,4),retry_packets(c,R,B,K))
            self.assertEqual(rp(c,K)['status']=='valid',expected,name)
    def test_huge_compressed_counterexample(self):
        c=example('sharp'); c['horizon']=2**60; p=rp(c,1)
        self.assertEqual(rv(c,1,p),'invalid'); self.assertEqual(sum(r[1] for r in p['witness']['runs']),2**60)
    def test_predicate_shorthand(self):
        c=example('ordered'); c.pop('feedback'); c['predicate']=0; self.assertEqual(rv(c,1,rp(c,1)),'valid')

class Mutations(unittest.TestCase):
    def bad(self,cert,raw=None,K=2):
        with self.assertRaises(Invalid): rv(raw or example('distance'),K,cert)
    def test_missing_world_row(self):
        p=rp(example('distance'),2); p['rows'].pop(); self.bad(p)
    def test_extra_world_row(self):
        p=rp(example('distance'),2); p['rows'].append(p['rows'][0]); self.bad(p)
    def test_reordered_worlds(self):
        p=rp(example('distance'),2); p['rows'].reverse(); self.bad(p)
    def test_forged_parent(self):
        p=rp(example('distance'),2); p['rows'][0]['parents'][3]=[-1,2]; self.bad(p)
    def test_infinite_reachable(self):
        p=rp(example('distance'),2); p['rows'][0]['distance'][3]=None; p['rows'][0]['parents'][3]=None; self.bad(p)
    def test_fake_reachable(self):
        p=rp(example('distance'),2); p['rows'][0]['distance'][0]=1; p['rows'][0]['parents'][0]=[-1,0]; self.bad(p)
    def test_zero_distance(self):
        p=rp(example('distance'),2); p['rows'][0]['distance'][3]=0; self.bad(p)
    def test_boolean_distance(self):
        p=rp(example('distance'),2); p['rows'][0]['distance'][3]=True; self.bad(p)
    def test_wrong_horizon(self):
        p=rp(example('distance'),2); p['horizon']+=1; self.bad(p)
    def test_wrong_cutoff(self):
        p=rp(example('distance'),2); p['cutoff']=3; self.bad(p)
    def test_false_collapse(self):
        c=example('sharp'); p=dict(horizon=10,cutoff=1,mode='collapse',status='valid'); self.bad(p,c,1)
    def test_false_rank(self):
        c=example('sharp'); p=dict(horizon=10,cutoff=2,mode='rank',status='valid',rank=2); self.bad(p,c)
    def test_wrong_packet(self):
        c=example('sharp'); p=rp(c,2); p['witness']['packet'][1]=0; self.bad(p,c)
    def test_disabled_witness(self):
        c=example('sharp'); p=rp(c,2); p['witness']['retrieval']=[0]; self.bad(p,c)
    def test_wrong_runs(self):
        c=example('sharp'); p=rp(c,1); p['witness']['runs'][1][1]-=1; self.bad(p,c,1)
    def test_fake_negative(self):
        c=example('distance'); p=rp(example('sharp'),2); self.bad(p,c)
    def test_unknown_world_limit(self):
        with self.assertRaises(Unknown): rp(example('distance'),2,max_worlds=1)
    def test_unknown_cell_limit(self):
        with self.assertRaises(Unknown): rv(example('distance'),2,rp(example('distance'),2),max_cells=1)
    def test_bool_cutoff(self):
        with self.assertRaises(Invalid): rp(example('ordered'),True)
    def test_negative_cost(self):
        c=example('ordered'); c['query_cost']=[-1,0]
        with self.assertRaises(Invalid): rp(c,1)
    def test_empty_feedback(self):
        c=example('ordered'); c['feedback'][0]=0
        with self.assertRaises(Invalid): rp(c,1)
    def test_empty_outcomes(self):
        c=example('ordered'); c['outcomes']=[]
        with self.assertRaises(Invalid): rp(c,1)
    def test_duplicate_id(self):
        c=example('ordered'); c['outcomes'][1]['id']=c['outcomes'][0]['id']
        with self.assertRaises(Invalid): rp(c,1)
    def test_dimension_mismatch(self):
        c=example('ordered'); c['feedback_cost']=[0]
        with self.assertRaises(Invalid): rp(c,1)
    def test_out_of_range_mask(self):
        c=example('ordered'); c['outcomes'][0]['add']=4
        with self.assertRaises(Invalid): rp(c,1)
    def test_boolean_horizon(self):
        c=example('ordered'); c['horizon']=True
        with self.assertRaises(Invalid): rp(c,1)
    def test_bad_feedback_width(self):
        c=example('ordered'); c['feedback'].pop()
        with self.assertRaises(Invalid): rp(c,1)
    def test_duplicate_json_key(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)/'x.json';p.write_text('{"bits":1,"bits":2}')
            with self.assertRaises(Invalid): load(p)

class GraphCases(unittest.TestCase):
    def test_example(self):
        c=example('graph'); self.assertEqual(gv(c,gp(c)),'valid')
    def test_identity_no_keys(self):
        c=simple_graph(); c['modules']=[]; self.assertEqual(gv(c,gp(c)),'valid')
    def test_missing_observation(self):
        c=simple_graph(); c['target']=[stop('fail')]; self.assertEqual(gv(c,gp(c)),'invalid')
    def test_resource_increase(self):
        c=simple_graph(); c['target']=[dict(kind='call',key=0,next=[1,1]),stop()]; self.assertEqual(gv(c,gp(c)),'invalid')
    def test_resource_reduction(self):
        c=simple_graph(); c['source']=[dict(kind='call',key=0,next=[1,1]),stop()]; self.assertEqual(gv(c,gp(c)),'valid')
    def test_public_word(self):
        c=simple_graph(); c['source']=[dict(kind='emit',symbol='event',next=1),stop()]; self.assertEqual(gv(c,gp(c)),'invalid')
    def test_parallel_edges_count(self):
        c=simple_graph(); c['source']=[dict(kind='call',key=0,next=[1,1]),stop()]; self.assertEqual(effects(c,'source')['terminal_paths'],2)
    def test_unowned_return(self):
        c=simple_graph(); c['tokens']=['a']; c['source']=[stop(returned=1)]
        with self.assertRaises(Invalid): gp(c)
    def test_unowned_call(self):
        c=simple_graph(); c['tokens']=['a']; c['modules'][0]['requires']=1; c['source']=[dict(kind='call',key=0,next=[1,1]),stop()]
        with self.assertRaises(Invalid): gp(c)
    def test_cycle_rejected(self):
        c=simple_graph(); c['source']=[dict(kind='call',key=0,next=[0,0])]
        with self.assertRaises(Invalid): gp(c)
    def test_missing_branch(self):
        c=simple_graph(); c['source']=[dict(kind='call',key=0,next=[1]),stop()]
        with self.assertRaises(Invalid): gp(c)
    def test_census_omission(self):
        c=example('graph'); p=gp(c); p['source'].pop()
        with self.assertRaises(Invalid): gv(c,p)
    def test_census_forgery(self):
        c=example('graph'); p=gp(c); p['source'][0]['cost'][0]=0
        with self.assertRaises(Invalid): gv(c,p)
    def test_boolean_census(self):
        c=example('graph'); p=gp(c); p['source'][0]['support'][0]=True
        with self.assertRaises(Invalid): gv(c,p)
    def test_missing_obligation(self):
        c=example('graph'); p=gp(c); p['covers']['coverage'].pop()
        with self.assertRaises(Invalid): gv(c,p)
    def test_disabled_negative_world(self):
        c=simple_graph(); c['target']=[stop('fail')]; p=gp(c); p['world']=[0]
        with self.assertRaises(Invalid): gv(c,p)
    def test_path_cap(self):
        c=example('graph')
        with self.assertRaises(Unknown): gp(c,max_paths=1)
    def test_replay_path_cap(self):
        c=example('graph'); p=gp(c)
        with self.assertRaises(Unknown): gv(c,p,max_paths=1)
    def test_adaptive_graph_oracle(self):
        c=graph(example('graph'))
        for world in ([1],[2],[3]):
            self.assertTrue(graph_refines(graph_traces(c,'source',world),graph_traces(c,'target',world)))
    def test_adapter_all_singleton_worlds(self):
        raw=example('ambiguous'); raw['horizon']=3; c=retry(raw); g=graph(expand(c))
        for R,B in all_retry_worlds(c):
            world=[sum(1<<i for i in R)]
            for e,allowed in enumerate(c['feedback']):
                acts=[a for a in (1,2) if allowed&a]
                world.append(sum(1<<j for j,a in enumerate(acts) if B[e]&a))
            actual={(tag,e,cost) for word,tag,e,cost in graph_traces(g,'source',world)}
            self.assertEqual(actual,retry_packets(c,R,B,3))
    def test_adapter_huge_rejected(self):
        with self.assertRaises(Unknown): expand(example('huge'))

if __name__=='__main__': unittest.main()

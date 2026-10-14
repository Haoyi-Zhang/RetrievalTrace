"""Required availability is not compulsory execution or fairness."""
import copy
import itertools
import unittest
from src.schema import Invalid, Unknown
from src.required_producer import produce
from src.required_replay import verify
from src.required_schema import admit, worlds
from tests.oracle import retry_packets, retry_refines

def declaration(adds=(1,2,3),required=(2,),failures=None,bits=2,horizon=5,feedback=None):
    return dict(protocol='required-outcomes-v1',required_outcomes=list(required),capsule=dict(
        bits=bits,initial=0,horizon=horizon,feedback=feedback or [1]*(1<<bits),
        outcomes=[dict(id=str(i),add=a,failure=(failures or [None]*len(adds))[i]) for i,a in enumerate(adds)],
        query_cost=[2,0,1],feedback_cost=[0,3,1]))

class RequiredContract(unittest.TestCase):
    def test_required_join_rescues_incomparability(self):
        x=declaration();self.assertEqual(verify(x,1,produce(x,1)),'valid')
        x['required_outcomes']=[];self.assertEqual(verify(x,1,produce(x,1)),'invalid')

    def test_matching_required_failure_and_label_boundary(self):
        x=declaration((1,0,1),(2,),[None,'f','f'],bits=1)
        self.assertEqual(verify(x,1,produce(x,1)),'valid')
        x['capsule']['outcomes'][2]['failure']='other'
        self.assertEqual(verify(x,1,produce(x,1)),'invalid')

    def test_presence_is_not_forced_selection(self):
        x=declaration((0,1,2,4),(0,),bits=3)
        p=produce(x,2);self.assertEqual(verify(x,2,p),'invalid')
        self.assertEqual(len(p['witness']['retrieval']),4)
        self.assertIn(0,p['witness']['retrieval'])

    def test_distance_positive_and_huge_horizon(self):
        x=declaration((0,3,5,6),(0,),bits=3,horizon=2**60)
        p=produce(x,2);self.assertEqual(p['mode'],'distance')
        self.assertEqual(verify(x,2,p),'valid')
        self.assertEqual(len(p['rows']),8)

    def test_strict_versioned_contract_and_binding(self):
        x=declaration();p=produce(x,1)
        for value in ([True],[2.0],[2,2],[3],None):
            y=copy.deepcopy(x);y['required_outcomes']=value
            with self.assertRaises(Invalid): produce(y,1)
        for key,value in [('protocol','unknown'),('required_outcomes',[]),('horizon',True)]:
            q=copy.deepcopy(p);q[key]=value
            with self.assertRaises(Invalid):verify(x,1,q)
        y=copy.deepcopy(x);y['extra']=0
        with self.assertRaises(Invalid):admit(y)
        with self.assertRaises(Invalid):admit(x['capsule'])

    def test_complete_world_rows_and_mutations(self):
        x=declaration((0,3,5,6),(0,),bits=3);p=produce(x,2)
        for kind in ('omit','duplicate','wrong-required','bool-world','parent'):
            q=copy.deepcopy(p)
            if kind=='omit':q['rows'].pop()
            elif kind=='duplicate':q['rows'][1]=q['rows'][0]
            elif kind=='wrong-required':q['required_outcomes']=[]
            elif kind=='bool-world':q['rows'][0]['retrieval']=[False]
            else:q['rows'][0]['parents'][0]=[0,0]
            with self.assertRaises(Invalid):verify(x,2,q)
        with self.assertRaises(Unknown):produce(x,2,max_worlds=7)
        with self.assertRaises(Unknown):verify(x,2,p,max_cells=63)

    def test_negative_replay_requires_all_mandatory_outcomes(self):
        x=declaration((0,1,2,4),(0,),bits=3);p=produce(x,2)
        p['witness']['retrieval'].remove(0)
        with self.assertRaises(Invalid):verify(x,2,p)

    def test_small_direct_operational_cost_oracle(self):
        for adds in itertools.product(range(2),repeat=2):
            for failures in itertools.product((None,'f'),repeat=2):
                for masks in itertools.product((1,2,3),repeat=2):
                    for required in ((),(0,),(1,),(0,1)):
                        x=declaration(adds,required,failures,bits=1,feedback=list(masks));c=admit(x)
                        truth=True
                        for R,B in worlds(c,1,all_feedback=True):
                            truth &= retry_refines(retry_packets(c,R,B,5),retry_packets(c,R,B,1))
                        self.assertEqual(verify(x,1,produce(x,1))=='valid',truth)

if __name__=='__main__':unittest.main()

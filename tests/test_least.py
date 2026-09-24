import copy,unittest
from pathlib import Path
from src.schema import load,Invalid
from src.cutoff_search import produce_least
from src.cutoff_replay import verify_least
from tests.oracle import all_retry_worlds,retry_packets,retry_refines
ROOT=Path(__file__).resolve().parents[1]
class LeastTests(unittest.TestCase):
    def example(self,name):return load(ROOT/'inputs/examples'/f'{name}.json')
    def check_case(self,name,want):
        c=self.example(name);p=produce_least(c);self.assertEqual(verify_least(c,p),want)
    def test_ordered(self):self.check_case('ordered',1)
    def test_distance(self):self.check_case('distance',2)
    def test_sharp(self):self.check_case('sharp',3)
    def test_huge(self):self.check_case('huge',2)
    def test_failure(self):self.check_case('failure',2)
    def test_identity(self):
        c=self.example('sharp');c['horizon']=1;self.assertEqual(verify_least(c,produce_least(c)),1)
    def mutate(self,field,value):
        c=self.example('distance');p=produce_least(c);p[field]=value
        with self.assertRaises((Invalid,TypeError,KeyError)):verify_least(c,p)
    def test_missing_lower(self):self.mutate('lower',None)
    def test_missing_upper(self):self.mutate('upper',None)
    def test_forged_cutoff(self):self.mutate('cutoff',3)
    def test_bool_cutoff(self):self.mutate('cutoff',True)
    def test_zero_cutoff(self):self.mutate('cutoff',0)
    def test_wrong_horizon(self):self.mutate('horizon',4)
    def test_extra_field(self):
        c=self.example('distance');p=produce_least(c);p['claimed_optimal']=True
        with self.assertRaises(Invalid):verify_least(c,p)
    def test_small_oracle(self):
        for name in ('ordered','distance','sharp','failure','ambiguous'):
            c=self.example(name);p=produce_least(c);K=verify_least(c,p)
            valid=[]
            for k in range(1,c['horizon']+1):
                valid.append(all(retry_refines(retry_packets(c,R,B,c['horizon']),retry_packets(c,R,B,k)) for R,B in all_retry_worlds(c)))
            self.assertEqual(K,valid.index(True)+1)
            self.assertEqual(valid,[i>=K for i in range(1,c['horizon']+1)])
if __name__=='__main__':unittest.main()

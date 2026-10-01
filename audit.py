#!/usr/bin/env python3
"""Check retained finite evidence consistency without network or paper files.

This is an integrity/reconciliation check, not a proof of the theorems.
"""
from __future__ import annotations
import csv,json,re,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
R=ROOT/'results/current'
def require(ok,message):
    if not ok:raise ValueError(message)
def js(name):return json.loads((R/name).read_text(encoding='utf8'))
def rows(name):
    with (R/name).open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
def main():
    totals={'contracts':0,'operational_executions':0,'cost_packet_equivalence_checks':0}
    for initial in range(4):
        rr=rows(f'grid-{initial}.csv'); report=js(f'grid-{initial}.json')
        require(len(rr)==20655==report['contracts'],'grid count')
        require({(int(x['signature']),int(x['feedback'])) for x in rr}=={(a,b) for a in range(1,256) for b in range(81)},'grid selection')
        require(all(int(x['initial'])==initial for x in rr),'grid entry evidence')
        require(not report['mismatches'],'grid mismatch')
        for k in totals:totals[k]+=report[k]
    require(totals==dict(contracts=82620,operational_executions=413100,cost_packet_equivalence_checks=826200),'grid totals')
    rr=rows('uniform-cutoffs.csv');c=js('cutoff.json')
    require(len(rr)==82620==c['contracts'],'uniform cutoff count')
    counts=[sum(int(x[f'K{k}']) for x in rr) for k in (1,2,3)]
    require(counts==[54300,80364,82620]==c['valid_uniform_cutoffs'],'uniform cutoff counts')
    require(all(int(x['K1'])<=int(x['K2'])<=int(x['K3']) for x in rr),'upper interval')
    require(c['adjacent_comparisons']==495720 and c['small_world_comparisons']==247860 and c['rank_comparisons']==529740,'cutoff comparison units')
    rr=rows('graph-pairs.csv');g=js('graphs.json')
    require(len(rr)==40804 and sum(int(x['valid']) for x in rr)==682,'graph decisions')
    require({(int(x['source']),int(x['target'])) for x in rr}=={(i,j) for i in range(202) for j in range(202)},'graph pair selection')
    require(len(js('graph-inputs.json')['programs'])==g['programs']==202,'graph input census')
    require(min(int(x['certificate_bytes']) for x in rr)==69 and max(int(x['certificate_bytes']) for x in rr)==843,'graph sizes')
    larger=js('larger-cases.json');l=js('larger.json');require(len(larger)==816,'larger count')
    for family,summary in l['families'].items():
        cases=[x for x in larger if x['family']==family]
        require(len(cases)==summary['cases'],'larger family count')
        require(sum(x['worlds'] for x in cases)==summary['world_comparisons'],'larger worlds')
        require(sum(x['status']=='valid' for x in cases)==summary['valid'],'larger verdicts')
        require([x['case'] for x in cases]==list(range(len(cases))),'larger inclusion order')
    require(sum(x['worlds'] for x in larger)==67744==l['world_comparisons'],'larger total worlds')
    ss=js('supports.json');require(ss['comparisons']==1048576 and ss['cover_search_checks']==4128 and ss['valid_covers']==989343,'support units')
    scaling=rows('encoding-scaling.csv');require(len(scaling)==12,'scaling rows')
    for x in scaling:
        h=int(x['horizon']);require(int(x['source_nodes'])==4*h+1 and int(x['source_paths'])==2**h,'scaling dimensions')
    require({k:int(v) for k,v in scaling[-1].items()}==js('scaling.json')['last'],'scaling summary')
    binary=js('binary-horizons.json')
    require(binary[-1]['horizon']==2**60,'binary horizon')
    require(all(x['worst_formula']==[x['horizon'],x['horizon']] and x['formula_branch']=='continuing-success' for x in binary),'binary symbolic formula')
    worst=js('worst-cost-branches.json')
    require(len(worst['cases'])==3 and not worst['mismatches'],'worst-cost branches')
    require(all(x['expected_worst']==x['operational_worst'] and x['jointly_attained'] for x in worst['cases']),'worst-cost trace comparison')
    erasure=js('observation-erasure.json')
    require(erasure['bits']==3 and erasure['target_horizon']==1,'erasure input')
    require(erasure['adjacent_after_erasure'] and not erasure['larger_after_erasure'] and not erasure['mismatches'],'erasure boundary')
    for filename in ('cutoff.json','larger.json','graphs.json','scaling.json','supports.json','examples.json'):
        require(not js(filename)['mismatches'],'retained mismatch '+filename)
    for filename in ('tests.log','optimized-tests.log'):
        text=(R/filename).read_text();require(re.search(r'Ran 100 tests',text) and text.rstrip().endswith('OK'),'unit result '+filename)
    with (ROOT/'literature/calibration.csv').open(newline='') as f:cal=list(csv.DictReader(f))
    toplas=[x for x in cal if 'TOPLAS' in x['group'].split(';')]
    adjacent=[x for x in cal if 'adjacent' in x['group'].split(';')]
    require(len(toplas)==12 and len(adjacent)==5 and len(cal)==17,'literature selection')
    require(statistics.median(int(x['reference_count']) for x in toplas)==40.5,'reference median')
    with (ROOT/'literature/influential-selection.csv').open(newline='') as f:influential=list(csv.DictReader(f))
    require(len(influential)==5 and {x['key'] for x in influential}<={x['key'] for x in cal},'influential full-text membership')
    with (ROOT/'literature/bibliography-audit.csv').open(newline='') as f:bib=list(csv.DictReader(f))
    require(len(bib)==44 and len({x['key'] for x in bib})==44,'bibliography identification')
    with (ROOT/'claim_evidence_ledger.csv').open(newline='') as f:ledger=list(csv.DictReader(f))
    for x in ledger:
        for field in ('proof_or_checker','source_or_test','raw_result'):
            for name in x[field].split(';'):
                if name and name!='not-applicable':require((ROOT/name).is_file(),'missing ledger evidence '+name)
    print(json.dumps({'status':'consistent','tests_each_mode':100,**totals,'graph_pairs':40804,'larger_worlds':67744,'scholarly_references':44,'toplas_sample':12,'adjacent_sample':5,'influential_sample':5},sort_keys=True))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError,KeyError,TypeError) as exc:print(str(exc),file=sys.stderr);sys.exit(1)

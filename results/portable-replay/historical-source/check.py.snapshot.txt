#!/usr/bin/env python3
"""Produce and replay one finite certificate. A valid counterexample exits 0."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from src.schema import Invalid,Unknown,load

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('kind',choices=['retry','graph','least']); ap.add_argument('input',type=Path)
    ap.add_argument('--cutoff',type=int,help='required for retry')
    ap.add_argument('--certificate',type=Path,help='replay supplied certificate instead of searching')
    ap.add_argument('--output',type=Path,help='write generated certificate')
    args=ap.parse_args(argv)
    try:
        raw=load(args.input)
        if args.kind=='retry':
            if args.cutoff is None: raise Invalid('--cutoff is required for retry')
            from src.retry_producer import produce
            from src.retry_replay import verify
            cert=load(args.certificate) if args.certificate else produce(raw,args.cutoff)
            status=verify(raw,args.cutoff,cert)
        elif args.kind=='least':
            from src.cutoff_search import produce_least
            from src.cutoff_replay import verify_least
            cert=load(args.certificate) if args.certificate else produce_least(raw)
            optimum=verify_least(raw,cert)
            status='least-valid'
        else:
            from src.graph_producer import produce
            from src.graph_replay import verify
            cert=load(args.certificate) if args.certificate else produce(raw)
            status=verify(raw,cert)
        if args.output:
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(cert,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
        result={'status':status,'certificate_checked':True,'kind':args.kind}
        if args.kind=='least':result['cutoff']=optimum
        print(json.dumps(result,sort_keys=True))
        return 0
    except Unknown as error:
        print(json.dumps({'status':'UNKNOWN','message':str(error)})); return 3
    except (Invalid,ValueError,KeyError,TypeError,IndexError,OSError,RecursionError) as error:
        print(json.dumps({'status':'malformed','message':str(error)}),file=sys.stderr); return 2
if __name__=='__main__': sys.exit(main())

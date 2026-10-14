"""Explicit required-outcome certificate CLI; owned finite inputs, no services."""
import argparse, json, sys
from src.schema import load, Invalid, Unknown
from src.required_producer import produce
from src.required_replay import verify

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['produce','verify'])
    p.add_argument('input');p.add_argument('cutoff',type=int);p.add_argument('--certificate');a=p.parse_args()
    try:
        raw=load(a.input)
        if a.action=='produce':
            cert=produce(raw,a.cutoff)
            verify(raw,a.cutoff,cert)
            print(json.dumps(cert,sort_keys=True))
        else:
            if not a.certificate:p.error('--certificate required for verify')
            print(verify(raw,a.cutoff,load(a.certificate)))
        return 0
    except Unknown as exc:print('UNKNOWN: '+str(exc),file=sys.stderr);return 2
    except Invalid as exc:print('MALFORMED: '+str(exc),file=sys.stderr);return 3

if __name__=='__main__':sys.exit(main())

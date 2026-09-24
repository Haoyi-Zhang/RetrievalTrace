"""Strict finite input admission shared by producer and consumer.

Sharing admission is part of the explicit trust boundary. Semantic search and
certificate replay are implemented separately. JSON integers never include bool.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class Invalid(ValueError):
    """Malformed input or certificate; not a semantic counterexample."""
class Unknown(RuntimeError):
    """An explicit resource ceiling was reached; no semantic conclusion."""

def require(condition: bool, message: str) -> None:
    if not condition:
        raise Invalid(message)

def integer(x: Any, name: str, low: int = 0, high: int | None = None) -> int:
    require(type(x) is int and x >= low and (high is None or x <= high),
            f'{name}: expected integer in [{low}, {high}]')
    return x

def vector(x: Any, name: str, length: int | None = None) -> list[int]:
    require(type(x) is list and len(x) > 0, f'{name}: nonempty vector required')
    if length is not None:
        require(len(x) == length, f'{name}: wrong vector dimension')
    return [integer(v, name) for v in x]

def load(path: str | Path) -> Any:
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, f'duplicate JSON key: {k}')
            out[k] = v
        return out
    with open(path, encoding='utf8') as stream:
        return json.load(stream, object_pairs_hook=pairs,
                         parse_constant=lambda s: (_ for _ in ()).throw(Invalid('nonfinite JSON number')))

def retry(x: Any) -> dict:
    require(type(x) is dict, 'retry declaration must be an object')
    n = integer(x.get('bits'), 'bits', 0, 12)
    e0 = integer(x.get('initial'), 'initial', 0, (1 << n)-1)
    H = integer(x.get('horizon'), 'horizon', 1)
    require(type(x.get('outcomes')) is list and 0 < len(x['outcomes']) <= 64,
            'outcomes: 1..64 entries required')
    outcomes, names = [], set()
    for o in x['outcomes']:
        require(type(o) is dict, 'outcome must be an object')
        name = o.get('id'); failure = o.get('failure')
        require(type(name) is str and name and name not in names, 'distinct nonempty outcome ids required')
        require(failure is None or (type(failure) is str and failure), 'failure: null or nonempty string')
        names.add(name)
        outcomes.append({'id': name, 'failure': failure,
                         'add': integer(o.get('add'), 'add', 0, (1 << n)-1)})
    if 'feedback' in x:
        require('predicate' not in x, 'choose feedback or predicate, not both')
        require(type(x['feedback']) is list and len(x['feedback']) == 1 << n,
                'feedback table must contain exactly 2**bits entries')
        feedback = [integer(v, 'feedback', 1, 3) for v in x['feedback']]
    else:
        pred = integer(x.get('predicate'), 'predicate', 0, (1 << (1 << n))-1)
        feedback = [2 if pred & (1 << e) else 1 for e in range(1 << n)]
    q = vector(x.get('query_cost', [1, 0]), 'query_cost')
    b = vector(x.get('feedback_cost', [0, 1]), 'feedback_cost', len(q))
    return dict(bits=n, initial=e0, horizon=H, outcomes=outcomes, feedback=feedback,
                query_cost=q, feedback_cost=b)

def graph(x: Any) -> dict:
    require(type(x) is dict, 'graph declaration must be an object')
    names = x.get('resources')
    require(type(names) is list and names and all(type(a) is str and a for a in names)
            and len(set(names)) == len(names), 'distinct resource names required')
    tokens = x.get('tokens', [])
    require(type(tokens) is list and len(tokens) <= 128, 'tokens: list of at most 128 origin labels')
    require(all(type(a) is str and a for a in tokens), 'token origins must be nonempty strings')
    full = (1 << len(tokens))-1
    initial = integer(x.get('initial', 0), 'initial', 0, full)
    labels = x.get('labels')
    require(type(labels) is list and labels and all(type(a) is str and a for a in labels)
            and len(set(labels)) == len(labels), 'distinct terminal labels required')
    modules = x.get('modules')
    require(type(modules) is list and len(modules) <= 32, 'modules: at most 32 keys')
    mods, keys = [], set()
    for m in modules:
        require(type(m) is dict, 'module must be an object')
        key = m.get('key')
        require(type(key) is str and key and key not in keys, 'distinct nominal module keys required')
        keys.add(key)
        adds = m.get('adds')
        require(type(adds) is list and 0 < len(adds) <= 32, 'nonempty finite module outcomes required')
        mods.append(dict(key=key, requires=integer(m.get('requires', 0), 'requires', 0, full),
                         adds=[integer(v, 'addition', 0, full) for v in adds],
                         cost=vector(m.get('cost'), 'module cost', len(names))))
    out = dict(resources=names, tokens=tokens, initial=initial, labels=labels, modules=mods)
    for side in ('source','target'):
        nodes = x.get(side)
        require(type(nodes) is list and 0 < len(nodes) <= 1000, 'program must have 1..1000 nodes')
        cleaned = []
        for i,node in enumerate(nodes):
            require(type(node) is dict, 'node must be an object')
            kind = node.get('kind')
            if kind == 'stop':
                require(node.get('label') in labels, 'undeclared terminal label')
                item = dict(kind=kind, label=node['label'], returned=integer(node.get('returned', 0), 'returned', 0, full))
            elif kind == 'emit':
                require(type(node.get('symbol')) is str, 'emit symbol must be a string')
                item = dict(kind=kind, symbol=node['symbol'], next=integer(node.get('next'), 'successor', i+1, len(nodes)-1))
            elif kind in ('call','choose'):
                nxt = node.get('next')
                require(type(nxt) is list and nxt, 'nonempty successors required')
                item = dict(kind=kind, next=[integer(j, 'successor', i+1, len(nodes)-1) for j in nxt])
                if kind == 'call':
                    k = integer(node.get('key'), 'key index', 0, len(mods)-1)
                    require(len(nxt) == len(mods[k]['adds']), 'one branch per module outcome required')
                    item['key'] = k
            else:
                raise Invalid('unknown node kind')
            cleaned.append(item)
        # Exact guaranteed-evidence admission; independent from trace enumeration.
        must = [None]*len(cleaned); must[0] = initial
        for i, node in enumerate(cleaned):
            if must[i] is None:
                continue
            e = must[i]
            if node['kind'] == 'stop':
                require(node['returned'] & ~e == 0, 'return uses unowned evidence')
                continue
            if node['kind'] == 'call':
                m = mods[node['key']]
                require(m['requires'] & ~e == 0, 'call uses unowned evidence')
                edges = zip(node['next'], m['adds'])
            else:
                edges = [(node['next'], 0)] if node['kind'] == 'emit' else [(j,0) for j in node['next']]
            for j,a in edges:
                value = e | a
                must[j] = value if must[j] is None else must[j] & value
        out[side] = cleaned
    return out

def path_budget(nodes: list[dict], limit: int) -> int:
    """Saturating path-count guard, computed before either census allocates paths."""
    ways=[0]*len(nodes)
    for i in range(len(nodes)-1,-1,-1):
        node=nodes[i]
        if node['kind']=='stop': ways[i]=1
        elif node['kind']=='emit': ways[i]=ways[node['next']]
        else: ways[i]=min(limit+1,sum(ways[j] for j in node['next']))
    if ways[0]>limit: raise Unknown(f'structural path count exceeds {limit}')
    return ways[0]

def identical(a: Any,b: Any) -> bool:
    """Structural equality without JSON bool/integer aliasing."""
    if type(a) is not type(b): return False
    if type(a) is dict:
        return a.keys()==b.keys() and all(identical(a[k],b[k]) for k in a)
    if type(a) is list:
        return len(a)==len(b) and all(identical(x,y) for x,y in zip(a,b))
    return a==b

"""Untimed pointwise conformance against the fixed, owned required-study corpus.

Usage: python -B native/check_managed_worlds.py NEW-WORLDS.csv NEW-DECISIONS.jsonl
The CLI reads only the fixed reference filenames under results/required; it
neither executes an interpreter nor follows paths supplied inside raw records.
Success requires all world keys, both packet counts, every relation, and all
contract decisions. Historical aggregate-only files are insufficient.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'results' / 'required'
WORLD_FIELDS = ('case', 'cutoff', 'retrieval_mask', 'feedback',
                'source_packets', 'target_packets', 'cost_relation')
PYTHON_FIELDS = WORLD_FIELDS + ('adjacent_relation',)
CENSUS = dict(cases=16208, contract_decisions=17232, worlds=294447,
              world_cutoff_checks=350141)
FAMILIES = {'one-bit-complete': (13104, 201600),
            'two-bit-join-complete': (2592, 65000),
            'seeded-49049': (512, 27847)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, name, low=0, high=None):
    require(type(value) is int and value >= low and
            (high is None or value <= high), name + ': invalid integer')
    return value


def fields(value, expected, name):
    require(type(value) is dict and set(value) == set(expected),
            name + ': wrong object fields')


def _pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def _constant(value):
    raise ValueError('nonfinite JSON value: ' + value)


def json_value(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)


def cases_from(stream, owned=False):
    """Admit finite campaign metadata; owned=True also enforces its full census."""
    cases = {}
    for line in stream:
        require(len(cases) < CENSUS['cases'], 'case ceiling exceeded')
        row = json_value(line)
        fields(row, ('case', 'family', 'input', 'worlds', 'results'), 'case')
        case = integer(row['case'], 'case', 0, CENSUS['cases'] - 1)
        require(case == len(cases), 'case IDs must be contiguous and unique')
        family = row['family']
        require(type(family) is str and family in FAMILIES, 'unknown owned family')
        declaration = row['input']
        fields(declaration, ('protocol', 'required_outcomes', 'capsule'), 'input')
        require(declaration['protocol'] == 'required-outcomes-v1', 'input protocol')
        c = declaration['capsule']
        fields(c, ('bits', 'initial', 'horizon', 'outcomes', 'feedback',
                   'query_cost', 'feedback_cost'), 'capsule')
        bits = integer(c['bits'], 'bits', 1, 4)
        integer(c['initial'], 'initial', 0, (1 << bits) - 1)
        integer(c['horizon'], 'horizon', 7, 7)
        require(type(c['outcomes']) is list and 1 <= len(c['outcomes']) <= 6,
                'owned outcome ceiling')
        for i, outcome in enumerate(c['outcomes']):
            fields(outcome, ('id', 'add', 'failure'), 'outcome')
            require(type(outcome['id']) is str and outcome['id'] == str(i), 'outcome ID')
            integer(outcome['add'], 'add', 0, (1 << bits) - 1)
            require(outcome['failure'] is None or
                    (type(outcome['failure']) is str and outcome['failure'] in ('f', 'g')),
                    'owned failure label')
        require(type(c['feedback']) is list and len(c['feedback']) == 1 << bits,
                'full feedback table required')
        for value in c['feedback']:
            integer(value, 'feedback', 1, 3)
        for name, expected in (('query_cost', [2, 0, 1]), ('feedback_cost', [0, 3, 1])):
            require(type(c[name]) is list and len(c[name]) == 3, name + ': dimension')
            for value in c[name]:
                integer(value, name)
            require(c[name] == expected, name + ': owned campaign charges')
        required = declaration['required_outcomes']
        require(type(required) is list, 'required outcomes must be a list')
        for value in required:
            integer(value, 'required outcome', 0, len(c['outcomes']) - 1)
        require(required == sorted(set(required)), 'required outcomes must be unique and increasing')
        masks = (1 << (len(c['outcomes']) - len(required))) - int(not required)
        worlds = masks * math.prod(3 if mask == 3 else 1 for mask in c['feedback'])
        integer(row['worlds'], 'worlds', 1, 567)
        require(row['worlds'] == worlds, 'case world cardinality: ' + str(case))
        require(type(row['results']) is list and 1 <= len(row['results']) <= 3,
                'cutoff result count')
        cutoffs, oracles = [], []
        for result in row['results']:
            fields(result, ('cutoff', 'status', 'oracle', 'legacy_unrestricted_collapse',
                            'certificate'), 'result')
            cutoffs.append(integer(result['cutoff'], 'cutoff', 1, c['horizon']))
            require(type(result['oracle']) is bool, 'oracle must be a JSON boolean')
            require(result['status'] in ('valid', 'invalid') and
                    (result['status'] == 'valid') == result['oracle'], 'case verdict')
            require(result['legacy_unrestricted_collapse'] is None or
                    type(result['legacy_unrestricted_collapse']) is bool, 'legacy verdict type')
            require(type(result['certificate']) is dict, 'certificate object required')
            oracles.append(result['oracle'])
        require(cutoffs == ([1, 2, 3] if family == 'seeded-49049' else [1]),
                'owned family cutoff set')
        require(bits == (1 if family == 'one-bit-complete' else 2) or
                (family == 'seeded-49049' and 2 <= bits <= 4), 'family bits')
        if owned:
            expected_family = ('one-bit-complete' if case < 13104 else
                               'two-bit-join-complete' if case < 15696 else 'seeded-49049')
            require(family == expected_family, 'owned family case range')
        cases[case] = dict(family=family, feedback=tuple(c['feedback']),
                           outcomes=len(c['outcomes']), required=sum(1 << i for i in required),
                           horizon=c['horizon'], worlds=worlds,
                           cutoffs=tuple(cutoffs), oracles=tuple(oracles))
    require(bool(cases), 'empty case corpus')
    if owned:
        require(census(cases) == CENSUS, 'owned corpus census mismatch')
        for family, (count, worlds) in FAMILIES.items():
            selected = [c for c in cases.values() if c['family'] == family]
            require(len(selected) == count and sum(c['worlds'] for c in selected) == worlds,
                    'owned family census: ' + family)
    return cases


def census(cases):
    return dict(cases=len(cases), contract_decisions=sum(len(c['cutoffs']) for c in cases.values()),
                worlds=sum(c['worlds'] for c in cases.values()),
                world_cutoff_checks=sum(c['worlds'] * len(c['cutoffs']) for c in cases.values()))


def decimal(value, name, low, high):
    require(type(value) is str and re.fullmatch(r'0|[1-9][0-9]*', value) is not None,
            name + ': canonical decimal required')
    require(len(value) <= len(str(high)), name + ': decimal ceiling')
    return integer(int(value), name, low, high)


def world_rows(stream, cases, python=False):
    reader = csv.reader(stream, strict=True)
    expected = PYTHON_FIELDS if python else WORLD_FIELDS
    require(tuple(next(reader, ())) == expected, 'world CSV header mismatch')
    limit = census(cases)['world_cutoff_checks']
    for index, row in enumerate(reader):
        require(index < limit, 'world row census exceeded')
        require(len(row) == len(expected), 'world row field count')
        case = decimal(row[0], 'case', 0, CENSUS['cases'] - 1)
        require(case in cases, 'unknown world case: ' + str(case))
        c = cases[case]
        cutoff = decimal(row[1], 'cutoff', 1, c['horizon'])
        require(cutoff in c['cutoffs'], 'unrequested cutoff')
        mask = decimal(row[2], 'retrieval_mask', 1, (1 << c['outcomes']) - 1)
        require(mask & c['required'] == c['required'], 'required outcome omitted')
        feedback = row[3]
        require(len(feedback) == len(c['feedback']) and all(
            char in '123' and int(char) & ~allowed == 0
            for char, allowed in zip(feedback, c['feedback'])), 'inadmissible full feedback coordinate')
        bound = c['horizon'] * len(c['feedback']) * (c['outcomes'] + 2)
        source = decimal(row[4], 'source_packets', 1, bound)
        target = decimal(row[5], 'target_packets', 1, bound)
        require(row[6] in ('0', '1'), 'cost_relation must be 0 or 1')
        if python:
            require(row[7] in ('0', '1') and row[7] == row[6], 'Python pointwise adjacency mismatch')
        yield (case, cutoff, mask, feedback), (source, target, row[6] == '1')


def reference_from(cases, stream):
    reference, counts, conjunctions, sources = {}, {}, {}, {}
    for key, value in world_rows(stream, cases, python=True):
        require(key not in reference, 'duplicate Python world key: ' + repr(key))
        reference[key] = value
        pair = key[:2]
        counts[pair] = counts.get(pair, 0) + 1
        conjunctions[pair] = conjunctions.get(pair, True) and value[2]
        world = (key[0], key[2], key[3])
        require(world not in sources or sources[world] == value[0],
                'inconsistent Python source packet count: ' + repr(world))
        sources[world] = value[0]
    # All keys are admitted and unique. Equality to the independently computed
    # domain cardinality per cutoff proves complete coverage, not an aggregate
    # approximation to verdict agreement.
    for case, c in cases.items():
        for cutoff, oracle in zip(c['cutoffs'], c['oracles']):
            pair = (case, cutoff)
            require(counts.get(pair, 0) == c['worlds'], 'incomplete Python world census: ' + repr(pair))
            require(conjunctions[pair] == oracle, 'Python contract conjunction: ' + repr(pair))
    return reference


def compare(cases, reference, managed_worlds, managed_decisions):
    seen = set()
    for key, value in world_rows(managed_worlds, cases):
        require(key not in seen, 'duplicate managed world key: ' + repr(key))
        require(key in reference, 'unknown managed world key: ' + repr(key))
        require(value == reference[key], 'pointwise mismatch at ' + repr(key) +
                ': expected ' + repr(reference[key]) + ', received ' + repr(value))
        seen.add(key)
    if len(seen) != len(reference):
        raise ValueError('missing managed world key: ' + repr(min(reference.keys() - seen)))
    ids = set()
    for line in managed_decisions:
        row = json_value(line)
        fields(row, ('id', 'worlds', 'valid'), 'managed contract')
        case = integer(row['id'], 'managed id', 0, CENSUS['cases'] - 1)
        require(case in cases and case not in ids, 'unknown or duplicate managed case')
        c = cases[case]
        integer(row['worlds'], 'managed worlds', 1, 567)
        require(row['worlds'] == c['worlds'], 'managed case world count')
        valid = row['valid']
        require(type(valid) is list and len(valid) == len(c['cutoffs']) and
                all(type(value) is bool for value in valid), 'managed verdicts must be JSON booleans')
        require(tuple(valid) == c['oracles'], 'managed contract verdict mismatch')
        ids.add(case)
    require(len(ids) == len(cases), 'missing managed contract rows')
    return dict(census(cases), pointwise_relations_compared=len(seen),
                packet_count_pairs_compared=len(seen), mismatches=0)


def binding(path):
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return dict(bytes=size, sha256=digest.hexdigest())


def load_reference():
    summary = json_value((REFERENCE / 'summary.json').read_text(encoding='utf8'))
    require(type(summary) is dict and summary.get('protocol') == 'required-outcomes-v1', 'summary protocol')
    for name, expected in (('contracts', 16208), ('decisions', 17232), ('world_decision_checks', 350141)):
        integer(summary.get(name), 'summary ' + name, expected, expected)
    require(type(summary.get('files')) is dict, 'summary file bindings')
    bindings = {}
    # These literal filenames, not raw-record paths, are the only reference inputs.
    for name in ('cases.jsonl', 'world-checks.csv'):
        expected = summary['files'].get(name)
        fields(expected, ('bytes', 'sha256'), 'reference file binding')
        integer(expected['bytes'], 'reference bytes', 1)
        bindings[name] = binding(REFERENCE / name)
        require(bindings[name] == expected, 'reference file binding mismatch: ' + name)
    with (REFERENCE / 'cases.jsonl').open(encoding='utf8') as stream:
        cases = cases_from(stream, owned=True)
    with (REFERENCE / 'world-checks.csv').open(encoding='utf8', newline='') as stream:
        reference = reference_from(cases, stream)
    return cases, reference, bindings


def source_receipt(receipt, bindings):
    """Check standalone bindings or scientific_binding within a process receipt.

    Other envelope fields are preserved by the main owner, not interpreted here.
    The digest payload contains no paths; no executable is ever run.
    """
    if type(receipt) is dict and 'scientific_binding' in receipt:
        receipt = receipt['scientific_binding']
    fields(receipt, ('schema', *bindings), 'source-binding receipt')
    require(receipt['schema'] == 'owned-retry-pointwise-files-v1', 'receipt schema')
    for name, expected in bindings.items():
        value = receipt[name]
        require(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
                'receipt digest type: ' + name)
        require(value == expected, 'receipt binding mismatch: ' + name)
    return 'matched-file-bindings; compilation and execution provenance remain main-owned'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('managed_worlds', type=Path)
    parser.add_argument('managed_decisions', type=Path)
    parser.add_argument('--source-binding-receipt', type=Path)
    parser.add_argument('--managed-executable', type=Path, help='hashed only; never executed')
    args = parser.parse_args(argv)
    if bool(args.source_binding_receipt) != bool(args.managed_executable):
        parser.error('receipt and managed-executable must be supplied together')
    try:
        cases, reference, raw_bindings = load_reference()
        with args.managed_worlds.open(encoding='utf8', newline='') as worlds, \
                args.managed_decisions.open(encoding='utf8') as decisions:
            report = compare(cases, reference, worlds, decisions)
        bindings = dict(source_sha256=binding(Path(__file__).with_name('OwnedRetry.cs'))['sha256'],
                        cases_sha256=raw_bindings['cases.jsonl']['sha256'],
                        python_worlds_sha256=raw_bindings['world-checks.csv']['sha256'],
                        managed_worlds_sha256=binding(args.managed_worlds)['sha256'],
                        managed_decisions_sha256=binding(args.managed_decisions)['sha256'])
        source_binding = 'not supplied; file digests alone do not establish a compiled run'
        if args.source_binding_receipt:
            bindings['executable_sha256'] = binding(args.managed_executable)['sha256']
            receipt = json_value(args.source_binding_receipt.read_text(encoding='utf8'))
            source_binding = source_receipt(receipt, bindings)
        report.update(status='pointwise-match', bindings=bindings, source_binding=source_binding,
                      scope='Untimed keyed conformance to retained Python worlds; no new measurement or packet-set proof')
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ValueError, OSError, csv.Error) as error:
        print(json.dumps(dict(status='rejected', error=str(error)), sort_keys=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

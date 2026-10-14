"""Untimed checker regressions, not a C# run or a performance measurement."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from native import check_managed_worlds as checker
from tests.oracle import all_retry_worlds, retry_packets, retry_refines


def csv_stream(rows, fields=checker.WORLD_FIELDS):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(fields)
    writer.writerows(rows)
    stream.seek(0)
    return stream


def json_stream(rows):
    return io.StringIO(''.join(json.dumps(row) + '\n' for row in rows))


def fixtures():
    """Two reviewed tiny contracts with unrestricted feedback and several failures.

    Only the existing direct Python packet oracle is executed, on 33 worlds.
    At least two distinct worlds fail the first contract, enabling the masked
    conjunction regression. No campaign, producer, compiler, or clocks run.
    """
    records, python_rows, managed_rows, decisions = [], [], [], []
    for case, required in enumerate(([], [2])):
        capsule = dict(bits=2, initial=0, horizon=7, feedback=[1, 1, 1, 3],
                       outcomes=[dict(id=str(i), add=add, failure=None)
                                 for i, add in enumerate((1, 2, 3))],
                       query_cost=[2, 0, 1], feedback_cost=[0, 3, 1])
        cutoffs = [1] if case == 0 else [1, 2, 3]
        truth = [True] * len(cutoffs)
        count = 0
        for retrieval, feedback in all_retry_worlds(capsule):
            if not set(required) <= set(retrieval):
                continue
            count += 1
            source = retry_packets(capsule, retrieval, feedback, 7)
            for j, cutoff in enumerate(cutoffs):
                target = retry_packets(capsule, retrieval, feedback, cutoff)
                relation = retry_refines(source, target)
                adjacent = retry_refines(retry_packets(capsule, retrieval, feedback, cutoff + 1), target)
                truth[j] &= relation
                row = [case, cutoff, sum(1 << i for i in retrieval), ''.join(map(str, feedback)),
                       len(source), len(target), int(relation)]
                managed_rows.append(row)
                python_rows.append(row + [int(adjacent)])
        results = [dict(cutoff=cutoff, status='valid' if valid else 'invalid', oracle=valid,
                        legacy_unrestricted_collapse=None, certificate={})
                   for cutoff, valid in zip(cutoffs, truth)]
        records.append(dict(case=case, family='two-bit-join-complete' if case == 0 else 'seeded-49049',
                            input=dict(protocol='required-outcomes-v1', required_outcomes=required,
                                       capsule=capsule), worlds=count, results=results))
        decisions.append(dict(id=case, worlds=count, valid=truth))
    return records, python_rows, managed_rows, decisions


class ManagedWorldCheckerTests(unittest.TestCase):
    def setUp(self):
        self.records, self.python_rows, self.rows, self.decisions = fixtures()
        self.cases = checker.cases_from(json_stream(self.records))
        self.reference = checker.reference_from(self.cases, csv_stream(self.python_rows, checker.PYTHON_FIELDS))

    def compare(self, rows=None, decisions=None, fields=checker.WORLD_FIELDS):
        return checker.compare(self.cases, self.reference,
                               csv_stream(self.rows if rows is None else rows, fields),
                               json_stream(self.decisions if decisions is None else decisions))

    def test_complete_keyed_comparison_and_counts(self):
        result = self.compare()
        self.assertEqual(result['cases'], 2)
        self.assertEqual(result['contract_decisions'], 4)
        self.assertEqual(result['worlds'], 33)
        self.assertEqual(result['world_cutoff_checks'], 57)
        self.assertEqual(result['pointwise_relations_compared'], 57)
        self.assertEqual(result['packet_count_pairs_compared'], 57)
        self.assertEqual(result['mismatches'], 0)

    def test_matching_is_by_full_key_not_stream_order(self):
        self.assertEqual(self.compare(), self.compare(list(reversed(self.rows)), list(reversed(self.decisions))))

    def test_flipped_world_in_already_invalid_contract_is_rejected(self):
        rows = copy.deepcopy(self.rows)
        failing = [i for i, row in enumerate(rows) if row[0] == 0 and row[6] == 0]
        self.assertGreaterEqual(len(failing), 2)
        self.assertFalse(self.decisions[0]['valid'][0])
        rows[failing[0]][6] = 1
        self.assertFalse(all(row[6] for row in rows if row[0] == 0))
        # Aggregates still match exactly; pointwise admission must fail.
        with self.assertRaisesRegex(ValueError, 'pointwise mismatch at'):
            self.compare(rows)

    def test_packet_counts_are_compared_individually(self):
        for index in (4, 5):
            with self.subTest(index=index):
                rows = copy.deepcopy(self.rows)
                rows[0][index] += 1
                with self.assertRaisesRegex(ValueError, 'pointwise mismatch at'):
                    self.compare(rows)

    def test_missing_and_duplicate_worlds_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing managed world key'):
            self.compare(self.rows[:-1])
        rows = copy.deepcopy(self.rows)
        rows[1] = rows[0]
        with self.assertRaisesRegex(ValueError, 'duplicate managed world key'):
            self.compare(rows)

    def test_extra_world_rejected(self):
        with self.assertRaisesRegex(ValueError, 'world row census exceeded'):
            self.compare(self.rows + [self.rows[0]])

    def test_strict_world_header_and_width(self):
        for fields in (checker.PYTHON_FIELDS, checker.WORLD_FIELDS[:-1],
                       checker.WORLD_FIELDS + ('case',), ('id', 'worlds', 'valid')):
            with self.subTest(fields=fields), self.assertRaisesRegex(ValueError, 'header mismatch'):
                self.compare(fields=fields)
        for row in (self.rows[0][:-1], self.rows[0] + ['extra']):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, 'field count'):
                self.compare([row] + self.rows[1:])

    def test_strict_decimal_and_relation_cells(self):
        for index in (0, 1, 2, 4, 5):
            for value in (True, False, '1.0', '01', '+1', '-1', ' 1', '1 ', '', '1e0'):
                with self.subTest(index=index, value=value):
                    rows = copy.deepcopy(self.rows)
                    rows[0][index] = value
                    with self.assertRaises(ValueError):
                        self.compare(rows)
        for value in (True, False, 'true', 'false', '2', '', '1.0'):
            with self.subTest(relation=value):
                rows = copy.deepcopy(self.rows)
                rows[0][6] = value
                with self.assertRaises(ValueError):
                    self.compare(rows)

    def test_foreign_keys_and_finite_bounds(self):
        for index, value in ((0, 16208), (0, 2), (1, 2), (2, 0), (2, 8),
                             (4, 0), (5, 0), (4, 10**100), (5, 10**100)):
            with self.subTest(index=index, value=value):
                rows = copy.deepcopy(self.rows)
                rows[0][index] = value
                with self.assertRaises(ValueError):
                    self.compare(rows)

    def test_full_feedback_including_unvisited_cells_is_a_key(self):
        for value in ('111', '11111', '1110', '1114', '2111', '111True'):
            with self.subTest(feedback=value):
                rows = copy.deepcopy(self.rows)
                rows[0][3] = value
                with self.assertRaisesRegex(ValueError, 'full feedback coordinate'):
                    self.compare(rows)

    def test_required_retrieval_outcome_cannot_be_omitted(self):
        rows = copy.deepcopy(self.rows)
        index = next(i for i, row in enumerate(rows) if row[0] == 1)
        rows[index][2] = 1
        with self.assertRaisesRegex(ValueError, 'required outcome omitted'):
            self.compare(rows)

    def test_aggregate_only_is_not_a_conformance_input(self):
        with self.assertRaises(ValueError):
            checker.compare(self.cases, self.reference, json_stream(self.decisions), json_stream(self.decisions))

    def test_strict_managed_contract_schema_and_types(self):
        for field, value in (('id', False), ('id', 0.0), ('worlds', True), ('worlds', 21.0),
                             ('valid', [0]), ('valid', [0.0]), ('valid', False),
                             ('valid', [False, False]), ('valid', [True])):
            with self.subTest(field=field, value=value):
                decisions = copy.deepcopy(self.decisions)
                decisions[0][field] = value
                with self.assertRaises(ValueError):
                    self.compare(decisions=decisions)
        decisions = copy.deepcopy(self.decisions)
        decisions[0]['extra'] = 1
        with self.assertRaisesRegex(ValueError, 'wrong object fields'):
            self.compare(decisions=decisions)

    def test_contract_count_and_uniqueness(self):
        for decisions in (self.decisions[:-1], [self.decisions[0]] * 2,
                          self.decisions + [self.decisions[0]]):
            with self.subTest(decisions=decisions), self.assertRaises(ValueError):
                self.compare(decisions=decisions)
        decisions = copy.deepcopy(self.decisions)
        decisions[0]['worlds'] -= 1
        with self.assertRaisesRegex(ValueError, 'managed case world count'):
            self.compare(decisions=decisions)

    def test_duplicate_json_fields_and_nonfinite_values(self):
        for text in ('{"id":0,"id":0,"worlds":21,"valid":[false]}\n',
                     '{"id":NaN,"worlds":21,"valid":[false]}\n',
                     '{"id":Infinity,"worlds":21,"valid":[false]}\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                checker.compare(self.cases, self.reference, csv_stream(self.rows), io.StringIO(text))

    def test_reference_also_requires_complete_unique_keys(self):
        rows = copy.deepcopy(self.python_rows)
        rows[1] = rows[0]
        with self.assertRaisesRegex(ValueError, 'duplicate Python world key'):
            checker.reference_from(self.cases, csv_stream(rows, checker.PYTHON_FIELDS))
        with self.assertRaisesRegex(ValueError, 'incomplete Python world census'):
            checker.reference_from(self.cases, csv_stream(self.python_rows[:-1], checker.PYTHON_FIELDS))

    def test_reference_adjacency_and_conjunction(self):
        rows = copy.deepcopy(self.python_rows)
        rows[0][7] = 1 - rows[0][6]
        with self.assertRaisesRegex(ValueError, 'Python pointwise adjacency mismatch'):
            checker.reference_from(self.cases, csv_stream(rows, checker.PYTHON_FIELDS))
        rows = copy.deepcopy(self.python_rows)
        for row in rows:
            if row[0] == 0:
                row[6] = row[7] = 1
        with self.assertRaisesRegex(ValueError, 'Python contract conjunction'):
            checker.reference_from(self.cases, csv_stream(rows, checker.PYTHON_FIELDS))

    def test_case_admission_remains_strict_without_asserts(self):
        for field, value in (('case', False), ('case', 0.0), ('worlds', True),
                             ('worlds', 21.0), ('worlds', 20), ('family', '../foreign')):
            with self.subTest(field=field, value=value):
                records = copy.deepcopy(self.records)
                records[0][field] = value
                with self.assertRaises(ValueError):
                    checker.cases_from(json_stream(records))
        for field, value in (('bits', True), ('bits', 12), ('horizon', 2**60),
                             ('feedback', [1]), ('query_cost', [True, 0, 1])):
            with self.subTest(field=field, value=value):
                records = copy.deepcopy(self.records)
                records[0]['input']['capsule'][field] = value
                with self.assertRaises(ValueError):
                    checker.cases_from(json_stream(records))
        records = copy.deepcopy(self.records)
        records[0]['input']['required_outcomes'] = [True]
        with self.assertRaises(ValueError):
            checker.cases_from(json_stream(records))
        records = copy.deepcopy(self.records)
        records[0]['results'][0]['oracle'] = 0
        with self.assertRaisesRegex(ValueError, 'JSON boolean'):
            checker.cases_from(json_stream(records))

    def test_owned_mode_cannot_accept_fixture_as_complete_corpus(self):
        with self.assertRaises(ValueError):
            checker.cases_from(json_stream(self.records), owned=True)

    def test_optional_receipt_is_strict_file_binding_not_compiler_attestation(self):
        bindings = {name: str(i) * 64 for i, name in enumerate(
                    ('source_sha256', 'executable_sha256', 'cases_sha256', 'python_worlds_sha256',
                     'managed_worlds_sha256', 'managed_decisions_sha256'))}
        receipt = dict(schema='owned-retry-pointwise-files-v1', **bindings)
        self.assertIn('remain main-owned', checker.source_receipt(receipt, bindings))
        envelope = dict(version='main-owned-operational-receipt', scientific_binding=receipt,
                        process_records={'not_interpreted_by_checker': True})
        self.assertEqual(checker.source_receipt(envelope, bindings), checker.source_receipt(receipt, bindings))
        with self.assertRaises(ValueError):
            checker.source_receipt(dict(envelope, scientific_binding=False), bindings)
        for name in bindings:
            for value in (True, 0, bindings[name].upper() + 'x', 'f' * 64):
                with self.subTest(name=name, value=value):
                    mutated = dict(receipt, **{name: value})
                    with self.assertRaises(ValueError):
                        checker.source_receipt(mutated, bindings)
        with self.assertRaises(ValueError):
            checker.source_receipt(dict(receipt, source_path='../foreign'), bindings)


class RetainedCensusTests(unittest.TestCase):
    def test_all_350141_keys_with_synthetic_projection_not_managed_execution(self):
        cases, reference, bindings = checker.load_reference()

        def projection(flipped=None):
            yield ','.join(checker.WORLD_FIELDS) + '\n'
            with (checker.REFERENCE / 'world-checks.csv').open(encoding='utf8', newline='') as stream:
                rows = csv.reader(stream)
                next(rows)
                for row in rows:
                    if (int(row[0]), int(row[1]), int(row[2]), row[3]) == flipped:
                        row[6] = '1'
                    yield ','.join(row[:-1]) + '\n'

        # Deliberately synthetic managed-shaped rows test the comparator's entire
        # retained census. They are NOT evidence of a new managed interpreter run.
        with (checker.REFERENCE / 'managed-world-decisions.jsonl').open(encoding='utf8') as decisions:
            result = checker.compare(cases, reference, projection(), decisions)
        self.assertEqual(len(reference), 350141)
        self.assertEqual({name: result[name] for name in checker.CENSUS}, checker.CENSUS)
        self.assertEqual(result['pointwise_relations_compared'], 350141)
        self.assertEqual(result['packet_count_pairs_compared'], 350141)
        self.assertEqual(set(bindings), {'cases.jsonl', 'world-checks.csv'})
        # Also exercise the masking bug at a genuine retained coordinate, still
        # with a deliberately synthetic candidate and no managed execution.
        failures = {}
        for key, value in reference.items():
            if not value[2]:
                failures[key[:2]] = failures.get(key[:2], 0) + 1
        flipped = next(key for key, value in reference.items()
                       if not value[2] and failures[key[:2]] >= 2)
        c = cases[flipped[0]]
        self.assertFalse(c['oracles'][c['cutoffs'].index(flipped[1])])
        self.assertGreaterEqual(failures[flipped[:2]] - 1, 1)
        with (checker.REFERENCE / 'managed-world-decisions.jsonl').open(encoding='utf8') as decisions:
            with self.assertRaisesRegex(ValueError, 'pointwise mismatch at'):
                checker.compare(cases, reference, projection(flipped), decisions)


class CommandLineTests(unittest.TestCase):
    def test_cli_exit_status_report_and_rejection_with_owned_tiny_fixtures(self):
        records, python_rows, rows, decisions = fixtures()
        cases = checker.cases_from(json_stream(records))
        reference = checker.reference_from(cases, csv_stream(python_rows, checker.PYTHON_FIELDS))
        # The loader is replaced only in this CLI unit test; the real CLI has no
        # override for the fixed full corpus. No historical result is written.
        raw_bindings = {name: dict(sha256='0' * 64)
                        for name in ('cases.jsonl', 'world-checks.csv')}
        with tempfile.TemporaryDirectory() as directory:
            worlds = Path(directory) / 'synthetic-worlds.csv'
            aggregate = Path(directory) / 'synthetic-decisions.jsonl'
            worlds.write_text(csv_stream(rows).getvalue(), encoding='utf8', newline='')
            aggregate.write_text(json_stream(decisions).getvalue(), encoding='utf8')
            with patch.object(checker, 'load_reference', return_value=(cases, reference, raw_bindings)):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(checker.main([str(worlds), str(aggregate)]), 0)
                report = json.loads(output.getvalue())
                self.assertEqual(report['pointwise_relations_compared'], 57)
                self.assertEqual(report['status'], 'pointwise-match')
                self.assertIn('do not establish a compiled run', report['source_binding'])
                self.assertEqual(report['bindings']['managed_worlds_sha256'], checker.binding(worlds)['sha256'])
                error = io.StringIO()
                with redirect_stderr(error):
                    self.assertEqual(checker.main([str(aggregate), str(aggregate)]), 1)
                self.assertEqual(json.loads(error.getvalue())['status'], 'rejected')

    def test_receipt_requires_explicit_executable_not_a_raw_record_path(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as failure:
            checker.main(['unused-worlds', 'unused-decisions', '--source-binding-receipt', 'unused-receipt'])
        self.assertEqual(failure.exception.code, 2)


if __name__ == '__main__':
    unittest.main()

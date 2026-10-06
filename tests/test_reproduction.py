"""Owned synthetic failure-path tests; mocks are not campaign measurements."""
import json,pathlib,subprocess,tempfile,types,unittest
from unittest.mock import patch
import reproduce

class RunnerEvidenceTests(unittest.TestCase):
    def check_failure(self,output,timeout=True):
        usage=types.SimpleNamespace(ru_utime=0,ru_stime=0,ru_maxrss=0)
        resources=types.SimpleNamespace(RUSAGE_CHILDREN=0,getrusage=lambda _:usage)
        failure=(subprocess.TimeoutExpired(['owned-task'],0.01,output=output)
                 if timeout else subprocess.CompletedProcess(['owned-task'],7,stdout=output))
        options={'side_effect':failure} if timeout else {'return_value':failure}
        with tempfile.TemporaryDirectory() as directory:
            out=pathlib.Path(directory)
            with patch.object(reproduce,'resource',resources), \
                 patch.dict(reproduce.GROUPS,{'owned':[('tests',)]}), \
                 patch.object(reproduce.subprocess,'run',**options) as child:
                with self.assertRaises(RuntimeError):reproduce.run('owned',out,False)
                child.assert_called_once()
            log=(out/'tests.log').read_text(encoding='utf8')
            record=json.loads((out/'execution-owned.json').read_text(encoding='utf8'))
            expected=output or ''
            if isinstance(expected,bytes):expected=expected.decode('utf8',errors='replace')
            self.assertEqual(log,expected)
            self.assertEqual(len(record),1)
            self.assertEqual(record[0]['exit_code'],124 if timeout else 7)
            self.assertEqual(record[0].get('timed_out',False),timeout)

    def test_timeout_preserves_bytes(self):self.check_failure(b'owned partial output\n')
    def test_timeout_preserves_text(self):self.check_failure('owned partial output\n')
    def test_timeout_preserves_unicode(self):self.check_failure('evidence: \u03bb\n'.encode('utf8'))
    def test_timeout_without_output_still_records_failure(self):self.check_failure(None)
    def test_timeout_with_invalid_utf8_retains_replacement(self):self.check_failure(b'owned \xff\n')
    def test_nonzero_child_preserves_output_and_fail_gate(self):self.check_failure('owned failure\n',False)

if __name__=='__main__':unittest.main()

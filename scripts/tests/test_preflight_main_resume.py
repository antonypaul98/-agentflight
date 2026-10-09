"""Defensive regressions for post-merge checkpoint resumability."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'session_preflight.py'


def load_preflight():
    spec = importlib.util.spec_from_file_location('agentflight_preflight_under_test', SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MergedCheckpointResumeTests(unittest.TestCase):
    def exercise(self, active_branch):
        m = load_preflight()
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'CHECKPOINT_STATE.json').write_text(json.dumps({
                'repository': 'owner/repo', 'active_branch': active_branch,
                'checkpoint_status': 'MERGED_AND_VERIFIED'}))
            (root / '.python-version').write_text(f'{sys.version_info.major}.{sys.version_info.minor}')

            def run(args):
                calls.append(args)
                if 'get-url' in args:
                    return 'https://github.com/owner/repo.git'
                if args[:2] == ['git', 'for-each-ref']:
                    return args[-1]
                if args[:3] == ['git', 'branch', '--show-current']:
                    return 'main'
                if args[:2] == ['git', 'rev-list']:
                    return '0 0'
                if args[:2] == ['git', 'status']:
                    return ''
                if args[:2] == ['gh', 'api']:
                    return 'true'
                if '--git-path' in args:
                    return str(root / 'preflight-receipt.json')
                return 'a' * 40

            with patch.object(m, 'ROOT', root), patch.object(m, 'run', run), patch.object(m.shutil, 'which', return_value='/usr/bin/gh'), contextlib.redirect_stdout(io.StringIO()):
                try:
                    m.main()
                except m.PreflightFailure as exc:
                    return exc.receipt, calls
        return None, calls

    def test_merged_checkpoint_on_main_preserves_main_and_checks_push(self):
        receipt, calls = self.exercise('main')
        self.assertIsNone(receipt)
        self.assertTrue(any(a[:3] == ['git', 'push', '--dry-run'] and a[-1] == 'HEAD:refs/heads/main' for a in calls))

    def test_merged_checkpoint_stale_branch_rejected_before_fetch(self):
        receipt, calls = self.exercise('work/af20-bounded-tool-call-envelope')
        self.assertIn('stale active_branch', receipt['BLOCKER'])
        self.assertIn('set active_branch to main', receipt['NEXT_ACTION'])
        self.assertFalse(any(a[:2] == ['git', 'fetch'] for a in calls))


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""Offline adoption-preparation checks; never contacts a host or deploys.

Run: uv run --with PyYAML==6.0.3 python q5m/test_production_contract.py
All tests are bounded and repeatable. Mock call logs live in auto-cleaned temp dirs.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parent.parent


def read(name):
    return (ROOT / name).read_text()


class ProductionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load(read('q5m.yaml'))
        # BaseLoader preserves GitHub's YAML 1.2 'on' key as text.
        cls.workflow = yaml.load(read('.github/workflows/deploy-production.yml'), Loader=yaml.BaseLoader)
        cls.job = cls.workflow['jobs']['deploy']
        cls.steps = cls.job['steps']
        cls.commands = [step['run'] for step in cls.steps if 'run' in step]

    def test_binding_and_unchanged_runtime(self):
        self.assertEqual(self.manifest['version'], 2)
        self.assertEqual(self.manifest['name'], 'erdos-193')
        self.assertEqual(self.manifest['production'], {
            'node': 'q5m-n03', 'hostname': 'erdos-193.q5m.ai'})
        self.assertEqual(self.manifest['release'], {
            'adapter': 'compose', 'compose': 'q5m/compose.yaml',
            'contract': 'q5m/app.env', 'health': '/.q5m-release'})
        self.assertNotIn('environments', self.manifest)
        self.assertEqual(read('q5m/app.env').splitlines(),
                         ['Q5M_APP=erdos-193', 'Q5M_INGRESS_PORTS=8193/tcp'])
        site = yaml.safe_load(read('q5m/compose.yaml'))['services']['site']
        self.assertEqual(site['ports'], [{'target': 8193, 'published': '8193',
                                         'host_ip': '0.0.0.0', 'protocol': 'tcp'}])
        self.assertEqual(site['build']['dockerfile'], 'q5m/Dockerfile')
        self.assertTrue(site['image'].startswith('q5m/erdos-193:${Q5M_RELEASE:'))
        self.assertIn('FROM nginxinc/nginx-unprivileged:', read('q5m/Dockerfile'))
        self.assertIn('/.q5m-release', read('q5m/nginx.conf'))
        dockerfile = read('q5m/Dockerfile')
        self.assertIn('COPY viz/ /usr/share/nginx/html/', dockerfile)
        self.assertIn('COPY results/ /usr/share/nginx/html/family/', dockerfile)

    def test_dev_build_stay_separate(self):
        self.assertEqual(self.manifest['development'], {
            'command': ['python3', 'q5m/serve_site.py'], 'health': '/index.html'})
        self.assertEqual(self.manifest['build'], {
            'command': ['python3', 'q5m/build_site.py'], 'output': 'build/q5m-site'})
        for text in self.commands + [read('q5m/Dockerfile'), read('q5m/compose.yaml')]:
            for forbidden in ['serve_site.py', 'build_site.py', 'build/q5m-site']:
                self.assertNotIn(forbidden, text)

    def test_trusted_runner_and_exact_revision(self):
        self.assertEqual(self.workflow['permissions'], {'contents': 'read'})
        self.assertEqual(self.workflow['on']['push']['branches'], ['main'])
        self.assertEqual(self.workflow['concurrency']['cancel-in-progress'], 'false')
        self.assertEqual(self.job['needs'], 'validate')
        self.assertEqual(self.job['environment'], 'production')
        self.assertEqual(self.job['runs-on'], ['self-hosted', 'Linux', 'X64', 'erdos-193-deploy'])
        guard = self.job['if']
        for required in ["github.repository == 'ekalvi/erdos-193'",
                         "github.ref == 'refs/heads/main'",
                         "github.event_name == 'push'", "github.event_name == 'workflow_dispatch'"]:
            self.assertIn(required, guard)
        self.assertEqual(self.steps[0]['with']['persist-credentials'], 'false')
        self.assertEqual(self.steps[0]['with']['fetch-depth'], '0')
        self.assertIn('test "$(git rev-parse HEAD)" = "$GITHUB_SHA"', self.commands[0])
        self.assertIn('test "$(git rev-parse --is-shallow-repository)" = "false"', self.commands[0])
        self.assertIn('test "$(hostname -s)" = "q5m-n03"', self.commands[0])
        prepare = self.steps[2]['run']
        self.assertIn('source=/home/q5m/code/erdos-193', prepare)
        self.assertIn('test -z "$(git -C "$source" status --porcelain)"', prepare)
        self.assertIn("'+refs/heads/main:refs/remotes/origin/main'", prepare)
        self.assertIn('rev-parse refs/remotes/origin/main', prepare)
        for step in self.steps[3:]:
            self.assertEqual(step['working-directory'], '/home/q5m/code/erdos-193')

    def test_only_yaml_lifecycle_and_first_deploy_adoption(self):
        expected = [
            'q5m-lab project production plan --revision "$GITHUB_SHA" --json',
            'q5m-lab project production deploy --revision "$GITHUB_SHA" --adopt-existing --json',
            'q5m-lab project production status --service erdos-193 --json',
        ]
        self.assertEqual(self.commands[2:], expected)
        for step in self.steps:
            self.assertNotIn('continue-on-error', step)
        for step in self.steps[3:5]:
            self.assertNotIn('if', step)  # Normal Actions success dependency; no failed-plan bypass.
        self.assertEqual(self.steps[-1]['if'], 'always()')
        self.assertNotIn('q5m-app', '\n'.join(self.commands))
        self.assertNotIn('--environment production', '\n'.join(self.commands))
        self.assertIn('q5m-lab project production rollback --service erdos-193 --json', read('docs/DEPLOYMENT.md'))
        self.assertIn('Before merging', read('docs/DEPLOYMENT.md'))

    def test_mock_plan_then_deploy_and_failed_plan(self):
        # Execute the actual workflow command text with a fake CLI only.
        for plan_exit in (0, 9):
            with self.subTest(plan_exit=plan_exit), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                log = root / 'calls.jsonl'
                cli = root / 'q5m-lab'
                cli.write_text(f'#!{sys.executable}\n'
                               'import json, os, sys\n'
                               'with open(os.environ["CALL_LOG"], "a") as f:\n'
                               '    f.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                               'sys.exit(int(os.environ["PLAN_EXIT"]) if sys.argv[3] == "plan" else 0)\n')
                cli.chmod(0o700)
                env = {'PATH': directory + os.pathsep + os.defpath, 'GITHUB_SHA': 'a' * 40,
                       'CALL_LOG': str(log), 'PLAN_EXIT': str(plan_exit)}
                result = subprocess.run(['/bin/bash', '--noprofile', '--norc', '-eo', 'pipefail', '-c',
                                         '\n'.join(self.commands[2:4])], env=env,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, plan_exit, result.stderr)
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                expected = [['project', 'production', 'plan', '--revision', 'a' * 40, '--json']]
                if not plan_exit:
                    expected.append(['project', 'production', 'deploy', '--revision', 'a' * 40,
                                     '--adopt-existing', '--json'])
                self.assertEqual(calls, expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)

"""Run with: python -m unittest discover -s third_party/mm/tests."""

import ast
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import tarfile
import tempfile
import unittest


MM_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MM_ROOT.parents[1]


class InternalTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'workspace with spaces'
        self.work.mkdir()
        shutil.copy(MM_ROOT / 'prepare_tasks.sh', self.work)
        shutil.copytree(MM_ROOT / 'internal', self.work / 'internal')
        self.archives = self.root / 'archives'
        self.archives.mkdir()
        public = self.root / 'public'
        public.mkdir()
        (public / 'public_task.py').write_text('PUBLIC = True\n')
        with tarfile.open(self.archives / 'paneval.tar.gz', 'w:gz') as archive:
            archive.add(public / 'public_task.py', arcname='tasks/public_task.py')

    def prepare(self):
        return subprocess.run(
            ['bash', str(self.work / 'prepare_tasks.sh')],
            env={**os.environ, 'CONDA_DATASET_DOWNLOAD_PATH': str(self.archives)},
            capture_output=True,
            text=True,
        )

    def test_extracts_then_copies_every_catalog_config_and_helper(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        evaluator = self.work / 'paneval'
        self.assertTrue((evaluator / 'tasks/public_task.py').is_file())
        self.assertFalse((evaluator / 'internal/internal').exists())
        migration = PROJECT_ROOT / 'paneval/apps/evaluation/migrations/0002_auto_20260609_1108.py'
        # Include the commented OCRLite configs without enabling them.
        paths = re.findall(r'"(paneval/internal/tasks/[^"]+\.py)"', migration.read_text())
        self.assertEqual(len(paths), 10)
        for path in paths:
            with self.subTest(config=path):
                config_file = self.work / path
                config = runpy.run_path(str(config_file))
                helpers = []
                for key in ('register_dataset', 'register_evaluator'):
                    helpers.extend(config.get(key, {}))
                if config.get('config', {}).get('processor'):
                    helpers.append(config['config']['processor'])
                if config['evaluator'].get('eval_func'):
                    helpers.append(config['evaluator']['eval_func'])
                for helper in helpers:
                    self.assertTrue((config_file.parent / helper).is_file(), helper)
        for path in (evaluator / 'internal').rglob('*.py'):
            ast.parse(path.read_text(), filename=str(path))
            self.assertNotIn('flagevalmm', path.read_text())

    def test_reused_evaluator_refreshes_tasks_without_reextracting(self):
        self.assertEqual(self.prepare().returncode, 0)
        shutil.rmtree(self.archives)
        internal = self.work / 'internal'
        task = internal / 'tasks/vqa/mmbench/mm_bench_cn.py'
        task.write_text('UPDATED = True\n')
        (internal / '.vendor-version').write_text('next')
        target = self.work / 'paneval'
        (target / 'internal/unrelated.txt').write_text('keep')
        for _ in range(2):
            result = self.prepare()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((target / task.relative_to(self.work)).read_text(), 'UPDATED = True\n')
            self.assertEqual((target / 'internal/.vendor-version').read_text(), 'next')
            self.assertEqual((target / 'internal/unrelated.txt').read_text(), 'keep')
            self.assertTrue((target / 'tasks/public_task.py').is_file())

    def test_missing_vendor_tree_fails_preparation(self):
        shutil.rmtree(self.work / 'internal')
        self.assertNotEqual(self.prepare().returncode, 0)


if __name__ == '__main__':
    unittest.main()

import os
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from paneval.apps.evaluation import executor
from paneval.apps.evaluation.models import Evaluation, SfTaskResult

from . import models, tasks


class BatchTestMixin:
    def create_evaluation(self, domain=Evaluation.Domain.NLP):
        return Evaluation.objects.create(
            user_id=1,
            name='test evaluation',
            sence=Evaluation.Sence.API,
            domain=domain,
            created_at=timezone.now(),
        )

    def create_batch(self, evaluation, **kwargs):
        values = {
            'evaluation_id': evaluation.pk,
            'user_id': 1,
            'celery_task_id': '',
            'resource': {},
            'status': models.Batch.Status.PENDING,
            'created_at': timezone.now(),
        }
        values.update(kwargs)
        return models.Batch.objects.create(**values)


@override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1', 'root@m2'])
class BatchExecutorPinningTests(BatchTestMixin, TestCase):
    @patch.object(tasks.start_sync_model, 'delay')
    @patch.object(tasks, 'watch_batch_timeout')
    def test_run_start_persists_and_keeps_pin_across_retries(
            self,
            watch_timeout,
            start_sync,
    ):
        batch = self.create_batch(self.create_evaluation())
        expected = executor.pick_instance(batch.pk)

        tasks.run_on_executor(batch.pk, 0)
        batch.refresh_from_db()
        self.assertEqual(batch.executor_instance, expected)
        self.assertEqual(batch.status, models.Batch.Status.PREPARING)

        batch.try_sequence = 1
        batch.status = models.Batch.Status.PENDING
        batch.save(update_fields=['try_sequence', 'status'])
        tasks.run_on_executor(batch.pk, 1)
        batch.refresh_from_db()
        self.assertEqual(batch.executor_instance, expected)

    @patch.object(tasks.start_sync_model, 'delay')
    @patch.object(tasks, 'watch_batch_timeout')
    def test_run_start_repins_removed_instance(self, watch_timeout, start_sync):
        batch = self.create_batch(
            self.create_evaluation(),
            executor_instance='root@removed',
        )

        with self.assertLogs(tasks.logger.name, level='WARNING'):
            tasks.run_on_executor(batch.pk, 0)

        batch.refresh_from_db()
        self.assertEqual(batch.executor_instance, executor.pick_instance(batch.pk))


@override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1'])
class ExecutorRoutingTests(BatchTestMixin, TestCase):
    def tearDown(self):
        executor._services.clear()

    @patch.object(tasks.storage.store, 'full_uri', return_value='/objects/model')
    @patch.object(tasks.subprocess, 'check_output', return_value=b'ok')
    def test_start_syncing_targets_pinned_instance(self, check_output, full_uri):
        on_error = Mock()
        callback = Mock()
        job = tasks.SyncJob(
            storage_key='model',
            user_model=True,
            sync_id='download-id',
        )

        tasks.start_syncing([job], on_error, callback, instance='root@m1')

        command = check_output.call_args.args[0]
        self.assertEqual(command[-1], 'root@m1:/share/project/download-id')
        callback.delay.assert_called_once_with(download_job=job)
        on_error.delay.assert_not_called()

    @patch.object(tasks.subprocess, 'run')
    def test_online_port_targets_pinned_instance(self, run):
        run.return_value = SimpleNamespace(stdout=b'43123\n', returncode=0)
        batch = SimpleNamespace(executor_instance='root@m1')

        self.assertEqual(tasks.online_port(batch), '43123')
        self.assertIn('root@m1', run.call_args.args[0])

    @patch.object(tasks.subprocess, 'run')
    def test_online_status_distinguishes_process_and_transport(self, run):
        evaluation = SimpleNamespace(domain=Evaluation.Domain.NLP)
        run.return_value = SimpleNamespace(
            returncode=0,
            stdout=b'',
            stderr=b'',
        )
        self.assertEqual(
            tasks.online_status(7, evaluation, 'root@m1')['status'],
            'Succeed',
        )

        run.return_value = SimpleNamespace(
            returncode=0,
            stdout=b'root 7 run.sh 7',
            stderr=b'',
        )
        self.assertEqual(
            tasks.online_status(7, evaluation, 'root@m1')['status'],
            'Running',
        )

        run.return_value = SimpleNamespace(
            returncode=255,
            stdout=b'',
            stderr=b'ssh: connect failed',
        )
        with self.assertRaisesRegex(executor.ExecutorUnreachable, 'root@m1'):
            tasks.online_status(7, evaluation, 'root@m1')

    @patch.object(tasks.subprocess, 'run')
    def test_kill_online_uses_pin_and_none_uses_legacy_host(self, run):
        tasks.kill_online('1.0', 'root@m1')
        self.assertIn('root@m1', run.call_args.args[0])

        tasks.kill_online('2.0', None)
        self.assertIn('root@executor', run.call_args.args[0])

    @patch.object(tasks.watch_batch, 'apply_async')
    @patch.object(tasks.threading, 'Thread')
    @patch.object(tasks.subprocess, 'Popen')
    @patch.object(tasks, '_build_environ')
    @patch.object(tasks, 'executor_instance_ready', return_value=True)
    def test_run_online_launches_on_pinned_instance(
            self,
            ready,
            build_environ,
            popen,
            thread,
            watch_apply,
    ):
        evaluation = self.create_evaluation()
        batch = self.create_batch(
            evaluation,
            executor_instance='root@m1',
            model_storage_url='api/model',
        )
        build_environ.return_value = {
            'MODEL_PATH': '/share/project/model',
        }
        process = Mock(pid=123)
        process.stdin = Mock()
        popen.return_value = process

        tasks.run_online(
            batch.pk,
            batch.try_sequence,
            tasks.SyncJob('model', user_model=True, sync_id='model'),
        )

        command = popen.call_args.args[0]
        self.assertIn('root@m1', command)
        watch_apply.assert_called_once_with(args=(batch.pk,), countdown=60)

    @patch.object(tasks.subprocess, 'Popen')
    @patch.object(tasks, '_build_environ', return_value={})
    @patch.object(tasks, 'executor_instance_ready', return_value=False)
    @patch.object(tasks.on_error, 'delay')
    def test_run_online_fails_when_pinned_instance_is_not_ready(
            self,
            on_error_delay,
            ready,
            build_environ,
            popen,
    ):
        evaluation = self.create_evaluation()
        batch = self.create_batch(evaluation, executor_instance='root@m1')
        SfTaskResult.objects.create(
            batch_id=-4,
            result={'status': 1},
        )

        tasks.run_online(
            batch.pk,
            batch.try_sequence,
            tasks.SyncJob('model', user_model=True, sync_id='model'),
        )

        on_error_delay.assert_called_once_with(
            batch.pk,
            models.Batch.FailureKind.SYSTEM,
            'executor instance root@m1 is not ready',
        )
        popen.assert_not_called()

    def test_multimodal_syncs_task_tree_before_launch_on_pinned_executor(self):
        evaluation = self.create_evaluation(domain=Evaluation.Domain.MULTI)
        batch = self.create_batch(evaluation, executor_instance='root@m1')
        process = Mock(pid=123)
        sequence = Mock()
        with (
            patch.object(tasks, 'executor_instance_ready', return_value=True),
            patch.object(tasks, '_build_environ', return_value={}),
            patch.object(tasks, 'merge_lbx_batch', return_value=[]),
            patch.object(tasks, 'online_port', return_value='43123'),
            patch.object(tasks.subprocess, 'run') as run,
            patch.object(tasks.subprocess, 'Popen', return_value=process) as popen,
            patch.object(tasks.threading, 'Thread'),
            patch.object(tasks.watch_batch, 'apply_async'),
        ):
            sequence.attach_mock(run, 'run')
            sequence.attach_mock(popen, 'launch')
            tasks.run_online(batch.pk, batch.try_sequence, tasks.SyncJob('model'))

        self.assertEqual([c[0] for c in sequence.mock_calls], ['run', 'run', 'launch'])
        mkdir, sync = run.call_args_list
        self.assertIn('root@m1', mkdir.args[0])
        self.assertTrue(mkdir.kwargs['check'])
        self.assertEqual(sync.args[0][-2:], [
            os.path.join(settings.BASE_DIR, 'third_party/mm/'),
            f'root@m1:/share/project/mmenv/{batch.pk}.{batch.try_sequence}/__paneval__',
        ])
        self.assertTrue(sync.kwargs['check'])
        self.assertIn('root@m1', popen.call_args.args[0])

    def test_multimodal_transfer_failure_prevents_launch(self):
        evaluation = self.create_evaluation(domain=Evaluation.Domain.MULTI)
        batch = self.create_batch(evaluation, executor_instance='root@m1')
        for failed_step in ('mkdir', 'rsync'):
            with self.subTest(failed_step=failed_step):
                error = subprocess.CalledProcessError(23, [failed_step])
                results = [error] if failed_step == 'mkdir' else [Mock(), error]
                with (
                    patch.object(tasks, 'executor_instance_ready', return_value=True),
                    patch.object(tasks, '_build_environ', return_value={}),
                    patch.object(tasks, 'merge_lbx_batch', return_value=[]),
                    patch.object(tasks, 'online_port', return_value='43123'),
                    patch.object(tasks.subprocess, 'run', side_effect=results),
                    patch.object(tasks.subprocess, 'Popen') as popen,
                    patch.object(tasks.watch_batch, 'apply_async') as watch,
                    patch.object(tasks.on_error, 'delay') as on_error,
                ):
                    tasks.run_online(batch.pk, batch.try_sequence, tasks.SyncJob('model'))
                popen.assert_not_called()
                watch.assert_not_called()
                on_error.assert_called_once_with(batch.pk, models.Batch.FailureKind.SYSTEM, str(error))

    @patch.object(tasks.notify_status, 'delay')
    @patch.object(tasks.kill_online, 'apply_async')
    def test_cancel_routes_kill_to_pinned_instance(self, kill_apply, notify_delay):
        evaluation = self.create_evaluation()
        batch = self.create_batch(evaluation, executor_instance='root@m1')

        tasks.cancel_batch(batch.pk)

        kill_apply.assert_called_once_with(
            args=(f'{batch.pk}.{batch.try_sequence}', 'root@m1'),
            countdown=10,
        )

    @patch('paneval.apps.evaluation.utils.get_subjective_tasks', return_value=[])
    @patch.object(tasks.watch_batch, 'apply_async')
    @patch.object(tasks.on_error, 'delay')
    @patch.object(tasks, 'online_status')
    def test_watch_transport_failure_is_terminal_system_failure(
            self,
            online_status,
            on_error_delay,
            watch_apply,
            subjective_tasks,
    ):
        evaluation = self.create_evaluation()
        batch = self.create_batch(evaluation, executor_instance='root@m1')
        online_status.side_effect = executor.ExecutorUnreachable('ssh failed')

        tasks.watch_batch(batch.pk)

        on_error_delay.assert_called_once_with(
            batch.pk,
            models.Batch.FailureKind.SYSTEM,
            'ssh failed',
        )
        watch_apply.assert_not_called()

    @patch('paneval.apps.evaluation.utils.get_subjective_tasks', return_value=[])
    @patch.object(tasks.watch_batch, 'apply_async')
    @patch.object(tasks.on_error, 'delay')
    @patch.object(tasks, 'online_status', side_effect=RuntimeError('temporary'))
    def test_watch_unrelated_exception_still_retries(
            self,
            online_status,
            on_error_delay,
            watch_apply,
            subjective_tasks,
    ):
        evaluation = self.create_evaluation()
        batch = self.create_batch(evaluation, executor_instance='root@m1')

        tasks.watch_batch(batch.pk)

        on_error_delay.assert_not_called()
        watch_apply.assert_called_once_with(
            args=(batch.pk,),
            countdown=30,
        )


class LegacyExecutorRoutingTests(SimpleTestCase):
    @patch.object(tasks.subprocess, 'run')
    def test_online_status_with_empty_pin_uses_default_service(self, run):
        run.return_value = SimpleNamespace(
            returncode=0,
            stdout=b'process',
            stderr=b'',
        )
        evaluation = SimpleNamespace(domain=Evaluation.Domain.NLP)

        tasks.online_status(1, evaluation, None)

        self.assertIn('root@executor', run.call_args.args[0])

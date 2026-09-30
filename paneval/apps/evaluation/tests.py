from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase, TestCase, override_settings

from . import executor
from .models import SfTaskResult
from . import tasks


class ExecutorServiceTests(SimpleTestCase):
    def tearDown(self):
        executor._services.clear()

    @override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1', 'root@m2'])
    def test_pick_instance_uses_batch_id_modulo(self):
        self.assertEqual(executor.pick_instance(0), 'root@m1')
        self.assertEqual(executor.pick_instance(1), 'root@m2')
        self.assertEqual(executor.pick_instance(2), 'root@m1')

    @override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@executor'])
    def test_pick_instance_with_one_entry_is_legacy_host(self):
        self.assertEqual(executor.pick_instance(123), 'root@executor')

    @override_settings(
        PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1:2222', 'root@m2'],
    )
    def test_service_parses_explicit_port_and_uses_default_port(self):
        explicit = executor.get_service('root@m1:2222')
        default_port = executor.get_service('root@m2')

        self.assertEqual(explicit.instance, 'root@m1:2222')
        self.assertEqual(
            explicit.online_ssh_exe_cmd('true'),
            [
                'ssh', '-o', 'StrictHostKeyChecking no',
                '-CAXY', 'root@m1', '-p', '2222', 'true',
            ],
        )
        self.assertEqual(
            explicit.online_scp_to_remote('/tmp/src', '/tmp/dst')[-1],
            'root@m1:/tmp/dst',
        )
        self.assertEqual(
            explicit.online_rsync_to_remote('/tmp/src', '/tmp/dst'),
            [
                'rsync', '-av', '-e', 'ssh -p 2222',
                '/tmp/src', 'root@m1:/tmp/dst',
            ],
        )
        self.assertIn('ssh -p 3022', default_port.online_rsync_to_remote('a', 'b'))

    def test_default_service_keeps_legacy_command_shape(self):
        self.assertIs(executor.get_service(None), executor.service)
        self.assertEqual(
            executor.get_service(None).online_ssh_exe_cmd('true'),
            [
                'ssh', '-o', 'StrictHostKeyChecking no',
                '-CAXY', 'root@executor', '-p', '3022', 'true',
            ],
        )

    @override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1'])
    def test_unknown_instance_is_rejected(self):
        with self.assertRaisesRegex(
                executor.ExecutorInstanceError,
                'root@removed',
        ):
            executor.get_service('root@removed')


@override_settings(PANEVAL_SSH_EXECUTOR_INSTANCES=['root@m1', 'root@m2'])
class ExecutorInitializationTests(TestCase):
    def tearDown(self):
        executor._services.clear()

    @patch.object(tasks.init_ssh_executor_instance, 'delay')
    def test_dispatcher_fans_out_to_every_instance(self, delay):
        tasks.init_ssh_executor()

        self.assertEqual(
            delay.call_args_list,
            [call('root@m1'), call('root@m2')],
        )

    @patch.object(tasks.cache, 'add', return_value=False)
    @patch.object(tasks, 'executor_instance_ready', return_value=False)
    def test_instance_init_skips_when_lock_is_held(self, ready, cache_add):
        tasks.init_ssh_executor_instance('root@m1')

        cache_add.assert_called_once_with(
            'paneval:ssh-executor-init:root@m1',
            '1',
            timeout=25 * 60,
        )
        self.assertFalse(SfTaskResult.objects.exists())

    @patch.object(tasks.cache, 'delete')
    @patch.object(tasks.cache, 'add', side_effect=[True, True])
    @patch.object(tasks.subprocess, 'run')
    def test_instance_init_records_success(self, run, cache_add, cache_delete):
        run.return_value = SimpleNamespace(returncode=0, stdout='', stderr='')

        tasks.init_ssh_executor_instance('root@m1')

        row = SfTaskResult.objects.get(batch_id=tasks.ONLINE_JOB_BATCH_ID)
        self.assertEqual(row.result['instances']['root@m1']['status'], 1)
        self.assertEqual(row.result['instances']['root@m1']['error'], '')
        self.assertEqual(row.result['status'], 0)
        self.assertEqual(run.call_count, 4)
        cache_delete.assert_any_call('paneval:ssh-executor-init:root@m1')

    @patch.object(tasks.cache, 'delete')
    @patch.object(tasks.cache, 'add', side_effect=[True, True])
    @patch.object(tasks.subprocess, 'run')
    def test_instance_init_resets_state_after_failure(self, run, cache_add, cache_delete):
        run.return_value = SimpleNamespace(
            returncode=255,
            stdout='',
            stderr='ssh: connect failed',
        )

        tasks.init_ssh_executor_instance('root@m1')

        row = SfTaskResult.objects.get(batch_id=tasks.ONLINE_JOB_BATCH_ID)
        state = row.result['instances']['root@m1']
        self.assertEqual(state['status'], 0)
        self.assertIn('ssh: connect failed', state['error'])
        self.assertIn('last_attempt_at', state)

    @patch.object(tasks.cache, 'delete')
    @patch.object(tasks.cache, 'add', return_value=True)
    def test_state_updates_preserve_other_instances(self, cache_add, cache_delete):
        self.assertTrue(tasks._update_instance_state('root@m1', 1, ''))
        self.assertTrue(tasks._update_instance_state('root@m2', 1, ''))

        row = SfTaskResult.objects.get(batch_id=tasks.ONLINE_JOB_BATCH_ID)
        self.assertEqual(set(row.result['instances']), {'root@m1', 'root@m2'})
        self.assertEqual(row.result['status'], 1)
        self.assertTrue(tasks.executor_instance_ready('root@m1'))
        self.assertTrue(tasks.executor_instance_ready('root@m2'))

    def test_ready_instance_skips_lock_and_provisioning(self):
        SfTaskResult.objects.create(
            batch_id=tasks.ONLINE_JOB_BATCH_ID,
            result={
                'exp_id': 'none',
                'status': 0,
                'instances': {'root@m1': {'status': 1}},
            },
        )
        with patch.object(tasks.cache, 'add') as cache_add, patch.object(
                tasks.subprocess,
                'run',
        ) as run:
            tasks.init_ssh_executor_instance('root@m1')

        cache_add.assert_not_called()
        run.assert_not_called()

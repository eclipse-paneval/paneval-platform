import abc
import threading
import queue
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Callable, Tuple, Optional, Dict, Any, Generator

from .models import Dataset, Task, Scenario, RequestState
from .models import DatasetMetric, Stat, TaskMetric


@dataclass
class RunUnit:
    scenario: Scenario
    task: Task
    dataset: Dataset


class Store(metaclass=abc.ABCMeta):
    """Store to save intermediate result of task."""
    @abc.abstractmethod
    def add_unit(self, unit: RunUnit):
        pass

    @abc.abstractmethod
    def is_all_units_done(self) -> bool:
        pass

    @abc.abstractmethod
    def done_unit(self, unit: RunUnit, summary: DatasetMetric):
        pass

    @abc.abstractmethod
    def load_next_pending_unit(self) -> Optional[RunUnit]:
        pass

    @abc.abstractmethod
    def load_results(self) -> List[Tuple[RunUnit, DatasetMetric]]:
        pass

    @abc.abstractmethod
    def store_stat(self, stat: Stat):
        pass

    @abc.abstractmethod
    def load_stat(self) -> Optional[Stat]:
        pass


class Dispatcher(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def dispatch(
            self,
            unit: RunUnit,
            on_unit_done: Callable[[RunUnit, List[RequestState]], None],
            barrier: threading.Barrier,
    ):
        pass



class ThreadingDispatcher(Dispatcher):
    def __init__(self, num: int, maxsize: int, store: Store):
        self.queue: queue.Queue = queue.Queue(maxsize)
        self.workers = []
        self.store = store
        self.states: List[RequestState] = []
        self._lock = threading.Lock()

        for _ in range(max(1, num)):
            t = threading.Thread(target=self._start, daemon=True)
            t.start()
            self.workers.append(t)

    def _start(self):
        while True:
            (unit, state) = self.queue.get()
            try:
                new_state = unit.task.execute(state)
                with self._lock:
                    self.states.append(new_state)
            except:
                with self._lock:
                    self.states.append(state)
                raise
            finally:
                self.queue.task_done()

    def dispatch(
            self,
            unit: RunUnit,
            on_unit_done: Callable[[RunUnit, List[RequestState]], None],
            barrier: threading.Barrier,
    ):
        with self._lock:
            self.states = []

        try:
            for state in unit.dataset.create_instances():
                self.queue.put((unit, state))
        except:
            on_unit_done(unit, self.states)
            barrier.wait()
            raise

        def _wait_then_call():
            print("Joinning")
            self.queue.join()
            print(f"Call with states: {len(self.states)}")
            on_unit_done(unit, self.states)

        threading.Thread(target=_wait_then_call, daemon=True).start()


class InmemoryStore(Store):
    """Store to save intermediate result of task."""
    def __init__(self):
        self.units: List[RunUnit] = []
        self.idx: int = 0
        self.results: List[Tuple[RunUnit, DatasetMetric]] = []
        self.stat: Optional[Stat] = None

    def add_unit(self, unit: RunUnit):
        self.units.append(unit)

    def is_all_units_done(self) -> bool:
        print(f'units {len(self.units)} -- results {len(self.results)}')
        return len(self.units) == len(self.results)

    def done_unit(self, unit: RunUnit, summary: DatasetMetric):
        self.results.append((unit, summary))

    def load_next_pending_unit(self) -> Optional[RunUnit]:
        if self.idx >= len(self.units):
            return None
        try:
            return self.units[self.idx]
        finally:
            self.idx += 1

    def load_results(self) -> List[Tuple[RunUnit, DatasetMetric]]:
        return self.results

    def store_stat(self, stat: Stat):
        self.stat = stat

    def load_stat(self) -> Optional[Stat]:
        return self.stat



class Runner:
    def __init__(
            self, scenario: Scenario, dispatcher: Dispatcher, store: Store,
            record_all_states: bool = False,
            summarize: bool = True,
    ):
        self.scenario: Scenario = scenario
        self.dispatcher = dispatcher
        self.store = store
        self.states: List[Dict[str, Any]] = []
        self.record_all_states = record_all_states
        self.summarize = summarize
        self._barrier = threading.Barrier(2)

        for task in self.scenario.create_tasks():
            for dataset in task.create_datasets():
                unit = RunUnit(
                    scenario=self.scenario,
                    task=task,
                    dataset=dataset,
                )
                self.store.add_unit(unit)

    def run(self):
        self.start()
        self.block_until_done()

    def start(self):
        self._dispatch_next()

    def block_until_done(self):
        self._barrier.wait()

    def _dispatch_next(self):
        next_unit = self.store.load_next_pending_unit()
        if next_unit is not None:
            self.dispatcher.dispatch(next_unit, self.on_unit_done, self._barrier)
            return

        if self.summarize:
            self._summarize()

        self._barrier.wait()

    def on_unit_done(self, unit: RunUnit, states: List[RequestState]):
        if self.record_all_states:
            self.states.append({
                "task_id": unit.task.id(),
                "dataset_id": unit.dataset.id(),
                "states": [
                    {
                        "request": x.request,
                        "response": x.response,
                        "golds": x.golds,
                        "timeline": x.timeline,
                    }
                    for x in states
                ],
            })

        try:
            if self.summarize:
                metric = unit.dataset.summarize(states)
                self.store.done_unit(unit, metric)
        except:
            raise
        finally:
            self._dispatch_next()

    def _summarize(self):
        results = self.store.load_results()
        by_task: Dict[str, List[DatasetMetric]] = defaultdict(list)
        tasks: Dict[str, Task] = {}
        for (unit, item) in results:
            by_task[unit.task.id()].append(item)
            tasks[unit.task.id()] = unit.task

        task_metrics: List[TaskMetric] = []
        for key, metrics in by_task.items():
            task_metrics.append(tasks[key].summarize(metrics))

        stat = self.scenario.summarize(task_metrics)
        self.store.store_stat(stat)


def run(
        scenario: Scenario,
        *,
        threads_num: int = 6,
        queue_maxsize: int = 1000,
        record_all_states: bool = False,
        summarize: bool = True,
) -> Tuple[Optional[Stat], List[Dict[str, Any]]]:
    store: Store = InmemoryStore()
    dispatcher = ThreadingDispatcher(threads_num, queue_maxsize, store)
    runner = Runner(
        scenario, dispatcher, store, record_all_states=record_all_states,
        summarize=summarize,
    )
    runner.run()
    return store.load_stat(), runner.states


class EvaluationError(Exception):
    pass


class DatasetStateRunner:
    def __init__(
            self, scenario: Scenario, task_id: str, dataset_id: str,
            dry_run: bool = False,
    ):
        self.scenario: Scenario = scenario
        task = scenario.lookup_task(task_id)
        if task is None:
            raise RuntimeError(f"couldn't find task via task_id={task_id}, dataset_id={dataset_id}")  # noqa
        self.task: Task = task
        dataset = scenario.lookup_dataset(task_id, dataset_id)
        if dataset is None:
            raise RuntimeError(f"couldn't find dataset via task_id={task_id}, dataset_id={dataset_id}")  # noqa

        self.dataset: Dataset = dataset
        self.task_id = task_id
        self.dataset_id = dataset_id
        self.dry_run = dry_run

        self._raw_states: List[Dict[str, Any]] = []
        self._index = 0

    def snapshot(self) -> Dict[str, Any]:
        """Take a snapshot of current state."""
        return {
            'raw_states': self._raw_states,
            'index': self._index
        }

    def resume(self, state: Dict[str, Any]):
        self._raw_states = state['raw_states']
        self._index = state['index']

    def run(self) -> Generator[Dict[str, Any], None, Tuple[Dict[str, Any], Dict[str, Any]]]:  # noqa
        if not self._raw_states:
            self._raw_states = [{'raw': x.raw} for x in self.dataset.create_instances()]
        if len(self._raw_states) == 0:
            raise EvaluationError(
                "prepare_dataset but got 0 instances, task_id: %s, dataset_id: %s" %
                (self.task_id, self.dataset_id)
        )

        for i in range(self._index, len(self._raw_states)):
            self._raw_states[i] = self._execute_request(self._raw_states[i])
            self._index += 1
            yield self._raw_states[i]

        return self.generate_metrics()

    def _execute_request(self, raw_state: Dict[str, Any]) -> Dict[str, Any]:
        new_state = self.task.execute(RequestState(raw=raw_state['raw']))

        if 'request_state' in new_state.raw:
            result = new_state.raw['request_state']['result']
            if result is not None and not result['success']:
                raise EvaluationError(result['error'])

        obj = {
            'raw': new_state.raw,
            'timeline': new_state.timeline,
        }
        if self.dry_run:
            obj.update(
                request=new_state.request,
                response=new_state.response,
                golds=new_state.golds,
            )
        return obj

    def generate_metrics(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        metrics: Dict[str, Any] = {}
        if self.dry_run:
            result = {
                'task_id': self.task_id,
                'dataset_id': self.dataset_id,
                'states': [
                    {
                        'request': x['request'],
                        'response': x['response'],
                        'golds': x['golds'],
                    }
                    for x in self._raw_states
                ]
            }
        else:
            ret: DatasetMetric = self.dataset.summarize([  # type: ignore
                RequestState(
                    raw=x['raw'],
                    timeline=x['timeline'],
                )
                for x in self._raw_states
            ])
            result = ret.raw
            metrics.update({
                'started_at': ret.started_at,
                'stopped_at': ret.stopped_at,
                'metrics': ret.metrics,
            })


        return result, metrics

import abc
import enum
import time

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from cached_property import cached_property

@dataclass
class Options:
    model: str
    "The model name to evaluate."

    server_url: str
    "The request url of the evaluated service."

    extras: Dict[str, Any] = field(default_factory=dict)
    "Extra options for scenario-specific usage."


class Domain(enum.Enum):
    NLP = "NLP"
    CV = "CV"
    Voice = "voice"


class Stage(enum.IntEnum):
    init = 0
    request = 1
    response = 2


@dataclass
class Metric:
    started_at: int
    stopped_at: int
    total: int
    avg: int
    max: int


@dataclass
class RequestState:
    raw: Dict[str, Any]

    request: Dict[str, Any] = field(default_factory=dict)
    response: Any = None
    golds: List[str] = field(default_factory=list)
    timeline: List[Tuple[Stage, int]] = field(default_factory=list)

    def record_init_at(self):
        self.timeline.append((Stage.init, int(time.time() * 1000)))

    def record_request_at(self):
        self.timeline.append((Stage.request, int(time.time() * 1000)))

    def record_response_at(self):
        self.timeline.append((Stage.response, int(time.time() * 1000)))


@dataclass
class Stat:
    accuracy: float
    calibration: float
    robustness: float
    fairness: float
    bias: float
    win_rate: Optional[float] = None
    details: List[Dict[str, Any]] = field(default_factory=list)


class Language(enum.Enum):
    any_ = "any"
    zh = "zh"
    en = "en"


class Tag(enum.Enum):
    commomsence = "CS"
    truthfulness = "TF"
    matching = "M"
    reasoning = "R"
    generation = "G"


@dataclass
class Meta:
    name: str
    description: str
    server_url: str
    subject: str = ''
    label: str = ''
    tags: List[Tag] = field(default_factory=list)


@dataclass
class DatasetMetric:
    raw: Dict[str, Any]

    started_at: Optional[int] = None
    stopped_at: Optional[int] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def get_timeline_metrics(states: List[RequestState]) -> Tuple[
            Optional[int], Optional[int], List[int]
    ]:
        started_at = None
        stopped_at = None
        elapseds: List[int] = []
        for state in states:
            timeline = dict(state.timeline)
            init = timeline.get(Stage.init)
            req = timeline.get(Stage.request)
            res = timeline.get(Stage.response)
            if init is not None:
                if started_at is None or init < started_at:
                    started_at = init

            if res is not None:
                if stopped_at is None or res > stopped_at:
                    stopped_at = res

            if res is not None and req is not None:
                elapseds.append(res - req)
        return started_at, stopped_at, elapseds


@dataclass
class TaskMetric:
    raw: Dict[str, Any]

    metric: Optional[Metric] = None

    @staticmethod
    def get_timeline_metrics(metrics: List[DatasetMetric]) -> Metric:
        started_at = None
        stopped_at = None
        elapseds: List[int] = []
        for item in metrics:
            elapseds.extend(item.metrics['elapseds'])
            if item.started_at is not None:
                if started_at is None or item.started_at < started_at:
                    started_at = item.started_at
            if item.stopped_at is not None:
                if stopped_at is None or item.stopped_at > stopped_at:
                    stopped_at = item.stopped_at

        return Metric(
            started_at=started_at or 0,
            stopped_at=stopped_at or 0,
            total=len(elapseds),
            max=max(elapseds),
            avg= int(sum(elapseds)/ len(elapseds)),
        )


class Dataset(metaclass=abc.ABCMeta):
    @cached_property
    def instances(self) -> List[RequestState]:
        return self.create_instances()

    @abc.abstractmethod
    def create_instances(self) -> List[RequestState]:
        pass

    @abc.abstractmethod
    def summarize(self, states: List[RequestState]) -> DatasetMetric:
        pass

    @abc.abstractmethod
    def id(self) -> str:
        pass



class Task(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_meta(self) -> Meta:
        pass

    @cached_property
    def datasets(self) -> List[Dataset]:
        return self.create_datasets()

    @abc.abstractmethod
    def create_datasets(self) -> List[Dataset]:
        pass

    @abc.abstractmethod
    def execute(self, instance: RequestState) -> RequestState:
        pass

    @abc.abstractmethod
    def summarize(self, stats: List[DatasetMetric]) -> TaskMetric:
        pass

    def id(self) -> str:
        meta = self.get_meta()
        if meta.subject:
            return f'{meta.name}-{meta.subject}'
        return meta.name


class Scenario(metaclass=abc.ABCMeta):
    def __init__(self, opts: Options):
        self.options: Options = opts
        self._loaded_tasks: Dict[str, Task] = {}
        self._loaded_dts: Dict[str, Dataset] = {}

    @abc.abstractmethod
    def get_domain(self) -> Domain:
        pass

    @abc.abstractmethod
    def get_language(self) -> Language:
        pass

    @cached_property
    def tasks(self) -> List[Task]:
        return self.create_tasks()

    @abc.abstractmethod
    def create_tasks(self) -> List[Task]:
        pass

    @abc.abstractmethod
    def summarize(self, metrics: List[TaskMetric]) -> Stat:
        pass

    def lookup_dataset(self, task_id: str, dataset_id: str) -> Optional[Dataset]:
        key = f'{task_id}{dataset_id}'
        if key in self._loaded_dts:
            return self._loaded_dts[key]
        task = self.lookup_task(task_id)
        if task is not None:
            for dt in task.create_datasets():
                if dt.id() == dataset_id:
                    self._loaded_dts[key] = dt
                    return dt

        return None

    def lookup_task(self, task_id: str) -> Optional[Task]:
        if task_id in self._loaded_tasks:
            return self._loaded_tasks[task_id]

        for task in self.create_tasks():
            if task.id() == task_id:
                self._loaded_tasks[task_id] = task
                return task
        return None

class NLPScenario(Scenario):
    def get_domain(self) -> Domain:
        return Domain.NLP


class CVScenario(Scenario):
    def get_domain(self) -> Domain:
        return Domain.CV


class VoiceScenario(Scenario):
    def get_domain(self) -> Domain:
        return Domain.Voice

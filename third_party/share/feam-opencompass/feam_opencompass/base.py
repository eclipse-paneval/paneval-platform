from typing import List, Dict, Any, Optional

from feam.models import TaskMetric, Stat, Language
from feam.nlp import NLPBaseScenario


class OpenCompassBaseScenario(NLPBaseScenario):
    def summarize(self, metrics: List[TaskMetric]) -> Stat:
        details = [
            {
                'key': x.raw['key'],
                'results': x.raw['results'],
                'accuracy': self._find_acc(x.raw['key'], x.raw['results']),
            }
            for x in metrics
        ]
        accs = [x['accuracy'] or 0 for x in details]
        return Stat(
            accuracy=sum(accs) / len(accs) if len(accs) > 0 else 0,
            robustness=0,
            fairness=0,
            bias=0,
            calibration=0,
            details=details,
        )

    @staticmethod
    def _find_acc(key: str, results: List[List[Dict[str, Any]]]) -> Optional[float]:
        for raw in results:
            for item in raw:
                if item['metric'] in ['score', 'humaneval_pass@1']:
                    for v in item.values():
                        try:
                            v = float(v) / 100.0
                            return v
                        except:
                            continue

        return None

    def get_language(self) -> Language:
        return Language.any_

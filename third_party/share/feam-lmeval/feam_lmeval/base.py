from typing import List, Dict, Any, Optional

from feam.models import TaskMetric, Stat
from feam.nlp import NLPBaseScenario


class LMEvalBaseScenario(NLPBaseScenario):
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
    def _find_acc(key: str, results: List[Dict[str, Any]]) -> Optional[float]:
        for raw in results:
            result = raw.get('results') or {}
            if key in result and isinstance(result[key], dict):
                score_keys = ["acc,none", "exact_match,none","exact_match,strict-match","exact_match,flexible-extract","exact_match,custom-extract","acc_norm,none"]
                for k in score_keys:
                    v = result[key].get(k)
                    if v is not None:
                        return v

        return None

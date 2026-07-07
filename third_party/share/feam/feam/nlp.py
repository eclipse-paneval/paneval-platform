import json
from typing import Optional, Dict, Any

import requests

from feam import models


class NLPBaseScenario(models.Scenario):
    @property
    def model(self) -> str:
        return self.options.model

    @property
    def max_eval_instances(self) -> int:
        return self.options.extras.get("max_eval_instances") or 1000

    @property
    def dry_run(self) -> bool:
        return self.options.extras.get("dry_run") or False

    @property
    def tokenizer(self) -> Optional[Dict[str, Any]]:
        return self.options.extras.get("tokenizer")

    def get_domain(self):
        return models.Domain.NLP

    @staticmethod
    def get_model_name(url: str) -> Optional[str]:
        raw_request = {
            "engine": 'aquila',
            "prompt": '你好',
            "temperature": 0.1,
            "num_return_sequences": 1,
            "max_new_tokens": 5,
            "top_p": 1,
            "echo_prompt": False,
            "top_k_per_token": 1,
            "stop_sequences": [],
        }
        try:
            # response = requests.post(url, json=json.dumps(raw_request))
            response = requests.post(
                url,
                json=json.dumps(raw_request),
                headers={
                    "Authorization":"#e7sYA3M&#9A#^nihtJh9FRpXX_woK0OulJgfAI9sogZL+lQXM0n9VQlzC#4_p&Th&",
                },
            )
        except:
            return None
        if response.status_code == 200:
            return response.json().get("model_info", None)
        return None

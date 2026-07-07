from typing import List

from feam.models import Task, Meta, Language

from .base import OpenCompassBaseScenario
from .opencompass import OpenCompassTask


class CodeScenario(OpenCompassBaseScenario):
    def create_tasks(self) -> List[Task]:
        return [
            OpenCompassTask(
                Meta(
                    name='humaneval',
                    description='',
                    server_url=self.options.server_url,
                ),
                model=self.model,
                tasks='humaneval',
            ),
            OpenCompassTask(
                Meta(
                    name='mbpp',
                    description='',
                    server_url=self.options.server_url,
                ),
                model=self.model,
                tasks='mbpp',
            ),
        ]

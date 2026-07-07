from importlib.metadata import entry_points
from typing import Dict, Type

from .models import Domain, Options, Scenario


def load_scenario_classes(domain: Domain) -> Dict[str, Type[Scenario]]:
    """Load all scenarios from entry points."""
    group = f'feam.scenario.{domain.value.lower()}'

    scenario_clses: Dict[str, Type[Scenario]] = {}

    eps = entry_points()[group]
    for item in eps:
        cls = item.load()
        scenario_clses[item.name] = cls

    return scenario_clses


def load_nlp_scenarios(options: Options) -> Dict[str, Scenario]:
    return {k: cls(options) for k, cls in load_scenario_classes(Domain.NLP).items()}


def load_nlp_scenario(entry_point: str, options: Options) -> Scenario:
    return load_nlp_scenarios(options)[entry_point]

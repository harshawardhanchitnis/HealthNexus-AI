"""Bounded process-local demo store. No baseline persistence or disk writes."""
from threading import RLock
from app.core.risk_config import MAX_SCENARIOS


class ScenarioStore:
    def __init__(self):
        self.lock = RLock()
        self.results = {}

    def put(self, result):
        with self.lock:
            if len(self.results) >= MAX_SCENARIOS:
                raise ValueError(f"Scenario limit ({MAX_SCENARIOS}) reached. Discard an existing scenario first.")
            self.results[result.scenario.scenario_id] = result

    def get(self, scenario_id, country):
        with self.lock:
            result = self.results.get(scenario_id)
            if result is None or result.scenario.definition.country_id != country:
                raise LookupError("Scenario not found in selected country; discarded scenarios and process restarts remove results")
            return result.model_copy(deep=True)

    def discard(self, scenario_id, country):
        with self.lock:
            self.get(scenario_id, country)
            del self.results[scenario_id]

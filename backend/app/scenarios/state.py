"""Bounded process-local demo store. No baseline persistence or disk writes."""
from threading import RLock
from app.core.risk_config import MAX_SCENARIOS
from app.core.runtime import low_memory


class ScenarioStore:
    def __init__(self):
        self.lock = RLock()
        self.results = {}
        self.limit = 4 if low_memory() else MAX_SCENARIOS

    def put(self, result):
        with self.lock:
            if len(self.results) >= self.limit:
                raise ValueError(f"Scenario limit ({self.limit}) reached. Discard an existing scenario first.")
            self.results[result.scenario.scenario_id] = result

    def get(self, scenario_id, country, profile="constrained"):
        with self.lock:
            result = self.results.get(scenario_id)
            if result is None or result.scenario.definition.country_id != country or result.scenario.definition.profile != profile:
                raise LookupError("Scenario not found in selected country; discarded scenarios and process restarts remove results")
            return result.model_copy(deep=True)

    def discard(self, scenario_id, country, profile="constrained"):
        with self.lock:
            self.get(scenario_id, country, profile)
            del self.results[scenario_id]

"""Verifier-only daily ledger. Reserve BEFORE transport, including retry attempts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from app.ai.client import CopilotError


class RequestBudget:
    def __init__(self, limit=10, ledger=None):
        if not 1 <= limit <= 10:
            raise ValueError('Verification budget must be between 1 and 10')
        self.limit, self.ledger = limit, Path(ledger) if ledger else None
        self.used, self.lock = 0, RLock()
        self.day = datetime.now(timezone.utc).date().isoformat()
        if self.ledger and self.ledger.exists():
            saved = json.loads(self.ledger.read_text(encoding='utf-8'))
            if saved['day'] == self.day:
                self.used = int(saved['used'])

    def consume(self):
        with self.lock:
            if self.used >= self.limit:
                raise CopilotError('quota_budget_exhausted_locally',
                    'Verification request budget exhausted locally; no provider request was sent.', 429)
            self.used += 1
            if self.ledger:
                self.ledger.parent.mkdir(parents=True, exist_ok=True)
                temp = self.ledger.with_suffix('.tmp')
                temp.write_text(json.dumps({'day':self.day, 'used':self.used}), encoding='utf-8')
                temp.replace(self.ledger)

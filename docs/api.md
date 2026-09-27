# API

Interactive OpenAPI: http://127.0.0.1:8000/docs

| GET endpoint | Purpose |
| --- | --- |
| `/api/health` | Readiness, active store, country, snapshot date |
| `/api/regions` | All 36 regions and illustrative districts |
| `/api/overview` | Resource totals, regional summaries, 28-day trend, top six alerts |
| `/api/facilities` | Searchable, paginated facility summaries |
| `/api/facilities/{id}` | Inventory balances, beds, staff, history and alerts |
| `/api/inventory` | Medicine totals and local shortage counts |
| `/api/alerts` | Scoped deterministic stock and attendance alerts |

Overview, facilities, inventory and alerts accept optional `state_id` and `district_id`. IDs come from `/api/regions`. A district must belong to the selected state. Invalid scopes return 404, malformed parameters 422, unavailable stores 503 with sanitized error text.

Facilities additionally accept `search`, `status`, `offset` (>=0) and `limit` (1–250). Alerts accept `severity`. Status enums: `HEALTHY`, `WATCH`, `AT_RISK`, `CRITICAL`.

Examples:

```text
/api/overview?state_id=MH&district_id=MH-PUNE
/api/facilities?state_id=MH&search=Pune&limit=15
/api/alerts?state_id=MH&severity=CRITICAL
```

There are no write, forecasting, AI or simulator APIs in this phase.

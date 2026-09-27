# Validation — 2026-09-27

## Executed successfully

- `python -m pytest backend -q`: **13 passed**. Covers all 36 regions, reproducible generation, unique facility IDs, inventory/bed/staff conservation, threshold boundaries, national rollups, district scoping, search, validation and sanitized storage failures.
- `npm run build`: **passed**, no build warnings after final layout changes. Initial bundle approximately 324 kB raw / 92 kB transfer.
- Live local backend at `127.0.0.1:8000`, frontend at `127.0.0.1:4200`, with real `/api` calls through the Angular proxy.
- Browser: national dashboard renders 207 facilities; Maharashtra narrows to six, Pune to three. Facility detail shows reconciled inventory, beds, attendance and history.
- Browser: nonexistent facility search produces a clean zero-result state; pagination changes 1–15 to 16–30 of 207.
- Browser: national medicine totals render all five medicines; Pune's empty alert state and national 221-alert view render correctly, with rule explanations.
- Responsive browser check at 390 × 844: overview cards, scope selectors and mobile navigation work; table pages retain horizontal scrolling inside their panel.
- Browser console: no captured errors during final checks.
- Snapshot generated with seed 42 and as-of date 2026-09-27.

Screenshot: [overview](screenshots/overview.png).

## Limits of verification

- Pytest emits one upstream Starlette/AnyIO deprecation warning; test results pass.
- Firestore adapter is implemented but has not been exercised against a live or emulator project. No cloud upload or deployment performed.
- Container/Firebase configurations are scaffolds and have not been deployed or tested with Docker here.
- No ML forecasts, OR-Tools solves, Gemini responses or FedAvg rounds were executed; those features are subsequent milestones.
- Browser checks were interactive checks, not a committed automated end-to-end test suite.

# Status

Release baseline:
- `README.md` describes the current public release (v2.0).

In progress (v2.1+):
- Config-flow updates to support new filtering logic for sensor state and calendar summaries  (see design contracts).

Known gaps and TODO (summary):
- Config-flow discovery is incomplete (see `docs/todo.md`).
- DayFilter schema and ordering are not fully aligned with contracts.
- Logging lacks contract-required context.
- Auto meal focus can mix meals when no Lunch is found.

References:
- Task list: `docs/todo.md`
- Legacy TODO notes: `TODO`
- UC catalog: `test/fixtures/usecases.json`

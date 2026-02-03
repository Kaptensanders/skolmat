This file is the canonical guardrails + pointers for Codex work in this repo.

## Project overview
- `docs/overview.md`
- `README.md` (end-user docs for release v2.0; may lag behind dev)

## Current status
- `docs/status.md`

## Ongoing tasks
- `docs/todo.md`
- `TODO`

## Setup
- `docs/setup.md`

## Architecture
- `docs/architecture.md`

## Design contracts (immutable)
- `docs/design/filtering-contract.md`
- `docs/design/config-flow-contract.md`
- `docs/design/calendar-contract.md`
- `docs/design/sensor-contract.md`

## Context for Codex
- `docs/context.md`
- `docs/decisions.md`
- `test/fixtures/usecases.json` (UC catalog)

## Legacy references
- `docs/resume_prompt.txt` (legacy backup)
- `docs/design/filtering-design-checkpoint.md` (legacy backup)
- `docs/design/filtering-config-flow-design.md` (legacy backup)
- `docs/vibe/context.md` (legacy, empty)

## Project file structure (in-file)
- `custom_components/skolmat/`: Home Assistant integration code.
- `custom_components/skolmat/processors/`: optional per-source normalizers.
- `skolmat-card/`: Lovelace card submodule.
- `docs/`: working docs and design contracts.
- `test/`: fixtures and tests (including UC catalog).

## Devcontainer model (in-file)
- `.devcontainer/devcontainer.json` uses image `hass_dev_image_2025.12.2`.
- Post-create runs `container setup-project` -> `.devcontainer/setup-project`.
- Mounts `skolmat-card/` into HA config `www/`.
- Bootstraps HA `.storage` from `.devcontainer/ha_config_bootstrap/.storage`.
- Ports: 8123 (HA) and 5678 (debugpy).

## Generic guardrails (in-file)
- Do not modify design contracts unless explicitly requested.
- Treat `test/fixtures/usecases.json` as ground truth. All implemented logic should be represented in this file. Suggest updates when neccesary.
- Don’t refactor entire architecture without approval.
- Never refactor code outside of the currently discussed scope.
- Only run code generation related to current file / feature.
- Prefer small, reviewable changes; avoid sweeping reformatting.
- Update or add tests when behavior changes; call out gaps explicitly if not possible. Suggest additions/updates to `test/fixtures/usecases.json` as needed.
- When requirements are unclear, pause and ask one question at a time before coding.
- Keep dev docs in `docs/` aligned with actual behavior; do not update end-user docs (`README.md`) unless requested.
- Avoid editing legacy backups unless explicitly asked.
- Use UTF-8 when Swedish terms or data require it; do not force ASCII where it harms clarity.
- Log important decisions in `docs/decisions.md` without waiting for confirmation.
- Dont overengineer things, keep it simple when possible
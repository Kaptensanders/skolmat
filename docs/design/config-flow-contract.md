# Skolmat filtering config flow contract (v2.1+)

This document captures the immutable design contract for the Home Assistant
config/options flow that sets up menu summary filtering.

It is intended to sit alongside `docs/design/filtering-contract.md` and should be
kept consistent with it.

**Immutable rule:** Do not change this file unless explicitly requested by the user.

**Conflict rule:** If this doc conflicts with `docs/design/filtering-contract.md`,
the filtering contract wins unless explicitly superseded by the user.

---

## 1. Design principles

- Progressive disclosure: start simple, reveal advanced settings only when needed.
- Trust over cleverness: avoid hidden logic or silent truncation.
- Deterministic output: same config + input => same summary.
- Safe fallbacks: never return an empty summary when entries exist.
- Preview-first: show a concrete summary preview wherever possible.

---

## 2. Flow overview (config vs options)

### 2.1 Initial config flow (new integration)

Step A: Basic connection
- Fields: `name`, `url` (or provider-specific fields if applicable).
- Optional: "Test connection" on submit; show friendly error if fetch fails.

Step B: Discovery + meal selection
- Fetch menu for "today" (or nearest available day).
- Derive discovered meals + labels (post-processor if configured).
- Show a preview summary for the current selection.

Step C: Meal selection
- Show discovered meal list (multi-select).
- Allow empty selection; explain that empty means all meals.

Step D: Advanced (optional, collapsible)
- Exclusions:
  - Keyword/regex patterns (single list).
  - Matches both label and dish.
- Preferences:
  - Keyword/regex patterns (single list).
  - Matches both label and dish.
- N max cap (opt-in, empty means unlimited).
- Custom processor (hidden behind "Power user" toggle):
  - File name (no path) under `custom_components/skolmat/processors/`.
  - Function name within that module.
  - "Reload menu" button to re-run discovery using the processor and repopulate
    meals/labels + preview.

Step E: Summary preview
- Show a preview of the resulting day summary string using the selected config.
- Include a "view full menu" (read-only) to emphasize that full data remains available.

Step F: Save
- Save config entry, then navigate to device page as usual.

### 2.2 Options flow (editing an existing config)

Options should mirror config flow but start at "Meals + Filters".

Step A: Discovery refresh
- Fetch "today" and refresh discovered meals/labels.
- Provide a refresh button to re-run discovery (useful if the provider changed).
- If processor settings changed, the refresh uses the processor and repopulates
  meals/labels + preview.

Step B: Meal scope
- Same as Step B/C above; preserve previous selections where possible.
- If previous meal selection is no longer present, show it with a warning tag
  and allow removal or keep (it will fall back to all meals for that day).

Step C: Advanced + Preview
- Same as Step D/E above.

---

## 3. UI details (copy and guardrails)

### 3.1 Warnings and transparency
- If exclusions would remove all entries, show non-blocking warning:
  "Rule skipped: would remove all entries."
- If N is set: "N is a maximum, not a target; no cross-meal fill."
- If selection has no matches: "No entries matched today; showing all meals."

### 3.2 Discovery preview
- Short preview string (same as sensor state format).
- Show count: "3 entries from Lunch (2 labels detected)."
- If discovery fails: show an error and return to the URL step.

### 3.3 Processor inputs (advanced)
- Inputs:
  - File name only (example: `my_processor.py`).
  - Function name only (example: `process_entries`).
- Validation:
  - Verify file exists under `custom_components/skolmat/processors/`.
  - Verify function exists and is callable.
  - If invalid, show inline error and keep discovery in "raw" mode.
- Reload:
  - "Reload menu" re-fetches and reprocesses using the provided processor,
    then repopulates meals/labels and preview.
- Execution failure:
  - If the processor raises, the default loading behavior applies for that entry.
  - Use the freshly loaded menu (post-fallback) to populate discovery and preview.

---

## 4. Data model (config entry fields)

Use only ASCII keys and keep fields stable for migration.

Core:
- `name`: string
- `url`: string (or provider-specific config)

Custom scope:
- `meals_selected`: list of strings (meal names)

Filters:
- `exclude_regex`: list of keyword/regex patterns
- `prefer_regex`: list of keyword/regex patterns

Optional:
- `max_entries`: integer or null
- `processor_file`: string (filename under `custom_components/skolmat/processors/`) or null
- `processor_fn`: string (callable function name) or null

Notes:
- Treat "" like `null` for labels.
- Avoid storing derived data like discovered meals/labels.

---

## 5. Discovery behavior

- Source day: prefer today; if no menu, pick the closest future day.
- Post-process entries if a processor is configured and valid.
- Normalize meals/labels before presenting.
- Block save on discovery failure; return to the URL step with a warning.
- If processor validation fails, show errors and allow a raw discovery fallback.

---

## 6. Preview generation rules

- Apply the same pipeline as production:
  - Phase A: meal focus.
  - Phase B: exclusions, then preferences.
  - Phase C: N cap (if set).
- If a valid processor is configured, preview uses processed entries.
- Preview must never be empty when entries exist.
- Explicitly note when a fallback happened.

---

## 7. Open questions (to resolve before implementation)

- Should we store a "last successful discovery date" for easier debugging?
- Should the preview allow switching between "today" and another day?
- Should the processor be applied before or after any provider-specific cleanup?

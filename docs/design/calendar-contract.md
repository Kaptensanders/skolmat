# Skolmat calendar design contract (v2.1+)

This document is the immutable design contract for the calendar entity behavior
in the Home Assistant custom integration **skolmat** (v2.1+).

**Immutable rule:** Do not change this file unless explicitly requested by the user.

**Conflict rule:** If this file conflicts with the filtering contract on summary
selection, the filtering contract wins unless explicitly superseded by the user.

---

## 1. Purpose

The calendar entity provides one event per day for past and upcoming menus. It
exposes a short summary in the event title and a full menu in the description.

---

## 2. Event content

- **Event summary (title):** Uses the filtered daily summary output (see
  `docs/design/filtering-contract.md`).
- **Event description:** Contains the full formatted day menu (unfiltered). This is
  the safe place for completeness.
- The summary should stay short and conservative; the description holds the full
  context.

---

## 3. History policy (LOCKED)

Past calendar summaries should not be rewritten.

Changes apply from "today and forward".

---

## 4. Dependencies

- Summary selection: `docs/design/filtering-contract.md`
- Sensor truth source (full menu attributes): `docs/design/sensor-contract.md`

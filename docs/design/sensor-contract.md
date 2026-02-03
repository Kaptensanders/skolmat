# Skolmat sensor design contract (v2.1+)

This document is the immutable design contract for the sensor entity behavior
in the Home Assistant custom integration **skolmat** (v2.1+).

**Immutable rule:** Do not change this file unless explicitly requested by the user.

**Conflict rule:** If this file conflicts with the filtering contract on summary
selection, the filtering contract wins unless explicitly superseded by the user.

---

## 1. Purpose

The sensor entity exposes the daily menu summary in its state while preserving
full structured menu data in its attributes.

---

## 2. State vs attributes (truth)

- **State:** A short daily summary produced by the filtering pipeline.
- **Attributes:** The full structured menu is always preserved here and is the
  truth source for cards, power users, and calendar descriptions.

---

## 3. Output constraints

- The state summary is short and conservative.
- The summary must never hide the existence of the full menu in attributes.
- `Menu.getMenu` returns a valid `MenuData` or `None`.
- `None` means the current data is invalid and the fetch failed.
- When `None`, the entity should be set to unavailable (Home Assistant best practice).

---

## 4. Dependencies

- Summary selection: `docs/design/filtering-contract.md`

# Skolmat card design contract (v2.1+)

This document is the immutable design contract for the Lovelace custom card
behavior in the Home Assistant custom integration **skolmat** (v2.1+).

**Immutable rule:** Do not change this file unless explicitly requested by the user.
**Immutable rule:** Do not modify `skolmat-card/skolmat-card.legacy.js`; it is an immutable backup used only for reference.

**Conflict rule:** If this file conflicts with filtering or sensor contracts,
those contracts win unless explicitly superseded by the user.

Related contracts:
- `docs/design/sensor-contract.md`
- `docs/design/filtering-contract.md`
- `docs/design/calendar-contract.md`

---

## 1. Purpose

The card renders the full daily menu from the sensor attributes for visual
inspection and comparison. The card is not a summary view; it should remain
truthful to the structured menu data.

Implementation posture:
- Keep logic simple and readable; avoid boilerplate layers unless the code gets
  messy or repeated.
- Prefer short, explicit logic over clever chaining.
- Include structured debug logging for this phase, keyed per card instance.

---

## 2. Truth source and data shape

- The card must read data from the sensor entity attributes.
- The authoritative menu data is the ISO-date keyed map stored in
  `attributes.calendar` (aka `MenuData`).
- The map format is: `{ "YYYY-MM-DD": [MenuEntry, ...] }`.

`MenuEntry` fields:
- `dish` is the primary display value.
- `meal` and `label` may be present and are supported by the card.
- `meal_raw` and `dish_raw` are deprecated and must be ignored.

---

## 3. Time scopes and week handling

### 3.1 Today view
- Match today using local time.
- Find the entry for today's ISO date.
- If no entry exists, render a no-menu message (do not fall back to week view).

### 3.2 Week view
- The data is no longer week-keyed.
- The card must compute week numbers from ISO dates and group data by week.
- Default week view is the current ISO week (Monday-based).
- The header should preserve the prior UI semantics with localization
  (for example, "Meny vNN" in sv, "Menu wNN" in en).
- Render Monday–Friday by default. If Saturday/Sunday entries exist for the week,
  render those days too, but do not emit "no menu" placeholders for weekend days
  that are missing.

### 3.3 Rolling-week view
- Rolling week is a forward-looking slice from today.
- Include up to N days with menu entries starting from today, where N is `rolling_week_max_days`.
- Do not render placeholder days without menu entries in rolling-week view.
- Header and date range should match prior rolling-week behavior (no week number
  in the header).

---

## 4. Rendering rules

- Render each day in chronological order.
- Weekday names are computed from ISO dates and localized to the current HA language.
- Dishes are grouped under their `meal` for the day (meal group headers may be hidden).
- For each meal group, render dishes in stored order.
- Meal headers are bold and styleable via CSS.
- Dish labels are styleable via CSS, with default styling matching dish text.
- If the entity does not exist, render a standard "missing entity" configuration
  error card (matching other HA cards).
- If the entity exists but is `unavailable`, or the attributes are invalid,
  render the normal card and header with content text `cannot load menu`.
- If valid menu data exists, render the view as usual and display
  `No menu available` under each day that has no entries.

---

## 5. No-menu message (localization)

- The no-menu message should be localized to match the current HA language
  when possible.
- Prefer using `hass.localize(...)` with a sensible built-in key and fallback.
- All static strings in the card should be localized when possible.
- Fallback strings:
  - `No menu available` (day-level empty data)
  - `cannot load menu` (entity unavailable or invalid attributes)

---

## 6. Backwards-compatibility

- The card must remain compatible with existing config options:
  `menu_type`, `header`, `header_font`, `header_fontsize`,
  `show_dates`, and `rolling_week_max_days`.
- New config options:
  - `show_meals`: `none`, `always`, `if-multiple` (default: `if-multiple`)
  - `show_dish_labels`: `none`, `always`, `if-multiple` (default: `if-multiple`)

## 7. Implementation notes

- Modernize the LitElement access to align with current HA best practices.
- Debug logging must include a stable per-card key to correlate output when
  multiple cards are rendered.
- Keep non-functional improvements aligned with simplicity:
  - Add clear CSS hooks and variables for card styling.
  - Follow HA theming best practices (e.g., `ha-card`/theme variables).
  - Prefer lightweight memoization if repeated processing becomes costly.
  - Provide basic accessibility affordances (labels/structure).
  - When menu data is empty or malformed, show a clear message instead of
    silently rendering empty output.

### 6.1 Meal rendering
- Meals are always used as grouping buckets.
- `show_meals` controls whether the meal name is shown:
  - `none`: never show meal name.
  - `always`: always show meal name.
  - `if-multiple`: show only if more than one distinct meal exists for the day.
- Entries with missing/empty `meal` are grouped under a hidden bucket that never
  renders a meal header, regardless of `show_meals`.

### 6.2 Dish label rendering
- Labels are only shown if present and non-empty.
- `show_dish_labels` controls whether the label is shown:
  - `none`: never show labels.
  - `always`: show label when present.
  - `if-multiple`: show labels only if multiple distinct labels exist for the meal.

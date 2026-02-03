# Skolmat v2.1+ filtering design checkpoint (authoritative)

This document is the authoritative checkpoint for the menu summary filtering design in the Home Assistant custom integration **skolmat** (v2.1+).

Its purpose is to preserve **decisions, rationale, constraints, requirements, and the mental model** so work can resume later without re-deriving context or re-litigating prior conclusions.

**Conflict rule:** If this file conflicts with later conversation snippets or partial drafts, this file wins **unless explicitly superseded by a newer checkpoint**.

**Important supersession note:** Earlier drafts stated a default N cap. That is now **explicitly superseded**:  
✅ **No default cap.** N (max cap) is always **opt-in**.

---

## 0. Why this exists

### 0.1 The reality: providers are messy and inconsistent
Menu providers and institutions encode daily menus in inconsistent ways. Institutions often **misuse** or overload the “meal/category/option” concepts:

- Sometimes `meal` contains both meal and variant (e.g. `"Lunch husman"`, `"Lunch timbal"`).
- Sometimes `meal="Lunch"` and `label` carries variant (`"Husman"`, `"Vegetariskt"`, etc.).
- Sometimes there is no “Lunch” bucket at all (e.g. `"Alt 1"`, `"Kökets rätt"`, `"Måltid 1"`).
- Sometimes non-main items appear as dishes (side items, bread, condiments, info messages).
- Sometimes meals are split (Lunch + Dessert) or expanded (Lunch + Dinner), and variants appear as separate “meals”.
- These structures are usually **stable day-to-day** per institution, but may change; when they change, users can reconfigure.

**Key insight:** We cannot rely on a single canonical provider schema. We must treat **meal**, **label**, and **dish** as best-effort signals that vary by institution, and we must prioritize user trust over clever inference.

### 0.2 What users need (and where)
Skolmat serves multiple UX surfaces with different constraints:

- **Sensor attributes (structured truth):** The full structured menu (all entries) is always available in attributes for cards and power users.
- **Sensor state (short):** A short “today summary” suitable for entity state (historically truncated to 255 chars).
- **Calendar event summary (short):** A concise summary that makes sense in HA calendar list views.
- **Calendar event description (full):** A full formatted day menu; this is the “safe place” to include everything.
- **Lovelace card:** Uses the full structured menu from attributes and can apply its own presentation/filtering later.

### 0.3 Primary goal of filtering
Filtering exists primarily to produce a **short, sane, non-embarrassing daily summary** for:
- the sensor state, and
- the calendar event summary.

Filtering must be:
- **Honest / transparent:** Do not silently hide menu items by default in a way users cannot understand.
- **Deterministic:** Same input + same config → same output.
- **Conservative:** Prefer “less filtered” over “wrong” when uncertain.
- **Configurable:** Advanced users can opt into tighter behavior via explicit settings.

**Perfect inference is not required.** “Good enough and appreciated” is the bar. If filtering can’t confidently improve output, it should back off rather than mislead.

---

## 1. Canonical reference: UC JSON (ground truth)

A canonical **Use Case catalog** exists as JSON using the real v2.1 `MenuEntry` shape. It is the ground truth for reasoning, validation, and tests.

Rules:
- Use the UC catalog to validate any new filtering logic or edge-case decisions.
- When resuming work, always ensure the UC JSON is available (preferably stored in-repo and referenced).
- When new real-world patterns appear, extend the UC catalog rather than “patching” behavior ad hoc.

### 1.1 The UC catalog reflects real corpus distinctions
The UC catalog was derived from real log output from multiple institutions and configurations and includes critical distinctions such as:

- generic/opaque meal names used as multiple buckets vs a single bucket
- “exploded” institutions (diet variants encoded as meals) vs “normalized” (variants encoded as labels)
- separate buckets such as Lunch + Dessert, Lunch + Dinner, etc.

---

## 2. Data model in scope (v2.1)

### 2.1 MenuEntry (one dish/line item)
`MenuEntry` is the normalized internal representation produced by providers (and optionally post-processed by a processor):

```json
{
  "meal_raw": "Lunch husman",
  "meal": "Lunch",
  "dish_raw": "Kyckling ...",
  "dish": "Kyckling ...",
  "label": "Husman",
  "order": 1
}
```

Field intent and constraints:
- `meal_raw`: provider’s original meal/category string (may include variants and noise).
- `meal`: normalized meal bucket (best effort).
- `dish_raw`: original dish string.
- `dish`: cleaned/normalized dish string.
- `label`: variant/option label (best effort).
  - `label` may be `null` or `""`. Treat `""` exactly like `null`.
- `order`: stable ordering key within the day/meal (also used as deterministic tie-breaker).
- **Post-normalization:** `meal` and `label` are post-normalization (and optionally post-processor).
- **Truth availability:** Full menu is always accessible via sensor attributes; summary filtering never removes access to the full menu.
- **Calendar description:** Calendar event description can (and should) contain the full readable day menu.

### 2.2 What filtering receives as input
Filtering operates on the list of `MenuEntry` objects for a **single day** and within whatever meal scope the upstream caller provides. Filtering must not assume providers are consistent beyond what is present in the entries.

---

## 3. High-level architecture: two outputs, one truth

### 3.1 One truth source
The sensor attributes contain the full structured menu (all entries). This is the truth and is used by:
- the Lovelace card (primary richer UI),
- power users,
- future richer presentations.

### 3.2 Two short outputs derived from the truth
Two “short” outputs are derived from the truth:
- Sensor state: concise summary
- Calendar event summary: concise summary

The calendar event description is **not** constrained: it should contain the full formatted day menu.

Therefore:
- summary selection must be **opinionated** and **trustworthy**
- but also **transparent** (avoid silent hiding by default)

---

## 4. Locked decisions (do not reopen unless explicitly revising)

This section contains decisions that should not be changed casually. If a decision is revised, update this checkpoint explicitly.

### 4.1 No mode; meal selection only (LOCKED)
Filtering does not use an explicit `mode`. Meal selection is the only scope control.

- If meal selection is empty, **all meals are in scope**.
- If meals are selected, they define a hard boundary.

### 4.2 Processor is a last resort (power user tool) (LOCKED)
Processor modules can normalize broken upstream data (e.g. convert “Lunch husman” → meal “Lunch”, label “Husman”).

However:
- processors are advanced and increase maintenance,
- most users should succeed using discovered values + filters,
- processors should be positioned as **last resort** and **opt-in**.

### 4.3 N cap semantics: maximum, not a target (UPDATED, LOCKED)
N is a max number of entries shown; never a target.

- N is a **MAX**, never “fill to N”.
- Never “fill up to N” by pulling entries from other meals.
- If fewer entries exist after focus + filtering, return fewer.
- **Default:** N is disabled (unlimited).
- N is always opt-in.

Rationale (UX-first):
- Avoid silent truncation (users should not wonder where dishes went).
- If output is too noisy, users explicitly opt into advanced behavior.

### 4.4 Determinism and safety invariants (LOCKED, non-negotiable)
- **Never mix meals unintentionally.** No cross-meal spillover to satisfy N or preferences.
- **Never output empty when input is non-empty.** Filtering cannot erase the day; it must degrade gracefully.
- **Deterministic output.** Stable ordering, stable tie-breakers, stable behavior given same inputs.
- **Transparency via logging.** When a rule is skipped or a fallback happens, log clearly with enough context to diagnose.

### 4.5 Calendar history policy (LOCKED)
Past calendar summaries should not be rewritten.

Changes apply from “today and forward”.

---

## 5. Selection pipeline (locked phases)

Daily summary selection is a pipeline of phases:

### Phase A — Meal focus
Decide which entries are eligible by selecting a meal scope.

- If meals are selected, they form a hard boundary.
  - **Fallback guarantee:** If the selection matches nothing (e.g. provider changed), fall back to all entries for that day and log clearly.
- If no meals are selected, keep all entries.

**Hard rule:** After Phase A, the meal scope is fixed for the rest of the pipeline.

### Phase B — Filtering within focus (LOCKED ORDER)
Within the focused entries, apply:

1) Exclusions (progressive guarded removal)  
2) Preference ranking (ordering only; never removes)

### Phase C — Apply N (max cap)
Apply optional N cap to ranked results.

Must obey invariants:
- no cross-meal fill,
- no empty output.

---

## 6. Phase B details (locked behavior)

### 6.1 Exclusions (progressive and guarded)
Exclusions may be expressed as:
- selections from discovered labels (label-first UI)
- regex patterns (advanced)
- targets: label and/or dish (depending on config; default should be label-first for UX)

Progressive guarded algorithm (LOCKED):
- Apply exclusion rules one by one, in configured order.
- A rule is applied only if at least one entry remains.
- If applying a rule would empty the result:
  - skip that rule
  - log: “rule skipped; would remove all entries”
- Earlier rules are higher priority than later rules.

This preserves intent while preventing empty output.

### 6.2 Preferences (ranking only)
Preferences may be expressed as:
- selections from discovered labels
- regex patterns
- targets: label and/or dish

Rules (LOCKED):
- Preferences NEVER remove entries.
- Preferences adjust ranking only.
- Multiple preferences can stack.
- Tie-breaker is deterministic: original order ascending.

---

## 7. UX constraints (guiding requirements)

Goal: good UX without overwhelming users.

### 7.1 Progressive disclosure in config/options flow
Default path:
- URL, name

Custom path:
- show discovered meal list
- user selects one or more meals (hard boundary)

Advanced (optional):
- exclusions (label list + regex)
- preferences (label list + regex)
- optional N max cap
- optional processor module selection (power user)

### 7.2 Discovery step requirement
During config flow (or options flow), the system should:
- load menu
- derive discovered meals/labels (post-processor if configured)
- present those as selectable options
- ideally show a preview of resulting summary for “today”

---

## 8. Logging requirements (LOCKED, explicit)

When something is skipped, falls back, or degrades, log clearly with enough context to diagnose, without spamming.

### 8.1 What must be logged
Include:
- configuration entry identifier (school name or a stable URL hash)
- day/date
- which rule was skipped (and why)
- what meal focus was used (Phase A result)
- compact dump of relevant entries (or summarized counts)

### 8.2 Anti-spam guidance
Avoid log spam:
- Prefer one log per (day, rule) event.
- If needed, store a “last log key” in memory to suppress repeats.

---

## 9. Glossary (to avoid future ambiguity)

- **Meal focus:** Which meal groups are eligible for summary selection (Phase A).
- **Exclusion:** Removes entries (Phase B.1), but guarded to never empty output.
- **Preference:** Ranks entries only (Phase B.2), never removes.
- **N cap:** Max entries shown (Phase C), never forces fill, never crosses meals.
- **Processor:** Optional per-entry hook to normalize upstream misuse; power user last resort.
- **Summary:** Short string for sensor state / calendar event summary.
- **Description:** Full formatted day menu (calendar event description), can include multiple meals.

---

## 10. Testing philosophy (practical enforcement)

Primary validation should be end-to-end tests that exercise the real summary path:

- Create menus via `Menu.createMenu(...)`
- Inject processed `MenuEntry` data (fixture snapshots)
- Apply filters via `Menu.setSummaryFilters(...)`
- Assert via `Menu.getReadableDaySummary(...)`

Guidance:
- Unit testing `DayFilter` directly is optional and generally less valuable than verifying user-visible outputs.
- Use-case catalog JSON is the reasoning ground truth.
- Real snapshot data is the regression corpus.

---

## 11. Explicitly out of scope (guardrails)

To avoid “clever” behavior that becomes misleading:
- inferring meals or variants beyond provided data
- automatic merging/splitting of meals
- semantic understanding of dishes (“this is probably dessert”)
- hidden heuristics that users cannot see
- overuse of processors

---

**End of checkpoint.**

# Decision log

This is the running log of important decisions for this repo.

Rules:
- Add an entry for any decision that changes behavior, architecture, or design contracts.
- Keep entries short, dated, and reference the relevant docs/files.

Template:
- Date: YYYY-MM-DD
- Decision: <one-line summary>
- Context: <why this was needed>
- Impact: <what changes or constraints follow>
- References: <paths, issues, or PRs>

- Date: 2026-01-24
- Decision: Implement discovery keyword derivation with UI help text and low-signal day skipping.
- Context: Config flow discovery needs meals/labels, and holiday-only days can yield empty keyword lists without user feedback.
- Impact: `Menu.getSummaryFilterKeywords` now returns UI info strings, logs the chosen day's entries, and searches for the first day with meal/label keywords before falling back.
- References: custom_components/skolmat/menu.py, docs/design/config-flow-contract.md

- Date: 2026-01-24
- Decision: Detect and warn when discovery keywords differ across days.
- Context: Config flow discovery is based on a single day and may miss meals/labels present on other days.
- Impact: Discovery now cross-checks the full menu for extra keywords, logs them clearly, and adds a short warning to the UI info text.
- References: custom_components/skolmat/menu.py

- Date: 2026-01-24
- Decision: Allow keyword discovery to accept an optional reference date.
- Context: Tests and config flow can pass a specific date to drive discovery; default remains today.
- Impact: `Menu.getSummaryFilterKeywords` now accepts `reference_date` and falls back to `date.today()` when omitted.
- References: custom_components/skolmat/menu.py

- Date: 2026-01-24
- Decision: Remove advanced discovery help text from keyword payload.
- Context: Advanced guidance will live in config flow UI for localization instead of being returned from `Menu.getSummaryFilterKeywords`.
- Impact: Discovery now returns only meals, labels, and an info string; UI provides static advanced help text.
- References: custom_components/skolmat/menu.py, custom_components/skolmat/config_flow.py

- Date: 2026-01-24
- Decision: Align calendar events with the Menu data model and persist full menu text in history.
- Context: The calendar entity still used legacy DayMenu objects; it must use filtered summaries with unfiltered menu descriptions per contract, and preserve past descriptions when menus roll off.
- Impact: Calendar events are built from ISO-date menu data, summaries come from the filtering pipeline, and history now stores both summary and menu text (backwards compatible with prior history).
- References: custom_components/skolmat/calendar.py, docs/design/calendar-contract.md, docs/design/filtering-contract.md

- Date: 2026-01-25
- Decision: Make entity unique IDs entry-based to allow multiple configs for the same URL.
- Context: URL-hash unique IDs collide when users create multiple configs for the same provider URL, or when entity registry retains an old entry.
- Impact: Sensor and calendar unique IDs now use the config entry ID, allowing duplicates to coexist and avoiding hash collisions.
- References: custom_components/skolmat/sensor.py, custom_components/skolmat/calendar.py

- Date: 2026-01-25
- Decision: Include the config entry name in unique IDs for easier debugging.
- Context: Multiple configs can now share the same URL; adding a name slug to unique IDs makes entity registry entries easier to identify.
- Impact: Sensor and calendar unique IDs now include a slugified name plus the entry ID.
- References: custom_components/skolmat/sensor.py, custom_components/skolmat/calendar.py

- Date: 2026-01-25
- Decision: Treat `Menu.getMenu` returning `None` as invalid data and mark the entity unavailable.
- Context: Fetch failures should not present stale or empty data as valid.
- Impact: `Menu.getMenu` may return `None` on failed fetch with invalid cached data; entities should map that to `available=False`.
- References: docs/design/sensor-contract.md

- Date: 2026-01-25
- Decision: Exclusion ordering is fixed to labels first, then regex.
- Context: Filtering behavior matches current implementation and simplifies UX expectations for exclusion priority.
- Impact: Design contract now specifies a single keyword/regex list applied in configured order across label+dish.
- References: docs/design/filtering-contract.md, custom_components/skolmat/dayfilter.py

- Date: 2026-01-25
- Decision: Preference stacking uses cumulative keyword/regex matches across label+dish.
- Context: Preferences should stack while remaining predictable for users; matching against label+dish keeps the model simple.
- Impact: DayFilter ranks by keyword/regex hit count with original order as the tie-breaker.
- References: custom_components/skolmat/dayfilter.py, docs/design/filtering-contract.md

- Date: 2026-01-25
- Decision: DayFilter accepts config-flow contract fields and ignores target scopes.
- Context: Core filtering must align with the config-flow contract before the new flow is implemented.
- Impact: DayFilter now accepts `meals_selected`, `exclude_*`, `prefer_*`, and `max_entries`, and matches exclude/prefer keywords against both labels and dishes.
- References: custom_components/skolmat/dayfilter.py, docs/design/config-flow-contract.md

- Date: 2026-01-25
- Decision: Config flow processor hook runs before provider-specific cleanup.
- Context: Processor normalization should see raw provider values and run ahead of provider-specific normalization.
- Impact: Config flow validation/loading uses the processor hook in `Menu.createMenu`, matching the core processing order.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/menu.py

- Date: 2026-01-25
- Decision: Config flow now starts in a custom-only "Configure" step with day navigation and full input/summary preview.
- Context: Users need visibility into all meals and the resulting summary before choosing meal selection; auto mode is hidden for now.
- Impact: Config flow presents a single configure step with prev/next day controls, input menu display, and summary preview, defaulting to all meals on the selected day.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Config flow uses a date selector and "I'm done configuring" checkbox to apply preview updates.
- Context: HA config flows do not support custom buttons or live updates; selection changes require a submit to refresh.
- Impact: The configure step now offers a date dropdown and a done checkbox; submitting without the checkbox re-renders preview for the chosen date and meals.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Advanced filter fields are included directly in the Configure step with a text divider.
- Context: Users requested a single-step flow with visible advanced filters instead of a hidden/collapsible section.
- Impact: Configure now includes exclusion/preference fields and max entries in the same dialog, with a textual "Advanced" divider in the description.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Target scope selection is removed; exclusions and preferences always match both label and dish.
- Context: Target controls add complexity and confusion in the config flow; default should be inclusive.
- Impact: Config flow and DayFilter no longer use target fields and always match against both labels and dishes.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/dayfilter.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Exclusion/preference inputs accept keywords with optional /regex/ syntax.
- Context: Regex-first UX is confusing for non-technical users; keywords should be the default input.
- Impact: Config flow now treats each line as a keyword unless wrapped in `/.../`, and commas are no longer supported as separators.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Use multi-select keyword chips for exclude/prefer inputs instead of multiline text.
- Context: Multiline text inputs submit on Enter and optional fields can be omitted, hurting UX and clearing behavior.
- Impact: Exclude/prefer keywords are now multi-select fields with custom values; clearing chips removes keywords reliably.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Max entries uses suggested value and treats 0/blank as unlimited.
- Context: Default values in optional fields caused max entries to reappear after clearing.
- Impact: Config flow uses `suggested_value` for max entries and normalizes values <= 0 to unlimited.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Processor reload is triggered on change or via explicit checkbox, re-importing the module.
- Context: Processor development needs reload without HA restart, and should reprocess raw provider data on changes.
- Impact: Configure step includes processor file/fn fields and a reload checkbox; changing either forces a reload and the current date is preserved when possible.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-01-25
- Decision: Remove label-specific exclude/prefer inputs; use keyword/regex lists that match both label and dish.
- Context: Separate label vs regex inputs are confusing and redundant for users.
- Impact: Config flow now exposes only keyword/regex lists; DayFilter merges legacy label selections into regex patterns for compatibility.
- References: docs/design/filtering-contract.md, docs/design/config-flow-contract.md, custom_components/skolmat/dayfilter.py, custom_components/skolmat/config_flow.py

- Date: 2026-02-02
- Decision: Use suggested values for processor fields to allow clearing them.
- Context: Text inputs with defaults reappear after clearing in config/options flows.
- Impact: Processor file/function fields now use `suggested_value` so empty submissions are respected.
- References: custom_components/skolmat/config_flow.py

- Date: 2026-02-02
- Decision: Decode HTML entities in menu normalization.
- Context: Some providers return escaped characters (e.g., `&amp;`) that leak into summaries.
- Impact: `normalizeString` now unescapes HTML entities before normalizing whitespace and punctuation.
- References: custom_components/skolmat/menu.py

- Date: 2026-02-02
- Decision: Avoid duplicate Mateo provider error logs by removing stack-trace logging in helpers.
- Context: Helper methods logged exceptions and then `getMenu` logged again, producing duplicate error lines and stack traces.
- Impact: Mateo menu helper methods now raise errors without logging; `getMenu` remains the single error log.
- References: custom_components/skolmat/menu.py

- Date: 2026-02-02
- Decision: Block config flow when initial menu fetch fails.
- Context: The flow proceeded to summary configuration even when the menu could not be fetched.
- Impact: Initial config now returns to the URL step with a "check URL" error on fetch failures.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/translations/en.json

- Date: 2026-02-02
- Decision: Preserve user input on config flow errors.
- Context: After a failed menu fetch, the initial form cleared name/URL fields.
- Impact: The user-entered values are now used as defaults when re-rendering the initial step.
- References: custom_components/skolmat/config_flow.py

- Date: 2026-02-02
- Decision: Remove auto mode from DayFilter and treat empty meal selection as "all".
- Context: Config flow does not expose auto mode, so empty selections should consistently include all meals.
- Impact: DayFilter no longer prefers Lunch implicitly; empty meal_focus keeps all entries.
- References: custom_components/skolmat/dayfilter.py

- Date: 2026-02-02
- Decision: Remove mode field from config flow filters.
- Context: Mode is no longer used anywhere; keeping it in config data is misleading.
- Impact: Config flow no longer sets or emits a mode value.
- References: custom_components/skolmat/config_flow.py, custom_components/skolmat/const.py

- Date: 2026-02-02
- Decision: Pin devcontainer workspace mount target to `/workspaces/skolmat`.
- Context: `${env:WORKSPACE_DIR}` was empty on the host, causing Docker to mount with an empty target and fail container startup.
- Impact: Devcontainer now binds the workspace to a fixed target path, removing reliance on host env resolution.
- References: .devcontainer/devcontainer.json

- Date: 2026-02-02
- Decision: Store VS Code server data under `/vscode/vscode-server` via `VSCODE_AGENT_FOLDER`.
- Context: The dedicated `/home/vscode/.vscode-server` volume was root-owned and VS Code tried to write before post-create scripts could fix permissions.
- Impact: VS Code uses the existing `/vscode` volume for persistence, avoiding the permission race.
- References: .devcontainer/devcontainer.json

- Date: 2026-02-02
- Decision: Set VS Code server path variables in `containerEnv` for early startup.
- Context: `remoteEnv` did not take effect before the VS Code server launched, so it still used `/home/vscode/.vscode-server`.
- Impact: The server now receives `VSCODE_AGENT_FOLDER` and `VSCODE_SERVER_DIR` at container start, directing it to `/vscode/vscode-server`.
- References: .devcontainer/devcontainer.json

- Date: 2026-02-02
- Decision: Pin VS Code server volume ownership via mount options.
- Context: VS Code always launches with `--server-data-dir /home/vscode/.vscode-server`, ignoring env overrides.
- Impact: The named volume is mounted with `uid=1000,gid=1000` so it is writable by the `vscode` user from container start.
- References: .devcontainer/devcontainer.json

- Date: 2026-02-02
- Decision: Use local volume `o=uid,gid` mount option for VS Code server volume.
- Context: Docker rejected `volume-opt=gid` on the local volume driver; using `o=uid=1000,gid=1000` is the supported option format.
- Impact: The volume is created with ownership options via the local driver, preventing root-owned data.
- References: .devcontainer/devcontainer.json

- Date: 2026-02-02
- Decision: Persist VS Code server data via a bind mount under `.devcontainer/vscode-server`.
- Context: Docker rejected local volume ownership options, so the named volume could not be made writable at mount time.
- Impact: The server data is stored under a repo-local bind mount and ignored by git.
- References: .devcontainer/devcontainer.json, .gitignore

- Date: 2026-02-02
- Decision: Fix VS Code server volume permissions during setup.
- Context: The named `/home/vscode/.vscode-server` volume must be writable by the `vscode` user to preserve extension state across rebuilds.
- Impact: `container setup-project` now creates the folder (if needed) and chowns it to `vscode:vscode`.
- References: .devcontainer/setup-project, .devcontainer/devcontainer.json

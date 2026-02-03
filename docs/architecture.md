# Architecture

High-level flow:
1. Provider fetch + parsing -> normalized MenuEntry list.
2. Optional processor normalization (advanced, last resort).
3. DayFilter selects a meal focus and filters entries for summary output.
4. Sensor state + calendar summary use filtered output; full menu stays in
   attributes and calendar description.

Key modules:
- `custom_components/skolmat/menu.py`: provider fetch/parsing, MenuEntry shapes.
- `custom_components/skolmat/dayfilter.py`: summary selection pipeline.
- `custom_components/skolmat/sensor.py`: sensor entity, state, attributes.
- `custom_components/skolmat/calendar.py`: calendar events and formatting.
- `custom_components/skolmat/config_flow.py`: setup/options UI.
- `custom_components/skolmat/processors/`: optional per-source normalization helpers.
- `skolmat-card/`: Lovelace custom card (submodule).

# Todo

## Active phases

- Finalize config flow implementation.

## Config flow vs implementation findings

- changing date in config flow does not update "Input data" and "State and calendar summary" (resolved: requires submit to refresh preview)
- processor in config flow cannot be removed / unset(text keeps reappearing in boxes after submit) (resolved)
- failed menu load keeps trying too often, add progressive backoff (2 min first fail, then +20 min per consecutive fail)
- day summary: &amp encoding: Potatismos med vegokorv, ketchup&amp;senap (Vegetariskt) (resolved)
- failed menu loads still allowed to continue in config flow (set optional/suggested instead of default value) (resolved)
- if meal not selected in config, should be "all". Seems to work that way but make it explicit/explained (resolved)
- set pylance and ruff config, only examine custom_components, test and skolmat_card folders

- meal stops beeing checkboxes if there are many meals

# Overview

Note: This is development-only documentation, not end-user guidance.

Skolmat is a Home Assistant custom integration that fetches daily menus from
Swedish providers and exposes them as entities.

Key surfaces:
- Sensor: short daily summary in the state; full structured menu in attributes.
- Calendar: one event per day; short summary in event title; full menu in description.
- Lovelace card: lives in `skolmat-card/` (submodule) and renders the full menu.

Data sources include skolmaten.se, webmenu.foodit.se, menu.matildaplatform.com,
mpi.mashie.com, and meny.mateo.se.

This repo contains v2.1+ work-in-progress. The end-user `README.md` reflects the
current released v2.0 and may lag behind development changes.

Design contracts for filtering and config flow live in `docs/design/`.

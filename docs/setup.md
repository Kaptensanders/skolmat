# Setup

Note: This is development-only documentation, not end-user guidance.

Recommended workflow: devcontainer.

## Devcontainer
- Config: `.devcontainer/devcontainer.json` (image `hass_dev_image_2025.12.2`).
- Post-create: `container setup-project` runs `.devcontainer/setup-project`.
- Ports: 8123 (Home Assistant), 5678 (debugpy).
- Mounts `skolmat-card/` into HA config `www/` for the card.
- Bootstraps HA `.storage` from `.devcontainer/ha_config_bootstrap/.storage` when present.
- Environment: `.devcontainer/container.env`.

## Submodules
- `skolmat-card` is a git submodule. Run `./setup-repo.sh` if the submodule is missing.

## Local install (non-devcontainer)
- Place `custom_components/skolmat/` under your HA `config/custom_components/`.
- Restart HA and add the integration via Settings -> Devices & Services.

#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------
# Update Home Assistant dev bootstrap storage
#
# Copies a curated subset of HA .storage into:
#   <repo>/.devcontainer/ha_config_bootstrap/.storage
#
# SAFETY:
#  - Must be run INSIDE the devcontainer
#  - Home Assistant MUST NOT be running
# ------------------------------------------------------------------

# ---- Ensure running inside container -----------------------------

if ! grep -qa docker /proc/1/cgroup; then
  echo "ERROR: This script must be run from inside the devcontainer."
  echo "Aborting."
  exit 1
fi

# ---- Ensure Home Assistant is NOT running -------------------------

if pgrep -f "homeassistant" >/dev/null; then
  echo "ERROR: Home Assistant appears to be running."
  echo "Stop HA before updating bootstrap storage."
  exit 1
fi

# ---- Paths --------------------------------------------------------

SRC_STORAGE="${HOME}/ha_config/.storage"
DST_STORAGE="$(dirname "$0")/ha_config_bootstrap/.storage"

echo "Updating HA bootstrap storage..."
echo "Source:      ${SRC_STORAGE}"
echo "Destination: ${DST_STORAGE}"

mkdir -p "${DST_STORAGE}"

# ---- Core registries (REQUIRED) ----------------------------------

cp -v "${SRC_STORAGE}/core.config_entries" \
      "${DST_STORAGE}/"

cp -v "${SRC_STORAGE}/core.device_registry" \
      "${DST_STORAGE}/"

cp -v "${SRC_STORAGE}/core.entity_registry" \
      "${DST_STORAGE}/"

echo
echo "Bootstrap storage updated successfully."
echo "NOTE: Home Assistant was not running during export (good)."

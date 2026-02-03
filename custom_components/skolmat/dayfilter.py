
from __future__ import annotations
from typing import (TypedDict, Any, TYPE_CHECKING)
import re

if TYPE_CHECKING:
    from .menu import MenuEntry

from logging import getLogger
log = getLogger(__name__)

class DayFilterConfig(TypedDict, total=False):
    # Phase A – meal focus
    meal_focus: list[str] | None

    # Phase B – exclusions
    exclude: dict[str, list[str | re.Pattern]]  # keys: "labels", "regex"

    # Phase B – preferences
    prefer: dict[str, list[str | re.Pattern]]   # keys: "labels", "regex"

    # Phase C – max cap
    max_items: int | None


class DayFilter():

    def __init__(self, config_raw:dict):
        self._config:DayFilterConfig = self._processConfig(config_raw)
    
    
    def _processConfig(self, config_raw:dict):

        config_raw = config_raw if isinstance (config_raw, dict) else {}

        # ---- meal_focus (Phase A) --------------------------------
        meal_focus = config_raw.get("meal_focus")
        if meal_focus is None:
            meal_focus = config_raw.get("meals_selected")
        if not isinstance(meal_focus, list):
            meal_focus = None
        else:
            meal_focus = [m.strip() for m in meal_focus if isinstance(m, str) and m.strip()]
            if not meal_focus:
                meal_focus = None

        # ---- helper for exclude / prefer blocks ------------------
        def normalize_block(block: Any) -> dict[str, list]:
            if not isinstance(block, dict):
                return {"labels": [], "regex": []}

            labels = block.get("labels")
            if not isinstance(labels, list):
                labels = []
            else:
                labels = [s.strip().lower() for s in labels if isinstance(s, str) and s.strip()]

            regex = []
            raw_regex = block.get("regex")
            if isinstance(raw_regex, list):
                for pattern in raw_regex:
                    if not isinstance(pattern, str) or not pattern.strip():
                        continue
                    try:
                        regex.append(re.compile(pattern, re.IGNORECASE))
                    except re.error as e:
                        log.error("Skolmat DayFilter: invalid regex '%s' ignored (%s)", pattern, e)

            return {
                "labels": labels,
                "regex": regex,
            }

        # ---- Phase B blocks --------------------------------------
        exclude = normalize_block(config_raw.get("exclude"))
        prefer = normalize_block(config_raw.get("prefer"))
        if "exclude_labels" in config_raw or "exclude_regex" in config_raw:
            exclude = normalize_block({
                "labels": config_raw.get("exclude_labels"),
                "regex": config_raw.get("exclude_regex"),
            })
        if "prefer_labels" in config_raw or "prefer_regex" in config_raw:
            prefer = normalize_block({
                "labels": config_raw.get("prefer_labels"),
                "regex": config_raw.get("prefer_regex"),
            })

        # Merge label selections into regex for backward compatibility.
        if exclude["labels"]:
            exclude["regex"].extend(
                re.compile(re.escape(label), re.IGNORECASE) for label in exclude["labels"]
            )
            exclude["labels"] = []
        if prefer["labels"]:
            prefer["regex"].extend(
                re.compile(re.escape(label), re.IGNORECASE) for label in prefer["labels"]
            )
            prefer["labels"] = []

        # ---- Phase C ---------------------------------------------
        max_items = config_raw.get("max_items")
        if max_items is None:
            max_items = config_raw.get("max_entries")
        if not isinstance(max_items, int) or max_items < 1:
            max_items = None

        # ---- canonical config ------------------------------------
        return {
            "meal_focus": meal_focus,
            "exclude": exclude,
            "prefer": prefer,
            "max_items": max_items,
        }

    def filter(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        if not entries:
            return []

        focused = self._phase_a_focus(entries)
        ranked = self._phase_b_filter_and_rank(focused)
        capped = self._phase_c_cap(ranked)

        # Final safety net
        return capped or focused


    def _phase_a_focus(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        """
        Phase A - meal focus
        """
        if not entries:
            return entries

        meal_focus = self._config["meal_focus"]

        # ---- meal focus: hard boundary -----------------------------
        if meal_focus:
            focused = [e for e in entries if e.get("meal") in meal_focus]
            if focused:
                return focused

            log.info("DayFilter: meal_focus %r matched nothing — falling back to all entries", meal_focus)
            return entries

        # fallback: keep all (empty meal_focus means all meals)
        return entries



    def _phase_b_filter_and_rank(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        if not entries:
            return entries

        filtered = self._apply_exclusions(entries)
        ranked = self._apply_preferences(filtered)
        return ranked

    def _apply_exclusions(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        cfg = self._config["exclude"]
        result = entries

        def matches_regex(entry: MenuEntry, rx: re.Pattern) -> bool:
            entry_label = entry.get("label") or ""
            entry_dish = entry.get("dish") or ""
            text = f"{entry_label} {entry_dish}"
            return rx.search(text) is not None

        # regex exclusions
        for rx in cfg["regex"]:
            tmp = [e for e in result if not matches_regex(e, rx)]
            if tmp:
                result = tmp
            else:
                log.info("DayFilter: exclusion skipped (regex=%r) — would remove all entries (%d)", rx.pattern, len(result))

        return result


    def _apply_preferences(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        cfg = self._config["prefer"]

        def score(entry: MenuEntry) -> tuple:
            label = (entry.get("label") or "").lower()
            dish = (entry.get("dish") or "").lower()

            def regex_hit(rx: re.Pattern) -> bool:
                text = f"{label} {dish}"
                return rx.search(text) is not None

            # Stack preferences across keywords; tie-breaker is original order.
            regex_hits = sum(1 for rx in cfg["regex"] if regex_hit(rx))
            return (-regex_hits, entry.get("order", 0))

        return sorted(entries, key=score)

    
    def _phase_c_cap(self, entries: list[MenuEntry]) -> list[MenuEntry]:
        max_items = self._config["max_items"]
        if not max_items:
            return entries
        return entries[:max_items]

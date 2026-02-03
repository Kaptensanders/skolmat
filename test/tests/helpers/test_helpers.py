import json, os, sys
from datetime import date as Date
from menu import Menu
from fixtures.providers import PROVIDERS
from pathlib import Path
from typing import Any
from menu import Menu, MenuData, MenuEntry

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
with open(FIXTURES / "test_data.json", encoding="utf-8") as f:
    FIXTURES = json.load(f)

USECASES = Path(__file__).resolve().parents[2] / "fixtures"
with open(USECASES / "usecases.json", encoding="utf-8") as f:
    USECASES = json.load(f)


def _current_test_name() -> str:
    raw = os.environ.get("PYTEST_CURRENT_TEST", "")
    if not raw:
        return "unknown-test"
    # Extract function name only
    return raw.split("::")[-1].split(" ")[0]


def _dump_summary(tag: str, org_summary: str, filtered_summary: str):
    test_case = _current_test_name()
    header = f"---- {test_case}:{tag} " + "-" * max(1, 80 - len(test_case) - len(tag))
    print(header)
    print(f"original summary: {org_summary}")
    print(f"filtered summary: {filtered_summary}")



class UCTestMenu(Menu):
    """Synthetic Menu for UC tests (no provider parsing, no I/O)."""

    provider = "uc"

    def _fixUrl(self, url: str) -> str:
        return url

    async def _loadMenu(self, aiohttp_session) -> MenuData:
        # UC tests never call getMenu(); menu is injected directly.
        return {}

    def _processMenuEntry(self, entryDate, order: int, raw_entry: Any) -> MenuEntry | None:
        # Not used in UC tests (we inject MenuEntry dicts directly),
        # but keep the base contract intact.
        return super()._processMenuEntry(entryDate, order, raw_entry)


def run_filter_rule(
    *,
    filters: dict,
    dataset: str = "provider",  # "provider" | "uc"
    provider: str | None = None,
    isodate: str | None = None,
    usecases: list[str] | None = None,
):
    if dataset == "provider":
        assert usecases is None, "usecases not valid for provider dataset"
        return run_filter_rule_provider(
            filters=filters,
            provider=provider,
            isodate=isodate,
        )

    if dataset == "uc":
        assert provider is None and isodate is None, "provider/date not valid for UC dataset"
        assert usecases, "usecases must be provided for UC dataset"
        return run_filter_rule_uc(
            filters=filters,
            usecases=usecases,
        )

    raise AssertionError(f"Unknown dataset: {dataset}")



def run_filter_rule_uc(*, filters: dict, usecases: list[str]) -> dict[str, dict[str, str]]:
    """
    Run E2E summary filtering against UC catalog only.

    Returns:
        results[uc_id] = {"raw": str, "summary": str}
    """
    results: dict[str, dict[str, str]] = {}

    for uc_id in usecases:
        uc = USECASES[uc_id]
        entries: list[MenuEntry] = uc["entries"]

        menu = UCTestMenu(
            asyncExecutor=None,
            url="uc://synthetic",
            customMenuEntryProcessorCB=None,
            readableDaySummaryCB=None,
        )

        # Synthetic one-day menu (stable, deterministic)
        iso = Date.today().isoformat()
        menu._menu = {iso: entries}
        menu.setSummaryFilters(filters)

        original_summary = menu.getReadableDaySummary(Date.fromisoformat(iso), False)
        filtered_summary = menu.getReadableDaySummary(Date.fromisoformat(iso))
        _dump_summary(uc_id, original_summary, filtered_summary)

        results[uc_id] = {
            "raw": " | ".join(e["dish"] for e in entries),
            "summary": filtered_summary,
        }

    return results

def run_filter_rule_provider(
    *,
    filters: dict,
    provider: str | None = None,
    isodate: str | None = None,
):
    results = {}

    for test in FIXTURES["tests"]:
        name = test["name"]
        if provider and name != provider:
            continue

        conf = PROVIDERS[name]

        menu = Menu.createMenu(
            asyncExecutor=None,
            url=conf["url"],
            customMenuEntryProcessorCB=conf.get("customMenuEntryProcessorCB"),
            readableDaySummaryCB=conf.get("readableDaySummaryCB"),
        )

        menu._menu = test["data"]
        menu.setSummaryFilters(filters)

        per_day = {}
        for d in sorted(test["data"].keys()):
            if isodate and d != isodate:
                continue

            original_summary = menu.getReadableDaySummary(Date.fromisoformat(d), False)
            filtered_summary = menu.getReadableDaySummary(Date.fromisoformat(d))

            _dump_summary(f"{name} {d}", original_summary, filtered_summary)
            per_day[d] = filtered_summary


        if per_day:
            results[name] = per_day


    return results

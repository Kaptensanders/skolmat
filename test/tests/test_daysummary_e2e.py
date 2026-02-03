from datetime import date as Date, timedelta

from fixtures.providers import PROVIDERS
from menu import Menu
from tests.helpers.test_helpers import FIXTURES, run_filter_rule, UCTestMenu, USECASES


def _menu_from_provider_fixture(provider_name: str) -> Menu:
    test = next(t for t in FIXTURES["tests"] if t["name"] == provider_name)
    conf = PROVIDERS[provider_name]
    menu = Menu.createMenu(
        asyncExecutor=None,
        url=conf["url"],
        customMenuEntryProcessorCB=conf.get("customMenuEntryProcessorCB"),
        readableDaySummaryCB=conf.get("readableDaySummaryCB"),
    )
    menu._menu = test["data"]
    return menu


def test_baseline_summary_non_empty():
    out = run_filter_rule(filters={"mode": "auto"})

    for provider, days in out.items():
        for d, summary in days.items():
            assert summary, f"{provider} {d} empty"

def test_exclude_never_empties():
    out = run_filter_rule(
        filters={
            "mode": "auto",
            "exclude": {
                "regex": [".*"]
            }
        }
    )

    for provider, days in out.items():
        for d, summary in days.items():
            assert summary, f"{provider} {d} emptied by exclusion"


def test_max_items_1():
    out = run_filter_rule(
        filters={"mode": "auto", "max_items": 1}
    )

    for provider, days in out.items():
        for summary in days.values():
            assert "|" not in summary


def test_exclusion_guarded_regex_uc():
    # Design contract §5.1 — Exclusions (progressive and guarded)
    # Rule:
    #   Keyword/regex exclusions apply in order and are guarded.
    #
    # UC-C data:
    #   1. meal="Lunch", label="Husman",        dish="Dish A"
    #   2. meal="Lunch", label="Dagens",        dish="Dish B"
    #   3. meal="Lunch", label="Vegetariskt",   dish="Dish C"
    #
    # Filters:
    #   - exclude keyword="Vegetariskt"
    #   - exclude regex=".*"   (would remove all remaining, must be skipped)
    #
    # Expected behavior:
    #   - Keyword exclusion removes entry (3)
    #   - Second regex exclusion is skipped (guarded)
    #   - Result contains Dish A and Dish B

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-C"],
        filters={
            "mode": "auto",
            "exclude": {
                "regex": ["Vegetariskt", ".*"],
            },
        },
    )

    summary = out["UC-C"]["summary"]

    assert "Dish A" in summary
    assert "Dish B" in summary
    assert "Dish C" not in summary


def test_max_items_caps_but_does_not_fill_uc():
    # Design contract §4.3 — N cap semantics
    #
    # UC-C data:
    #   1. Dish A
    #   2. Dish B
    #   3. Dish C
    #
    # max_items = 2
    # Expected:
    #   - Only first 2 entries kept
    #   - No attempt to backfill or reorder

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-C"],
        filters={
            "mode": "auto",
            "max_items": 2,
        },
    )

    summary = out["UC-C"]["summary"]

    assert "Dish A" in summary
    assert "Dish B" in summary
    assert "Dish C" not in summary


def test_max_items_larger_than_entries_is_noop_uc():
    # Design contract §4.3 — N cap semantics
    #
    # UC-A data:
    #   2 entries total
    #
    # max_items = 5
    # Expected:
    #   - All entries preserved

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-A"],
        filters={
            "mode": "auto",
            "max_items": 5,
        },
    )

    summary = out["UC-A"]["summary"]

    assert "Dish A" in summary
    assert "Dish B" in summary


def test_max_items_respects_meal_focus_uc():
    # Design contract §4.3 + §5 — N cap must not cross meals
    #
    # UC-E1 data:
    #   Lunch: Dish A
    #   Middag: Dish B
    #
    # Auto focus keeps Lunch only
    # max_items = 1
    #
    # Expected:
    #   - Dish A kept
    #   - Dish B never pulled in

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-E1"],
        filters={
            "mode": "auto",
            "max_items": 1,
        },
    )

    summary = out["UC-E1"]["summary"]

    assert "Dish A" in summary
    assert "Dish B" not in summary


def test_preference_stacking_uc():
    # Design contract §5.2 — Preferences can stack; keywords match label+dish.
    #
    # UC-H1 data:
    #   1. label="Husman",  dish="Veg stew"    (2 keyword hits)
    #   2. label="Dagens",  dish="Veg curry"   (1 keyword hit)
    #   3. label="Special", dish="Stew"        (1 keyword hit)
    #   4. label="Husman",  dish="Chicken"     (1 keyword hit)
    #
    # Filters:
    #   prefer keywords=["Husman", "veg", "stew"]
    #
    # Expected order:
    #   - Higher hit counts sort first; ties keep original order

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-H1"],
        filters={
            "mode": "auto",
            "prefer": {
                "regex": ["Husman", "veg", "stew"],
            },
        },
    )

    summary = out["UC-H1"]["summary"]
    assert summary == "Veg stew | Veg curry | Stew | Chicken"


def test_prefer_keyword_matches_dish_uc():
    # Design contract §5.2 — Keywords match dish and label.
    #
    # UC-H2 data:
    #   1. "Fish soup"
    #   2. "Chicken curry"
    #   3. "Veg stew"
    #
    # Filters:
    #   prefer keywords=["Veg stew"]
    #
    # Expected:
    #   - "Veg stew" moves to the front.

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-H2"],
        filters={
            "mode": "auto",
            "prefer_regex": ["Veg stew"],
        },
    )

    summary = out["UC-H2"]["summary"]
    assert summary == "Veg stew | Fish soup | Chicken curry"


def test_exclude_keyword_matches_dish_uc():
    # Design contract §5.1 — Keywords match dish and label for exclusions.
    #
    # UC-H2 data:
    #   1. "Fish soup"
    #   2. "Chicken curry"
    #   3. "Veg stew"
    #
    # Filters:
    #   exclude keywords=["Chicken curry"]
    #
    # Expected:
    #   - "Chicken curry" removed, others preserved.

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-H2"],
        filters={
            "mode": "auto",
            "exclude_regex": ["Chicken curry"],
        },
    )

    summary = out["UC-H2"]["summary"]
    assert summary == "Fish soup | Veg stew"


def test_exclude_keyword_matches_label_uc():
    # Design contract §5.1 — Keywords match dish and label for exclusions.
    #
    # UC-H2 data:
    #   1. label="Alt 1" dish="Fish soup"
    #   2. label="Alt 2" dish="Chicken curry"
    #   3. label="Alt 3" dish="Veg stew"
    #
    # Filters:
    #   exclude keywords=["Alt 2"]
    #
    # Expected:
    #   - Entry with label "Alt 2" removed.

    out = run_filter_rule(
        dataset="uc",
        usecases=["UC-H2"],
        filters={
            "mode": "auto",
            "exclude_regex": ["Alt 2"],
        },
    )

    summary = out["UC-H2"]["summary"]
    assert summary == "Fish soup | Veg stew"


def test_provider_summary_never_empty():
    # Design contract §4.4 — Filtering must never erase a day completely
    out = run_filter_rule(
        filters={"mode": "auto"},
    )

    for provider, days in out.items():
        for d, summary in days.items():
            assert summary.strip(), f"{provider} {d} produced empty summary"




def test_provider_auto_prefers_lunch_when_present():
    # Design contract §5 Phase A — Auto prefers Lunch
    out = run_filter_rule(
        filters={"mode": "auto"},
    )

    for provider, days in out.items():
        for d, summary in days.items():
            raw = summary.lower()

            if "lunch" in raw:
                # sanity: no obvious dinner-only summaries
                assert not raw.startswith(("middag", "kväll", "dinner")), (
                    f"{provider} {d} looks like non-lunch summary: {summary}"
                )



def test_provider_max_items_reduces_or_equals_length():
    # Design contract §4.3 — max_items is a cap, never a filler
    base = run_filter_rule(
        filters={"mode": "auto"},
    )

    capped = run_filter_rule(
        filters={"mode": "auto", "max_items": 1},
    )

    for provider in base:
        for d in base[provider]:
            assert len(capped[provider][d]) <= len(base[provider][d]), (
                f"{provider} {d} got longer with max_items"
            )


def test_provider_custom_meal_focus_fallback():
    # Design contract §5 Phase A — Custom fallback must never empty output
    out = run_filter_rule(
        filters={
            "mode": "custom",
            "meal_focus": ["THIS_MEAL_DOES_NOT_EXIST"],
        },
    )

    for provider, days in out.items():
        for d, summary in days.items():
            assert summary.strip(), (
                f"{provider} {d} empty after custom meal_focus fallback"
            )


def test_provider_discovery_consistent_keywords_no_warning():
    # Provider data with stable meals/labels should not warn.
    menu = _menu_from_provider_fixture("skolmaten1")
    reference_date = Date.fromisoformat("2026-01-09")

    keywords = menu.getSummaryFilterKeywords(reference_date=reference_date)

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1", "Alt 2"]
    assert keywords["info"] == "Found 1 results for meals, and 2 dish labels in menu data."


def test_provider_discovery_warns_on_extra_meals():
    # Provider data with extra meals on other days should warn.
    menu = _menu_from_provider_fixture("mashie4")
    reference_date = Date.fromisoformat("2026-01-12")

    keywords = menu.getSummaryFilterKeywords(reference_date=reference_date)

    assert keywords["meals"] == ["Kökets gröna 1", "Kökets rätt"]
    assert keywords["labels"] == []
    assert keywords["info"] == (
        "Found 2 results for meals, and 0 dish labels in menu data. "
        "Warning: other days include additional meals/labels; discovery may be incomplete. See logs for details."
    )


def test_provider_discovery_warns_on_extra_labels():
    # Provider data with extra labels on other days should warn.
    menu = _menu_from_provider_fixture("foodit")
    reference_date = Date.fromisoformat("2026-01-05")

    keywords = menu.getSummaryFilterKeywords(reference_date=reference_date)

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1"]
    assert keywords["info"] == (
        "Found 1 results for meals, and 1 dish labels in menu data. "
        "Warning: other days include additional meals/labels; discovery may be incomplete. See logs for details."
    )


def test_provider_discovery_holiday_today_uses_same_keywords():
    # Holiday text still yields stable keywords when meals/labels are present.
    menu = _menu_from_provider_fixture("skolmaten3")
    reference_date = Date.fromisoformat("2026-01-05")

    keywords = menu.getSummaryFilterKeywords(reference_date=reference_date)

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1", "Alt 2"]
    assert keywords["info"] == "Found 1 results for meals, and 2 dish labels in menu data."


def test_discovery_skips_low_signal_day_uc():
    # Design contract §6.2.1 — Keyword discovery should skip low-signal days.
    menu = UCTestMenu(
        asyncExecutor=None,
        url="uc://synthetic",
        customMenuEntryProcessorCB=None,
        readableDaySummaryCB=None,
    )

    today = Date.today()
    tomorrow = today + timedelta(days=1)

    menu._menu = {
        today.isoformat(): USECASES["UC-G1"]["entries"],
        tomorrow.isoformat(): USECASES["UC-G2"]["entries"],
    }

    keywords = menu.getSummaryFilterKeywords()

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1", "Alt 2"]
    assert "Warning:" not in keywords["info"]


def test_discovery_warns_on_inconsistent_keywords_uc():
    # Design contract §6.2.1 — Warn when other days include additional keywords.
    menu = UCTestMenu(
        asyncExecutor=None,
        url="uc://synthetic",
        customMenuEntryProcessorCB=None,
        readableDaySummaryCB=None,
    )

    today = Date.today()
    tomorrow = today + timedelta(days=1)

    menu._menu = {
        today.isoformat(): USECASES["UC-G2"]["entries"],
        tomorrow.isoformat(): USECASES["UC-G3"]["entries"],
    }

    keywords = menu.getSummaryFilterKeywords()

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1", "Alt 2"]
    assert "Warning:" in keywords["info"]
    assert "See logs for details." in keywords["info"]


def test_discovery_keywords_predictable_uc():
    # Design contract §6.2.1 — Keyword discovery should be deterministic.
    menu = UCTestMenu(
        asyncExecutor=None,
        url="uc://synthetic",
        customMenuEntryProcessorCB=None,
        readableDaySummaryCB=None,
    )

    today = Date.today()

    menu._menu = {
        today.isoformat(): USECASES["UC-G2"]["entries"],
    }

    keywords = menu.getSummaryFilterKeywords()

    assert keywords["meals"] == ["Lunch"]
    assert keywords["labels"] == ["Alt 1", "Alt 2"]
    assert keywords["info"] == "Found 1 results for meals, and 2 dish labels in menu data."

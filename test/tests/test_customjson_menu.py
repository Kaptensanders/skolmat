import logging

import pytest

from menu import CustomJsonMenu, Menu


SAMPLE = {
    "2026-04-28": [
        {"meal": "Lunch", "dish": "Pasta carbonara", "label": "", "order": 2},
        {"meal": "Lunch", "dish": "Vegetarian lasagna", "label": "Vegetarian", "order": 1},
    ],
    "2026-04-29": [
        {"meal": "Lunch", "dish": "Fish soup", "label": "Fish"},
    ],
}


def _menu():
    return CustomJsonMenu(asyncExecutor=None, url="https://www.mysite.se/lunch.json")


def test_create_menu_logs_custom_json_fallback(caplog):
    url = "https://www.mysite.se/lunch.json"

    with caplog.at_level(logging.WARNING):
        menu = Menu.createMenu(asyncExecutor=None, url=url)

    assert isinstance(menu, CustomJsonMenu)
    assert (
        "Menu URL did not match a known provider; falling back to the custom JSON provider: "
        f"{url}"
    ) in caplog.messages


def test_customjson_two_dates_multiple_dishes_order_preserved():
    parsed = _menu()._parseMenuData(SAMPLE)

    assert sorted(parsed.keys()) == ["2026-04-28", "2026-04-29"]

    day1 = parsed["2026-04-28"]
    assert len(day1) == 2
    assert day1[0]["dish"] == "Pasta carbonara"
    assert day1[0]["order"] == 2
    assert day1[0]["meal"] == "Lunch"
    assert day1[1]["dish"] == "Vegetarian lasagna"
    assert day1[1]["order"] == 1
    assert day1[1]["label"] == "Vegetarian"

    day2 = parsed["2026-04-29"]
    assert len(day2) == 1
    assert day2[0]["dish"] == "Fish soup"


def test_customjson_missing_order_falls_back_to_position():
    data = {
        "2026-04-28": [
            {"meal": "Lunch", "dish": "Pasta carbonara"},
            {"meal": "Lunch", "dish": "Vegetarian lasagna"},
        ],
    }

    parsed = _menu()._parseMenuData(data)

    day1 = parsed["2026-04-28"]
    assert day1[0]["order"] == 1
    assert day1[1]["order"] == 2


def test_customjson_missing_meal_and_label_do_not_crash():
    data = {
        "2026-04-28": [
            {"dish": "Pasta carbonara"},
        ],
    }

    parsed = _menu()._parseMenuData(data)

    entry = parsed["2026-04-28"][0]
    assert entry["dish"] == "Pasta carbonara"
    assert entry["label"] is None
    assert entry["meal"] == ""


def test_customjson_empty_dish_is_discarded():
    data = {
        "2026-04-28": [
            {"meal": "Lunch", "dish": "Pasta carbonara"},
            {"meal": "Lunch", "dish": ""},
        ],
    }

    parsed = _menu()._parseMenuData(data)

    assert len(parsed["2026-04-28"]) == 1
    assert parsed["2026-04-28"][0]["dish"] == "Pasta carbonara"


def test_customjson_non_object_payload_raises_value_error():
    with pytest.raises(ValueError):
        _menu()._parseMenuData([{"meal": "Lunch", "dish": "Pasta carbonara"}])


def test_customjson_invalid_date_key_raises_value_error():
    data = {
        "måndag": [
            {"meal": "Lunch", "dish": "Pasta carbonara"},
        ],
    }

    with pytest.raises(ValueError):
        _menu()._parseMenuData(data)


def test_customjson_non_object_entry_raises_value_error():
    data = {
        "2026-04-28": ["not an object"],
    }

    with pytest.raises(ValueError):
        _menu()._parseMenuData(data)

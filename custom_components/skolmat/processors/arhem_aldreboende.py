'''

    Arhem äldreboende
    https://mpi.mashie.matildaplatform.com/public/menu/Sigtuna%20Kommun/c32fae7a
    
    Mashie format is both weird and misused.
    
            "Days": [
                {
                    "DayMenuDate": 1767567600000,
                    "DayMenus": [
                        {
                            "MenuAlternativeName": "Lunch husman",
                            "DayMenuInfo": "",
                            "DayMenuName": "Fisk med citronsås och kokt potatis",
                        },
                        {
                            "MenuAlternativeName": "Lunch dagens",
                            "DayMenuName": "Nötskav med svamp*, potatis, lingon, grönsaker",
                        },
                        {
                            "MenuAlternativeName": "Lunch vegetariskt",
                            "DayMenuName": "Frittata med oliver och salladsost",
                        },
                        {
                            "MenuAlternativeName": "Lunch Grov Paté ",
                            "DayMenuName": "Fisk med citronsås och kokt potatis",
                        },
                        {
                            "MenuAlternativeName": "Lunch Timbal ",
                            "DayMenuName": "A: Kycklingtimbal*, örtig sås*, potatismos*, ärttimbal*",
                        },
                        {
                            "MenuAlternativeName": "Middag 1",
                            "DayMenuName": "Chili con carne*, ris, grönsaker",
                        },
                        {
                            "MenuAlternativeName": "Middag 2",
                            "DayMenuName": "Drumsticks* med sweetchilisås* och ris",
                        },
                        {
                            "MenuAlternativeName": "Middag vegetariskt",
                            "DayMenuName": "Vegokorv* med senapssås* potatismos, grönsaker",
                        },
                        {
                            "MenuAlternativeName": "Middag Grov Paté ",
                            "DayMenuName": "Chili con carne*, ris, grönsaker",
                        },
                        {
                            "MenuAlternativeName": "Middag Timbal ",
                            "DayMenuName": "Fisktimbal*, citronsås*, potatismos*, ärttimbal*",
                        }
                    ]
                },

    The DayMenus entries is what will be passed as raw_entry to the processor function and we need to take it from there

    ----- we want to turn this:
    {
        "MenuAlternativeName": "Lunch dagens",
        "DayMenuName": "Nötskav med svamp*, potatis, lingon, grönsaker",
        ...
    }
    ------ into this:
    {
        "meal":  "Lunch",
        "label": "Dagens",
        "dish":  "Nötskav med svamp*, potatis, lingon, grönsaker",
        ...
    }

    ----- and this:
    {
        "MenuAlternativeName": "Middag 1",
        "DayMenuName": "Kyckling med soltorkade tomater och basilika*, pasta, grönsaker",
        ...
    }
    ----- into this:
    {
        "meal":  "Middag",
        "label": "Alt 1",
        "dish":  "Nötskav med svamp*, potatis, lingon, grönsaker",
        ...
    }
    
    --- etc etc
    
'''

from menu import MenuEntry, normalizeString
from datetime import date
from logging import getLogger
import json
log = getLogger(__name__)


MEAL_PREFIXES = ("lunch", "middag", "kvällsmat")
def entryProcessor(entryDate: date, order: int, raw_entry) -> MenuEntry:

    # log.info (json.dumps(raw_entry, indent=4, ensure_ascii=False))

    alt_raw = raw_entry.get("MenuAlternativeName")
    dish_raw = raw_entry.get("DayMenuName")

    meal = alt_raw
    label = None

    if alt_raw:
        alt_norm = normalizeString(alt_raw)
        alt_cf = alt_norm.casefold()

        if alt_cf == "dessert":
            meal = "Lunch"
            label = "Dessert"

        elif alt_cf == "timbal dess":
            meal = "Lunch"
            label = "Dessert Timbal"

        else:
            for prefix in MEAL_PREFIXES:
                if alt_cf.startswith(prefix):
                    prefix_len = len(prefix)
                    meal = alt_norm[:prefix_len]
                    rest = alt_norm[prefix_len:].strip()

                    if rest:
                        label = f"Alt {rest}" if rest.isdigit() else rest
                    break

    return {
        "meal_raw": alt_raw,
        "meal": normalizeString(meal) if meal else None,
        "dish_raw": dish_raw,
        "dish": normalizeString(dish_raw) if dish_raw else None,
        "label": normalizeString(label) if label else None,
        "order": order,
    }

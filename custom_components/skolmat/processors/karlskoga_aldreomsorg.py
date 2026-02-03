'''

    Karlskoga Äldreomsorg matsedel
    https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel
    
    ------ They misuse it like this: ------
    
    {
        "name": "Lunch",
        "courses": [
            {
                "name": "Kålpudding, sås, (potatis), grönsaker, (lingonsylt)",
                "optionName": "",
            }
        ]
    },
    {
        "name": "Fiskalternativ",
        "courses": [
            {
                "name": "Fiskgryta, (potatis), grönsaker",
                "optionName": "",
            }
        ],
        ...
    },
    {
        "name": "Kvällsmat",
        "courses": [
            {
                "name": "...",
                "optionName": "",
            }
        ]
    },

    ------ What they should have done is this: ------
    {
        "name": "Lunch",
        "courses": [
            {
                "name": "Kålpudding, sås, (potatis), grönsaker, (lingonsylt)",
                "optionName": "Huvudalternativ",
            },
            {
                "name": "Fiskgryta, (potatis), grönsaker",
                "optionName": "Fiskalternativ",
            },
            {
                "name": "Tårta",
                "optionName": "Dessert",
            },
        ]
    },
    {
        "name": "Kvällsmat",
        "courses": [
            {
                "name": "...",
                "optionName": "",
            }
        ]
    },

'''

from menu import MenuEntry, normalizeString
from datetime import date
from logging import getLogger
import json
log = getLogger(__name__)

def entryProcessor( entryDate: date, order:int, raw_entry) -> MenuEntry:

    # log.info (json.dumps(raw_entry, indent=4, ensure_ascii=False))

    entry:MenuEntry = {
        "meal_raw": raw_entry["mealName"],
        "meal": normalizeString(raw_entry["mealName"]),
        "dish_raw": raw_entry["name"],
        "dish": normalizeString(raw_entry["name"]),
        "label": raw_entry["optionName"],
        "order": order
    }

    meal_name = raw_entry["mealName"].casefold()

    if "alternativ" in meal_name or meal_name == "dessert":
        entry["meal"] = "Lunch"
        entry["label"] = normalizeString(raw_entry["mealName"])

    return entry
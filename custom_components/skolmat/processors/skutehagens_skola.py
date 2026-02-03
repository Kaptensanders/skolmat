'''

    Skutehagens skola
    https://skolmaten.se/skutehagens-skolan
    
    Simple string as raw_entry, label of meal often in pharantesis, like (Vegetarisk), (Fågel)

'''

import re
from menu import MenuEntry, normalizeString
from datetime import date
from logging import getLogger
log = getLogger(__name__)

LABEL_RE = re.compile(r"\(([^)]+)\)")

def entryProcessor(entryDate: date, order: int, raw_entry) -> MenuEntry:

    entry:MenuEntry = {
        "meal_raw": None,
        "meal": "Lunch",
        "dish_raw": raw_entry,
        "dish": normalizeString(raw_entry) or None,
        "label": None,
        "order": order,
    }

    if not isinstance(raw_entry, str):
        return entry

    m = LABEL_RE.search(raw_entry)
    if m:
        entry['label'] = normalizeString(m.group(1))
        entry['dish'] = normalizeString(LABEL_RE.sub("", raw_entry).strip())

    return entry
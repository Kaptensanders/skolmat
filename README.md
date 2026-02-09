![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=)
![Version](https://img.shields.io/github/v/release/Kaptensanders/skolmat)

## ⚠️ Version 3.0 release information

> **3.0 is a Breaking release**
> <br>The Skolmat integration started out as a simple integration for parsing skolmaten.se and populating a card. Now it grew to support multiple providers, some of which serves multiple meals a day and during weekends. Data structures from all providers are different, and on top of already weak schemas, kitchens impose their own keys and structures, making generic structuring rules hard. <br>So long time coming, the Skolmat data structures needed to be refactored to more robustly support generic handling and filtering.<br><br>
> **3.0 highlights**
> * Config flow has multiple filtering options to support better daily summaries for calendar events.
> * skolmaten.se back to using the api instead of rss
> * mateo.se switched to new api
> * added provider meny.skolmat.info
> * Card updated with some config options
> * Added visual UI editor support to card 
> * Added custom data preprocessor option for those multi-meal, multi course, custom key menues filtering cannot handle
> * Issue and compability fixes
>
> ... **new config and data format makes this a breaking release. Delete the old device and add again using the new config flow**


#
# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools (and some other places)

## Description
This component is most probably only valid in Sweden. It leverages data from skolmaten.se, webmenu.foodit.se, menu.matildaplatform.com, mpi.mashie.com or meny.mateo.se to create entities from a configured data source (url).

The integration exposes **two entities per configured school**, tied to a Skolmat device:
- a **sensor entity** showing today's lunch, and full menu data as attributes
- a **calendar entity** showing lunch events for past and upcoming days (90 day event history kept)


Use the entities as you please or install the companion lovelace custom card to display the menu for today or for the week:
https://github.com/Kaptensanders/skolmat-card

![image](https://user-images.githubusercontent.com/24979195/154963878-013bb9c0-80df-4449-9a8e-dc54ef0a3271.png)

---

## Installation (version 3.0+)

> **3.0 is a breaking release, old skolmat entities needs to be removed before upgrading**

1. Install the integration with **HACS**
2. Restart Home Assistant
3. Go to **Settings → Devices & Services**
4. Click **Add integration**
5. Search for **Skolmat**
6. Enter:
   * Name of the school
   * Menu URL
   * Optional lunch begin / end time for calendar events (or it will be a full day event)
   * The second dialog is for advanced manipulation of the menu. ~85% of users can just skip this. 
     * *Meal, dish type and dish filtering:* Affects what is displayed as sensor state and calendar event summary. For those kitchens with several meals and courses, here are some options for you to select what you want to display in the calendar events, and what to discard. 
     In order to keep it short and readable in the calendar overview, maybe you want to discard the "Vegetariskt" dish, here is where you do it.
     If your kitchen provides meals such as breakfast, etc, and you want to split the meals into separate entities, this can be done here. Filtering has no effect on the Skolmat card.
     * *Custom processor:* Manipulate the data entries, affects everything. If your kitchen misuse the provider schemas or imposes their own custom keys for meals, etc. This is a last-resort option to bend that data into something that will display nicely in a menu. Or it can be used to do some custom filtering, or plant easter eggs in the menu data. Read more below...

For each configured school, the integration will create:
- One sensor entity
- One calendar entity

Both entities belong to the same device and share the same underlying menu data.

## Entities

### Sensor
- Entity ID: `sensor.<school name>`
- State: today's available course(es) (as )
- Attributes contain the full parsed menu data (used by skolmat-card)

### Calendar
- Entity ID: `calendar.<school name>`
- One event per day, if you want separate entries for lunch, dinner etc; configure multiple devices and use filtering.
- All-day events by default
- Optional lunch begin / end time if configured
- Past events are kept for a limited time window

---

## Find the menu url

### skolmaten.se
1. Open https://skolmaten.se/ and follow the links to find your school.
2. When you arrive at the page with this week's menu, copy the url  
   Example:  
   `https://skolmaten.se/skutehagens-skolan`

---

### webmenu.foodit.se
1. Open https://webmenu.foodit.se/ and follow the links to find your school.
2. When you arrive at the page with this week's menu, copy the url  
   Example:  
   `https://webmenu.foodit.se/?r=6&m=617&p=883&c=10023&w=0&v=Week&l=undefined`

---

### menu.matildaplatform.com
1. Open https://menu.matildaplatform.com/ and find your school using the search box.
2. When you arrive at the page with this week's menu, copy the url  
   Example:  
   `https://menu.matildaplatform.com/meals/week/63fc93fcccb95f5ce5711276_indianberget`

---

### mashie.com
NOTE: mashie.com has different subdomains like mpi, sodexo, and possibly more.  
Example below is for mpi.mashie.com.

If the url to your weekly menu contains `/public/app/` you should be fine. Otherwise, let me know.

1. Open https://mpi.mashie.com/public/app and find your school using the search box
2. When you arrive at the page where you can see the menu, copy the url  
   Example:  
   `https://mpi.mashie.com/public/app/Laholms%20kommun/a326a379`

---

### mateo.se
**Note: mateo recently restructured their service. Old url's may have been changed**
1. Open https://meny.mateo.se and find your school using the search box
2. When you arrive at the page where you can see the menu, copy the url  
   Example:  
   `https://meny.mateo.se/kavlinge-utbildning/91`

---

### meny.skolmat.info
*Karlskrona and possibly other regions recently migrated from skolmaten.se to meny.skolmat.info.
1. Open https://meny.skolmat.info/ and follow the links to find your school.
2. When you arrive at the page with this week's menu, copy the url  
   Example:  
   `https://meny.skolmat.info/blekinge/karlskrona/asposkolan`


## Custom data preprocesor (advanced)

From version 3.0, custom python preprocessors can be used to manipulate the data entries into whatever you want.<br>
If your kitchen misuse the provider schemas or imposes their own custom keys for meals, etc. This is a last-resort option to bend that data into something that will display nicely in a menu.<br>
... or it can be used to do some custom filtering, or plant easter eggs in the menu data, etc etc

Consider the example below:
<img src="image-1.png" width="1369" />

custom_components/skolmat/processors/arhem_aldreboende.py:
```python
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
```

*Example processors:*<br>
[`arhem_aldreboende.py`](custom_components/skolmat/processors/arhem_aldreboende.py)<br>
[`karlskoga_aldreomsorg.py`](custom_components/skolmat/processors/karlskoga_aldreomsorg.py)




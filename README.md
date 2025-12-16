![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=)
![Version](https://img.shields.io/github/v/release/Kaptensanders/skolmat)

<h3 style="color:red; font-weight:bold;">
⚠️ Version 2.0 is a breaking release. YAML configuration is no longer supported.
</h3>

<h4 style="color:red; font-weight:bold;">
Note: skolmaten.se api key issue still not resolved, still only one week menu available via rss, sorry:
</h4>

# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools (and some other places)

## Description
This component is most probably only valid in Sweden. It leverages data from skolmaten.se, webmenu.foodit.se, menu.matildaplatform.com, mpi.mashie.com or meny.mateo.se to create entities from a configured data source (url).

From version 2.0, the integration exposes **two entities per configured school**:
- a **sensor entity** showing today's lunch
- a **calendar entity** showing lunch events for past and upcoming days (90 day event history kept)

The sensor attributes contain the full parsed menu data and are used by the calendar entity and the corresponding lovelace card.

Use the entities as you please or install the companion lovelace custom card to display the menu for today or for the week:
https://github.com/Kaptensanders/skolmat-card

![image](https://user-images.githubusercontent.com/24979195/154963878-013bb9c0-80df-4449-9a8e-dc54ef0a3271.png)

---

## Installation (version 2.0+)

> **YAML configuration is no longer supported as of version 2.0.**

1. Install the integration with **HACS**
2. Restart Home Assistant
3. Go to **Settings → Devices & Services**
4. Click **Add integration**
5. Search for **Skolmat**
6. Enter:
   - Name of the school
   - Menu URL
   - Optional lunch begin / end time for calendar events (or it will be a full day event)

For each configured school, the integration will create:
- One sensor entity
- One calendar entity

Both entities belong to the same device and share the same underlying menu data.

---

## Entities

### Sensor
- Entity ID: `sensor.skolmat_<school>`
- State: today's available course(es)
- Attributes contain the full parsed menu data (used by skolmat-card)

### Calendar
- Entity ID: `calendar.skolmat_<school>`
- One event per day (lunch)
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
1. Open https://meny.mateo.se and find your school using the search box
2. When you arrive at the page where you can see the menu, copy the url  
   Example:  
   `https://meny.mateo.se/kavlinge-utbildning/91`

---

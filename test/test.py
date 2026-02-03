import sys, os, json, aiohttp, asyncio, logging, importlib
from datetime import date, timedelta


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "custom_components", "skolmat"))
sys.path.append(os.path.join(ROOT, "test"))

menu_module = importlib.import_module("custom_components.skolmat.menu")
sys.modules.setdefault("menu", menu_module)



#sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'custom_components','skolmat'))
from menu import Menu





# processors
from custom_components.skolmat.processors.skutehagens_skola import entryProcessor as skolmaten1bProcessor
from custom_components.skolmat.processors.karlskoga_aldreomsorg import entryProcessor as matilda5bProcessor
from custom_components.skolmat.processors.arhem_aldreboende import entryProcessor as mashie3bProcessor

logging.basicConfig(level=logging.INFO)

def preProcessor_mashie3( entryDate: date, courseNo:int, mealName: str, courseName: str | None, courseDescription: str,) -> tuple[str, str | None, str]:
    """
    Handles:
      - 'Lunch husman'   -> ('Lunch', 'Husman', desc)
      - 'Middag Timbal'  -> ('Middag', 'Timbal', desc)
      - 'Middag 1'       -> ('Middag', 'Alt 1', desc)
      - 'Timbal Dess'    -> ('Dessert', 'Timbal', desc)
    """

    if not mealName:
        return mealName, courseName, courseDescription

    name = mealName.strip()

    # --- explicit special case ---
    if name == "Timbal Dess":
        return "Dessert", "Timbal", courseDescription

    parts = name.split(" ", 1)

    if len(parts) == 2:
        base, variant = parts

        if base in {"Frukost", "Lunch", "Middag"}:
            variant = variant.strip()

            # numeric variants → "Alt N"
            if variant.isdigit():
                variant = f"Alt {variant}"

            return base, variant, courseDescription

    return mealName, courseName, courseDescription

conf = {
    "foodit":       {"name": "Blåsut/Dalen förskolor",  "url": "https://webmenu.foodit.se/?r=1&m=180&p=1035&c=10228&w=0&v=Week&l=undefined", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten1":   {"name": "Skutehagsskolan",         "url": "https://skolmaten.se/skutehagens-skolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten1b":  {"name": "Skutehagsskolan",         "url": "https://skolmaten.se/skutehagens-skolan", "customMenuEntryProcessorCB": skolmaten1bProcessor, "readableDaySummaryCB": None},
    "skolmaten2":   {"name": "Påskbergsskolan", "url": "https://skolmaten.se/paskbergsskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten3":   {"name": "Klarebergsskolan 4-6, 7-9", "url": "https://skolmaten.se/klarebergsskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo1":       {"name": "Bosgårdsskolan", "url": "https://meny.mateo.se/molndal/66", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo2":       {"name": "Stallbackens förskola", "url": "https://meny.mateo.se/molndal/29", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo3":       {"name": "Emyhills förskola", "url": "https://meny.mateo.se/kavlinge-utbildning/88", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda1":     {"name": "Skolor: Älvkarleby, Skutskär", "url": "https://menu.matildaplatform.com/meals/week/63fc6e2dccb95f5ce56d8ada_skolor", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda2":     {"name": "Parkskolan restaurang", "url": "https://menu.matildaplatform.com/meals/week/63fc8f84ccb95f5ce570a0d4_parkskolan-restaurang", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda3":     {"name": "Dalajärs förskola", "url": "https://menu.matildaplatform.com/meals/week/6682a34d6337e8ced9340214_dalajars-forskola", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda4":     {"name": "Kramfors kommun, Äldreboenden", "url": "https://menu.matildaplatform.com/meals/week/682308b1e431ee42ec97f4c3_aldreboenden", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda5":     {"name": "Karlskoga, Äldreomsorg matsedel", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda5b":    {"name": "Karlskoga, Äldreomsorg matsedel", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": matilda5bProcessor, "readableDaySummaryCB": None},
    "mashie1":      {"name": "Ekhaga", "url": "https://mpi.mashie.com/public/app/Bjuvs%20kommun/c19fee26", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie2":      {"name": "Ekhaga", "url": "https://mpi.mashie.matildaplatform.com/public/app/Bjuvs%20kommun/c19fee26", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie3":      {"name": "Arhem äldreboende", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie3b":     {"name": "Arhem äldreboende", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": mashie3bProcessor, "readableDaySummaryCB": None},
    "mashie4":      {"name": "Brinkskolan", "url": "https://sodexo.mashie.com/public/menu/T%C3%A4by%20skolor%20Norr/5678b8c3", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie4b":     {"name": "Brinkskolan", "url": "https://sodexo.mashie.matildaplatform.com/public/menu/T%C3%A4by%20skolor%20Norr/5678b8c3", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None}
}

def createMenu(conf: dict):
    customMenuEntryProcessorCB = conf.get("customMenuEntryProcessorCB", None)
    readableDaySummaryCB = conf.get("readableDaySummaryCB", None)
    url = conf["url"]
    return Menu.createMenu(asyncio.to_thread, 
                           url=url, 
                           customMenuEntryProcessorCB = customMenuEntryProcessorCB, 
                           readableDaySummaryCB = readableDaySummaryCB
                           )

# override default with script argument "p test.py mashie4b"
default_entry = "skolmaten1b"

async def main ():

    global conf

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = default_entry

    if mode == "all":
        
        testData = {
            "date" : date.today().isoformat(),
            "tests" :[]
        }

        for name, config in conf.items():
            print ("\n-----------------------------------------------------------------------------------------------------------------")
            print (f"--- ▶️ Running: {name}: {conf[name]["name"]}-------")
            print ("-----------------------------------------------------------------------------------------------------------------")

            menu = createMenu(config)
            menu.DEBUG = False
            
            print (f"url (original):  {conf[name]["url"]}")
            print (f"url (rewritten): {menu.url}")

            print (f"🧩 Custom MenuEntry processor: {"\033[32mYES\033[0m" if conf[name]["customMenuEntryProcessorCB"] else "NO"}")

            async with aiohttp.ClientSession() as session:
                menuData = await menu.getMenu(session)
                if menuData:
                    print ("✅ Menu loaded: OK")
                else:
                    print ("❌ Menu loaded: No Data")
                    continue

                testData["tests"].append({
                    "test": name,
                    "name": config["name"],
                    "url": config["url"],
                    "data" : menuData,
                })

                for offset in range(0, 10):
                    d = date.today() + timedelta(days=offset)

                    entries = menu.getDayMenu(d)

                    if entries:  # first valid day with menu
                        print(f"📋 data entries for {d.isoformat() }:\n")
                        print (json.dumps(entries, indent=4, ensure_ascii=False))

                        # print(f"📋 Readable {d.isoformat() } menu:\n")
                        # print(menu.getReadableDayMenu(d))
                        # print(f"\n📋 Readable {d.isoformat() } summary:\n")
                        # print(menu.getReadableDaySummary(d))
                        break
                else:
                    print("❌ No menu found within the next 10 days")

            with open("output.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(testData, indent=4, ensure_ascii=False))

    else:

        if mode not in conf:
            print(f"{mode} - Not found")
            return

        menu = createMenu(conf[mode])
        menu.DEBUG = True
        menu.DUMP_TO_FILE = True

        async with aiohttp.ClientSession() as session:
            menuData = await menu.getMenu(session)
            print (f"Name: {mode}, URL: {conf[mode]["url"]}")
            print ("------------------------------------------------------------------------------------------------------")
            print (json.dumps(menuData, indent=4, ensure_ascii=False))

        for offset in range(0, 10):
            d = date.today() + timedelta(days=offset)

            entries = menu.getDayMenu(d)
            if entries:  # first valid day with menu
                print(f"\n--- {mode}: {d.isoformat()} MENU READABLE --------------------------------------------------")
                print(menu.getReadableDayMenu(d))
                print(f"\n--- {mode}: {d.isoformat()} SUMMARY READABLE -----------------------------------------------")
                print(menu.getReadableDaySummary(d))
                break
        else:
            print("No menu found within the next 10 days")


asyncio.run(main())
import sys, os, json, aiohttp, asyncio, logging
from datetime import date, timedelta
from fixtures.providers import PROVIDERS

ROOT = os.path.dirname(os.path.dirname(sys.path[0]))
sys.path.append(os.path.join(ROOT, 'custom_components', 'skolmat'))
sys.path.append(os.path.join(ROOT, 'test'))

logging.basicConfig(level=logging.INFO)

from menu import Menu

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

#    if mode == "fixed":

    if mode == "all":
        
        testData = {
            "date" : date.today().isoformat(),
            "tests" :[]
        }

        for name, config in PROVIDERS.items():
            print ("\n-----------------------------------------------------------------------------------------------------------------")
            print (f"--- ▶️ Running: {name}: {PROVIDERS[name]["name"]}-------")
            print ("-----------------------------------------------------------------------------------------------------------------")

            menu = createMenu(config)
            menu.DEBUG = False
            
            print (f"url (original):  {PROVIDERS[name]["url"]}")
            print (f"url (rewritten): {menu.url}")

            print (f"🧩 Custom MenuEntry processor: {"\033[32mYES\033[0m" if config["customMenuEntryProcessorCB"] else "NO"}")

            async with aiohttp.ClientSession() as session:
                menuData = await menu.getMenu(session)
                if menuData:
                    print ("✅ Menu loaded: OK")
                else:
                    print ("❌ Menu loaded: No Data")
                    continue

                testData["tests"].append({
                    "name": name,
                    "data" : menuData,
                })

                for offset in range(0, 10):
                    d = date.today() + timedelta(days=offset)

                    entries = menu.getDayMenu(d)

                    if entries:  # first valid day with menu
                        print(f"📋 data entries for {d.isoformat() }:\n")
                        print (json.dumps(entries, indent=4, ensure_ascii=False))
                        break
                else:
                    print("❌ No menu found within the next 10 days")

            with open("all_data.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(testData, indent=4, ensure_ascii=False))

    else:

        if mode not in PROVIDERS:
            print(f"{mode} - Not found")
            return

        menu = createMenu(PROVIDERS[mode])
        menu.DEBUG = True
        menu.DUMP_TO_FILE = True

        async with aiohttp.ClientSession() as session:
            menuData = await menu.getMenu(session)
            print (f"Name: {mode}, URL: {PROVIDERS[mode]["url"]}")
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
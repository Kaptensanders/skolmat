import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'custom_components','skolmat'))

from menu import Menu
import json
import aiohttp, asyncio
import logging

logging.basicConfig(level=logging.INFO)

conf = {
    "foodit": "https://webmenu.foodit.se/?r=6&m=617&p=883&c=10023&w=0&v=Week&l=undefined",
    "skolmaten": "https://skolmaten.se/menu/29f13515-185f-4df5-b39b-bca0a2bc4fc8?school=157fa289-ef68-411d-b2b5-d98014555c02",
    "matilda1": "https://menu.matildaplatform.com/meals/week/63fc6e2dccb95f5ce56d8ada_skolor",
    "matilda2": "https://menu.matildaplatform.com/meals/week/63fc8f84ccb95f5ce570a0d4_parkskolan-restaurang?startDate=2023-05-22&endDate=2023-05-28",
    "mashie": "https://mpi.mashie.com/public/app/Laholms%20kommun/a326a379",
    "skolmaten2": "https://skolmaten.se/menu/f2f243b5-f644-43cd-862b-20b7a4c58d41?school=dca1eb12-435a-4a46-93d2-d8e40035759f"
}

menu = Menu.createMenu(asyncio.to_thread, url=conf["skolmaten2"])
async def main ():
    async with aiohttp.ClientSession() as session:
        await menu.loadMenu(session)
        print (json.dumps(menu.menu, indent=4))
        print ("Today:" + "\n".join(menu.menuToday))


asyncio.run(main())
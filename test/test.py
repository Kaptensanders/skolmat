import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0]),'custom_components','skolmat'))

from menu import Menu
import json
import aiohttp, asyncio
import logging

logging.basicConfig(level=logging.INFO)

conf = {
    "foodit": "https://webmenu.foodit.se/?r=6&m=617&p=883&c=10023&w=0&v=Week&l=undefined",
    "skolmaten": "https://skolmaten.se/skutehagens-skolan",
    "matilda1": "https://menu.matildaplatform.com/meals/week/63fc6e2dccb95f5ce56d8ada_skolor",
    "matilda2": "https://menu.matildaplatform.com/meals/week/63fc8f84ccb95f5ce570a0d4_parkskolan-restaurang?startDate=2023-05-22&endDate=2023-05-28",
    "mashie": "https://mpi.mashie.com/public/app/Laholms%20kommun/a326a379",
    "skolmaten2": "https://skolmaten.se/annerstaskolan"
}

menu = Menu.createMenu(asyncio.to_thread, url=conf["skolmaten"])
async def main ():
    async with aiohttp.ClientSession() as session:
        await menu.loadMenu(session)
        print (json.dumps(menu.menu, indent=4))
        print ("Today:" + "\n".join(menu.menuToday))


asyncio.run(main())
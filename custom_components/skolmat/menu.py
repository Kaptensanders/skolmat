import feedparser, re
from abc import ABC, abstractmethod
from datetime import datetime, date
from logging import getLogger

import asyncio, aiohttp
from bs4 import BeautifulSoup
import json


log = getLogger(__name__)

class Menu(ABC):

    @staticmethod
    def createMenu (url:str):
        url = url.rstrip(" /")

        if SkolmatenMenu.provider in url:
            return SkolmatenMenu(url)
        elif FoodItMenu.provider in url:
            return FoodItMenu(url)
        elif MatildaMenu.provider in url:
            return MatildaMenu(url)
        else:
            raise Exception(f"URL not recognized as {SkolmatenMenu.provider}, {FoodItMenu.provider} or {MatildaMenu.provider}")


    def __init__(self, url:str):
        self.menu = {}
        self.url = url
        self.menuToday = []
        self.last_menu_fetch = None
        self._weeks = 2
        self._weekDays = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']

    
    @abstractmethod
    async def _loadMenu (self, aiohttp_session):
        return

    async def loadMenu(self, aiohttp_session):
        cur_menu = self.menu
        cur_menuToday = self.menuToday
        
        self.menu = {}
        self.menuToday = []

        try:
            await self._loadMenu(aiohttp_session)
            self.last_menu_fetch = datetime.now()
            return True

        except Exception as err:
            self.menu = cur_menu
            self.menuToday = cur_menuToday
            log.exception(f"Failed to load {self.provider} menu from {self.url}")
            return False

    def appendEntry(self, entryDate:date, courses:list):

        week = entryDate.isocalendar().week

        if not week in self.menu:
            self.menu[week] = []

        dayEntry = {
            "weekday": self._weekDays[entryDate.weekday()],
            "date": entryDate.isoformat(),
            "week": week,
            "courses": courses
        }
        
        if entryDate == date.today():
            self.menuToday = courses

        self.menu[week].append(dayEntry)


class FoodItMenu(Menu):

    provider = "foodit.se"

    def __init__(self, url:str):

        if not "foodit.se/rss" in url:
            url = url.replace("foodit.se", "foodit.se/rss")

        super().__init__(url)


    async def _getFeed(self, aiohttp_session):
        # returns only one week at the time
        weekMenus = []
        for week in range(self._weeks):
            rss = re.sub(r'\&w=[0-9]*\&', f"&w={week}&", self.url)
            async with aiohttp_session.get(rss) as response:
                raw_feed = await response.text()
                weekMenus.append(feedparser.parse(raw_feed))

        feed = weekMenus.pop(0)
        for f in weekMenus:
            feed["entries"].extend(f["entries"])

        return feed

    async def _loadMenu(self, aiohttp_session):

        menuFeed = await self._getFeed(aiohttp_session)
        for day in menuFeed["entries"]:
            
            entryDate = datetime.strptime(day["title"].split()[1], "%Y%m%d").date()
            courses = [s.strip() for s in day['summary'].split(':') if s]
            self.appendEntry(entryDate, courses)


class SkolmatenMenu(Menu):

    provider = "skolmaten.se"

    def __init__(self, url:str):

        if not "/rss/weeks" in url: # keep for bw comp, changed to not need rss/weeks in 1.2.0
            url = f"{url}/rss/weeks"

        super().__init__(url)

    async def _getFeed(self, aiohttp_session):
        
        async with aiohttp_session.get(f"{self.url}?limit={self._weeks}") as response:
            raw_feed = await response.text()
            return feedparser.parse(raw_feed)
        
   
    async def _loadMenu(self, aiohttp_session):

        menuFeed = await self._getFeed(aiohttp_session)
        for day in menuFeed["entries"]:
            entryDate = datetime(day['published_parsed'][0], day['published_parsed'][1], day['published_parsed'][2]).date()
            courses = day['summary'].split('<br />')
            self.appendEntry(entryDate, courses)



class MatildaMenu (Menu):
    provider = "matildaplatform.com"

    def __init__(self, url:str):
        # https://menu.matildaplatform.com/meals/week/63fc93fcccb95f5ce5711276_indianberget
        super().__init__(url)
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"}

    async def _getWeek(self, aiohttp_session, url):

        try:
            async with aiohttp_session.get(url, headers=self.headers, raise_for_status=True) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                jsonData = soup.select("#__NEXT_DATA__")[0].string
                return json.loads(jsonData)["props"]["pageProps"]
        except Exception as err:
            log.exception(f"Failed to retrieve {url}")
            raise        


    async def _loadMenu(self, aiohttp_session):

        w1 = await self._getWeek(aiohttp_session, self.url)
        w2 = await self._getWeek(aiohttp_session, "https://menu.matildaplatform.com" + w1["nextURL"])

        dayEntries = [*w1["meals"], *w2["meals"]]

        for day in dayEntries:
            entryDate = datetime.strptime(day["date"], "%Y-%m-%dT%H:%M:%S").date() # 2023-06-02T00:00:00
            courses = []
            for course in day["courses"]:
                courses.append(course["name"])
            self.appendEntry(entryDate, courses)

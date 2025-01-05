import feedparser, re
from abc import ABC, abstractmethod
from datetime import datetime, date, timezone
from dateutil import tz
from logging import getLogger
from bs4 import BeautifulSoup
import json

log = getLogger(__name__)

class Menu(ABC):

    @staticmethod
    def createMenu (hass, url:str):
        url = url.rstrip(" /")

        if SkolmatenMenu.provider in url:
            return SkolmatenMenu(hass, url)
        elif FoodItMenu.provider in url:
            return FoodItMenu(hass, url)
        elif MatildaMenu.provider in url:
            return MatildaMenu(hass, url)
        elif MashieMenu.provider in url:
            return MashieMenu(hass, url)
        else:
            raise Exception(f"URL not recognized as {SkolmatenMenu.provider}, {FoodItMenu.provider}, {MatildaMenu.provider} or {MashieMenu.provider}")


    def __init__(self, hass, url:str):
        self.hass = hass
        self.menu = {}
        self.url = self._fixUrl(url)
        self.menuToday = []
        self.last_menu_fetch = None
        self._weeks = 2
        self._weekDays = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']

    @abstractmethod
    async def _fixUrl (self, url:str):
        return url

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

        if type(entryDate) is not date:
            raise TypeError("entryDate must be date type") 

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


    async def parse_feed(self, raw_feed):

        def parse_helper(raw_feed):
            return feedparser.parse(raw_feed)
    
        return await self.hass.async_add_executor_job(parse_helper, raw_feed)


class FoodItMenu(Menu):

    provider = "foodit.se"

    def __init__(self, hass, url:str):

        super().__init__(hass, url)

    def _fixUrl(self, url:str):

        if not "foodit.se/rss" in url:
            url = url.replace("foodit.se", "foodit.se/rss")
        return url

    async def _getFeed(self, aiohttp_session):       
        
        # returns only one week at the time
        weekMenus = []
        for week in range(self._weeks):
            rss = re.sub(r'\&w=[0-9]*\&', f"&w={week}&", self.url)
            async with aiohttp_session.get(rss) as response:
                
                # Offload feedparser.parse to an executor
                raw_feed = await response.text()
                parsed_feed = await self.parse_feed(raw_feed)
                weekMenus.append(parsed_feed)                
                
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

    def __init__(self, hass, url:str):
        super().__init__(hass, url)

    def _fixUrl(self, url:str):
        if not "/rss/weeks" in url: # keep for bw comp, changed to not need rss/weeks in 1.2.0
            url = f"{url}/rss/weeks"
        return url

    async def _getFeed(self, aiohttp_session):
        
        async with aiohttp_session.get(f"{self.url}?limit={self._weeks}") as response:
            raw_feed = await response.text()
            return await self.parse_feed(raw_feed)
        
   
    async def _loadMenu(self, aiohttp_session):

        menuFeed = await self._getFeed(aiohttp_session)
        for day in menuFeed["entries"]:
            entryDate = datetime(day['published_parsed'][0], day['published_parsed'][1], day['published_parsed'][2]).date()
            courses = day['summary'].split('<br />')
            self.appendEntry(entryDate, courses)



class MatildaMenu (Menu):
    provider = "matildaplatform.com"

    def __init__(self, hass, url:str):
        # https://menu.matildaplatform.com/meals/week/63fc93fcccb95f5ce5711276_indianberget
        super().__init__(hass, url)
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"}

    def _fixUrl(self, url: str):
        return url

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

class MashieMenu(Menu):

    provider = "mashie.com"

    def __init__(self, hass, url:str):

        super().__init__(hass, url)
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36",
                        "cookie": "cookieLanguage=sv-SE"} # set page lang to Swe

    def _fixUrl(self, url):
        # observed variants:
        #   mpi.mashie.com/public/app/Laholms%20kommun/a326a379
        #   sodexo.mashie.com/public/app/Akademikrogen%20skolor/d47bc6bf
        #
        #  all subdomains seem to have a corresponding ../menu/.. url to the ../app/..
        #  the ../menu/.. page contains json data for the menu, so use that instead of scraping the page

        if "/app/" in url:
            url = url.replace("/app/", "/menu/")

        return url

    async def _loadMenu(self, aiohttp_session):

        def preserveTs(match_obj):
            if match_obj.group() is not None:
                return re.sub(r"[^0-9]", "", match_obj.group())

        #se = tz.gettz("Europe/Stockholm")
        # se = await run_in_executor(None, gettz, "Europe/Stockholm")
        se = await self.hass.async_add_executor_job(tz.gettz, "Europe/Stockholm")

        try:
            async with aiohttp_session.get(self.url, headers=self.headers, raise_for_status=True) as response:
                html = await response.text()

                soup = BeautifulSoup(html, 'html.parser')
                jsonData = soup.select_one("script").string
                # discard javascript variable assignment, weekMenues = {...
                jsonData = jsonData[jsonData.find("{") - 1:]
                # replace javascipt dates (new Date(1234567...) with only the ts
                jsonData = re.sub(r"new Date\([0-9]+\)", preserveTs, jsonData)
                # json should be fine now
                data = json.loads(jsonData)

                w = 1
                for week in data["Weeks"]:
                    for day in week["Days"]:
                        entryDate = datetime.fromtimestamp(day["DayMenuDate"] / 1000, timezone.utc)
                        entryDate = entryDate.astimezone(tz=se).date()
                        courses = []
                        for course in day["DayMenus"]:
                            courses.append(course["DayMenuName"].strip())
                        
                        self.appendEntry(entryDate, courses)
                    
                    w = w + 1 
                    if w > 2:
                        break

        except Exception as err:
            log.exception(f"Failed to retrieve {self.url}")
            raise



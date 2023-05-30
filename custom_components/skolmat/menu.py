import feedparser, re
from abc import ABC, abstractmethod
from datetime import datetime, date
from logging import getLogger

log = getLogger(__name__)

class Menu(ABC):

    @staticmethod
    def createMenu (url:str):

        url = url.rstrip(" /")

        if "skolmaten.se" in url:
            return SkolmatenMenu(url)
        elif "foodit.se" in url:
            return FoodItMenu(url)
        elif "matildaplatform.com" in url:
            return MatildaMenu(url)
        else:
            raise Exception("URL not recognized as skolmaten.se, webmenu.foodit.se or matildaplatform.com")


    def __init__(self, url:str):
        self.menu = {}
        self.url = url
        self.menuToday = []
        self.last_menu_fetch = None
        self._weeks = 2
        self._weekDays = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']

    
    @abstractmethod
    def _loadMenu (self):
        return

    def loadMenu(self):
        
        cur_menu = self.menu
        cur_menuToday = self.menuToday
        
        self.menu = {}
        self.menuToday = []

        try:
            self._loadMenu()
            self.last_menu_fetch = datetime.now()

        except Exception as err:
            self.menu = cur_menu
            self.menuToday = cur_menuToday
            log.critical(f"Failed to load {self.provider} menu from {self.url}")
            raise


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


    def _getFeed(self):
        # returns only one week at the time
        weekMenus = []
        for week in range(self._weeks):
            rss = re.sub(r'\&w=[0-9]*\&', f"&w={week}&", self.url)
            weekMenus.append(feedparser.parse(rss))

        feed = weekMenus.pop(0)
        for f in weekMenus:
            feed["entries"].extend(f["entries"])

        return feed

    def _loadMenu(self):

        menuFeed = self._getFeed()
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

    def _getFeed(self):
        return feedparser.parse(f"{self.url}?limit={self._weeks}")
   
    def _loadMenu(self):

        menuFeed = self._getFeed()
        for day in menuFeed["entries"]:
            
            entryDate = datetime(day['published_parsed'][0], day['published_parsed'][1], day['published_parsed'][2]).date()
            courses = day['summary'].split('<br />')
            self.appendEntry(entryDate, courses)



class MatildaMenu (Menu):
    pass

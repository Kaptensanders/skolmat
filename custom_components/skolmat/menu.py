import feedparser, re
from datetime import datetime

class Menu(object):
    
    def __init__(self, rss:str):
        self.menu = {}
        self.menuToday = []
        self.last_menu_fetch = None
        self._weeks = 2
        self._weekDays = ['Måndag', 'Tisdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lördag', 'Söndag']
        self.initMenuType(rss)
    
    def initMenuType (self, rss):

        self._rss = rss.rstrip(" /")

        # skolmaten.se
        if "skolmaten.se" in rss:
            self.provider = "skolmaten.se"
            if not "/rss/weeks" in rss: # keep for bw comp, changed to not need rss/weeks in 1.2.0
                self._rss = f"{self._rss}/rss/weeks"

        elif "foodit.se" in rss:
            self.provider = "foodit.se"
            if not "foodit.se/rss" in rss:
                self._rss = rss.replace("foodit.se", "foodit.se/rss")
        else:
            raise Exception("RSS feed not recognized as skolmaten.se or webmenu.foodit.se")

    def isSkolmaten(self):
        return self.provider == "skolmaten.se"

    def isMatilda(self):
        return self.provider == "foodit.se"

    def _getDayEntry (self, day):

        if self.isSkolmaten():
            return datetime(day['published_parsed'][0], day['published_parsed'][1], day['published_parsed'][2]).date(), day['summary'].split('<br />')
        else:
            courses = day['summary'].split(':')
            return datetime.strptime(day["title"].split()[1], "%Y%m%d").date(), [s.strip() for s in courses if s]

    def getFeed(self):

        if self.isSkolmaten():
            feed = feedparser.parse(f"{self._rss}?limit={self._weeks}")
        else: # returns only one week at the time
            weekMenus = []
            for week in range(self._weeks):
                rss = re.sub(r'\&w=[0-9]*\&', f"&w={week}&", self._rss)
                weekMenus.append(feedparser.parse(rss))

            feed = weekMenus.pop(0)
            for f in weekMenus:
                feed["entries"].extend(f["entries"])

        return feed

    def loadMenu(self):

        menuFeed = self.getFeed()
        menu = {}
        today = datetime.now().date()
        menuToday = None

        for day in menuFeed["entries"]:
            
            date, courses = self._getDayEntry(day)           
            week = date.isocalendar().week
            
            if not week in menu:
                menu[week] = []
            dayEntry = {
                "weekday": self._weekDays[date.weekday()],
                "date" : date.isoformat(),
                "week": week,
                "courses": courses
            }
            menu[week].append(dayEntry)
            if date == today:
                menuToday = courses

        self.menuToday = menuToday
        
        self.menu = menu            
        self.last_menu_fetch = datetime.now()


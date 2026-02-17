import feedparser, re, asyncio, traceback, json, html  # noqa: E401
from abc import ABC, abstractmethod
from datetime import datetime, date, timezone, timedelta
from dateutil import tz, parser
from logging import getLogger
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote
from collections.abc import Callable
from typing import TypedDict, TypeAlias, Any
from pathlib import Path
from .dayfilter import DayFilter

# Precompiled regexes (clarity + speed)
RE_PAREN_MARK = re.compile(r"\(([A-Za-z0-9])\)")
RE_PREFIX_MARK = re.compile(r"^[A-Za-z]:\s*")
RE_ASTERISK = re.compile(r"\*+")
log = getLogger(__name__)

def normalizeString(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""

    # decode HTML entities (e.g., &amp;)
    s = html.unescape(s)

    # normalize all whitespace
    s = " ".join(s.split())

    # remove known junk markers
    s = RE_PREFIX_MARK.sub("", s)
    s = RE_PAREN_MARK.sub("", s)
    s = RE_ASTERISK.sub("", s)

    # normalize commas
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"^\s*,\s*", "", s)
    s = re.sub(r",\s*$", "", s)

    # normalize whitespace again
    s = re.sub(r"\s+", " ", s).strip()

    if not s:
        return ""

    return s[0].upper() + s[1:]


class MenuEntry(TypedDict):
    meal_raw: str | None
    meal: str | None
    dish_raw: str
    dish: str
    label: str | None
    order: int

MenuData: TypeAlias = dict[str, list[MenuEntry]]

class Menu(ABC):

    _NO_MENU_MESSAGE = ""
    DEBUG = False
    DUMP_TO_FILE = False

    @staticmethod
    def createMenu (asyncExecutor, 
                    url:str, 
                    customMenuEntryProcessorCB: Callable | None = None,
                    readableDaySummaryCB: Callable | None = None
                ):
        url = url.rstrip(" /")

        if SkolmatenMenu.provider in url:
            return SkolmatenMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif FoodItMenu.provider in url:
            return FoodItMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif MatildaMenu.provider in url:
            return MatildaMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif MashieMenu.provider in url:
            return MashieMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif MateoMenu.provider in url:
            return MateoMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif SkolmatInfoMenu.provider in url:
            return SkolmatInfoMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        elif MenuGoMenu.provider in url:
            return MenuGoMenu(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        else:
            raise Exception(
                f"URL not recognized as {SkolmatenMenu.provider}, {FoodItMenu.provider}, "
                f"{MatildaMenu.provider}, {MashieMenu.provider}, {MateoMenu.provider} or {SkolmatInfoMenu.provider}"
            )

    def __init__(self, 
                 asyncExecutor, 
                 url:str,
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None, 
                 menuValidHours:int = 4
            ):
        
        self.asyncExecutor = asyncExecutor
        self._menu:MenuData = {}
        self._customMenuEntryProcessorCB:Callable = customMenuEntryProcessorCB
        self.menuProcessorSuccessful = False
        self._readableDaySummaryCB:Callable = readableDaySummaryCB
        self.url:str = self._fixUrl(url)
        self._menuToday:list = [] 
        self.last_menu_fetch:datetime | None = None
        self._weeks:int = 2
        self._menuValidHours:int  = menuValidHours
        self._lock = asyncio.Lock()
        self._dayFilter:DayFilter = None
        self._nextAllowed = None
        self._faliureCount = 0
        self._lastFail = None

    @abstractmethod
    def _fixUrl (self, url:str) -> str:
        ...
    @abstractmethod
    async def _loadMenu (self, aiohttp_session) -> MenuData:
        ...
    @abstractmethod
    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry | None:
        """
         NOTE: Must be called by the derived version!!
         _customMenuEntryProcessorCB(entryDate:date, order:int, raw_entry:Any) -> MenuEntry behaviour:
            * return None to default to standard processing
            * set dish to None to discard entry
        """
        if self._customMenuEntryProcessorCB:
            try:
                entry:MenuEntry = self._customMenuEntryProcessorCB(entryDate, order, raw_entry)
                self. menuProcessorSuccessful = True
                return entry
            except Exception as e:
                self. menuProcessorSuccessful = False
                log.error( "Custom menu entry processor failed for %s: %s",self.url, e)
        return None


    def _addFail (self):
        self._faliureCount += 1
        self._lastFail = datetime.now()
    
    def _resetFail(self):
        self._faliureCount = 0

    def _isFailRetry(self):
        return self._faliureCount > 0

    def _getRetryDelay (self):

        # after first fail, add a 2 min minimum delay 
        # after that add +20 min per consecutive fail

        if self._faliureCount == 1:
            return timedelta(minutes = 2)

        retryDelay = self._faliureCount * 20 * 60 # mins
        return timedelta(seconds=retryDelay)


    def _getWeekNumber (self, offset:int = 0):
        weekDate = date.today() + timedelta(weeks=offset)
        return weekDate.isocalendar()

    async def getMenu(self, aiohttp_session, force:bool=False) -> MenuData | None:

        """
        getMenu returns:
            non-empty dict: containing valid data
            empty dict: valid, but no entries
            None: current data is invalid and fetch failed
        """

        async with self._lock:

            if self._lastFail is not None and self._lastFail.date() != datetime.now().date():
                self._resetFail() # reset once every new day

            if self._isFailRetry() and not force:
                if self._nextAllowed > datetime.now():
                    if self._isMenuValid():
                        return self._menu 
                    else:
                        return None
                


            if not force and self._isMenuValid():
                return self._menu
            try:

                menu = await self._loadMenu(aiohttp_session)
                self.last_menu_fetch = datetime.now()
                self._menu = menu
                self._resetFail()

            except Exception as err:
                
                self._addFail()
                self._nextAllowed = datetime.now() + self._getRetryDelay()

                tb = traceback.extract_tb(err.__traceback__)[-1]
                log.error(
                    f"Failed to load {self.provider} menu from {self.url} "
                    f"at {Path(tb.filename).name}:{tb.lineno}"
                    f" - [{type(err).__name__}]: {err}"
                )

                # loading failed, return the existing menu only if it contains
                # valid furure entries, or at least today
                today = date.today()
                for isodate in self._menu:
                    day = date.fromisoformat(isodate)
                    if day >= today:
                        return self._menu                
                
                return None

            return self._menu

    def getReadableDayMenu(self, d:date | str) -> str:
        
        isodate = str if isinstance(d, str) else d.isoformat()
        
        if isodate not in self._menu:
            return ""
        entries = self._menu[isodate]
        return self._defaultReadableDayMenu(entries) or ""

    def getReadableTodayMenu(self) -> str:
        return self.getReadableDayMenu(date.today()) 

    def getSummaryFilterKeywords (self, reference_date: date | None = None):
        # get meal and label keywords that can be used for filtering
        no_results_info = "No filtering keyword results found in menu data. See logs for more info."

        if not self._menu:
            return {
                "meals": [],
                "labels": [],
                "info": no_results_info,
            }

        entries_by_date: dict[date, list[MenuEntry]] = {}
        for iso, entries in self._menu.items():
            if not entries:
                continue
            try:
                entry_date = date.fromisoformat(iso)
            except ValueError:
                continue
            entries_by_date[entry_date] = entries

        if not entries_by_date:
            return {
                "meals": [],
                "labels": [],
                "info": no_results_info,
            }

        def collect_keywords(entries: list[MenuEntry]) -> tuple[list[str], list[str]]:
            meals: list[str] = []
            labels: list[str] = []
            seen_meals: set[str] = set()
            seen_labels: set[str] = set()

            for entry in entries:
                meal = normalizeString(entry.get("meal") or "")
                if meal and meal not in seen_meals:
                    meals.append(meal)
                    seen_meals.add(meal)

                label = normalizeString(entry.get("label") or "")
                if label and label not in seen_labels:
                    labels.append(label)
                    seen_labels.add(label)

            return meals, labels

        def collect_all_keywords() -> tuple[set[str], set[str]]:
            all_meals: set[str] = set()
            all_labels: set[str] = set()
            for entries in entries_by_date.values():
                day_meals, day_labels = collect_keywords(entries)
                all_meals.update(day_meals)
                all_labels.update(day_labels)
            return all_meals, all_labels

        def first_with_signal(dates: list[date]) -> tuple[date | None, list[str], list[str]]:
            for d in dates:
                day_meals, day_labels = collect_keywords(entries_by_date[d])
                if day_meals or day_labels:
                    return d, day_meals, day_labels
            return None, [], []

        today = reference_date or date.today()
        meals: list[str] = []
        labels: list[str] = []

        future_dates = sorted(d for d in entries_by_date if d >= today)
        past_dates = sorted((d for d in entries_by_date if d < today), reverse=True)

        chosen_date, meals, labels = first_with_signal(future_dates)
        if not chosen_date:
            chosen_date, meals, labels = first_with_signal(past_dates)

        all_meals, all_labels = collect_all_keywords()
        extra_meals = sorted(m for m in all_meals if m not in meals)
        extra_labels = sorted(l for l in all_labels if l not in labels)
        warning = ""

        if extra_meals or extra_labels:
            log.warning(
                "Summary filter discovery: additional keywords found outside chosen day "
                "(extra_meals=%s extra_labels=%s)",
                extra_meals,
                extra_labels,
            )
            warning = " Warning: other days include additional meals/labels; discovery may be incomplete. See logs for details."

        if meals or labels:
            info = (
                f"Found {len(meals)} results for meals, and {len(labels)} dish labels in menu data."
                f"{warning}"
            )
        else:
            info = f"{no_results_info}{warning}"

        return {
            "meals": meals,
            "labels": labels,
            "info": info,
        }

    def setSummaryFilters(self, raw_config: dict | None):
        self._dayFilter = DayFilter(raw_config)

    def getReadableDaySummary(self, d:date, filtered:bool = True) -> str:

        isodate = d.isoformat()
        if isodate not in self._menu:
            return ""
        
        entries = self._menu[isodate]

        # _readableDaySummaryCB logic is implemented, but lets leave undocumented and unused for now.
        # We  finalize the filtering concepts first and see if this approach still apply and adds meaningful value
        if self._readableDaySummaryCB:
            try:
                return self._readableDaySummaryCB(entries)
            except Exception as e:
                data = json.dumps(entries, indent=4, ensure_ascii=False)
                log.error(f"Custom summary processor failed - {str(e)} for entry:\n{data}")

        if filtered and self._dayFilter:
            entries = self._dayFilter.filter(entries)

        return self._defaultReadableDaySummary(entries) or ""

    def getDayMenu (self, d:date | str) -> list[MenuEntry]:
        isodate = str if isinstance(d, str) else d.isoformat()
        return self._menu.get(isodate, None)

    def getReadableTodaySummary(self) -> str:
        return self.getReadableDaySummary(date.today())


    def _defaultReadableDayMenu(self, entries: list[MenuEntry]) -> str:
        if not entries:
            return ""

        lines: list[str] = []
        current_meal: str | None = None

        for entry in entries:
            meal = entry.get("meal")
            label = entry.get("label")
            dish = entry.get("dish")

            if not dish:
                continue  # safety, though parent already filtered

            # New meal section
            if meal != current_meal:
                if lines:
                    lines.append("")  # blank line between meals
                lines.append(f"[{meal}]")
                current_meal = meal

            # Entry line
            if label:
                lines.append(f"• {label}: {dish}")
            else:
                lines.append(f"• {dish}")

        return "\n".join(lines)


    def _defaultReadableDaySummary(self, entries:list[MenuEntry]) -> str:
        # derive as needed...
        return " | ".join(entry["dish"] for entry in entries)

    def _isMenuValid (self) -> bool:

        if not self._menu:
            return False

        if not isinstance(self.last_menu_fetch, datetime):
            return False

        now = datetime.now()
        if now.date() != self.last_menu_fetch.date():
            return False
    
        if now - self.last_menu_fetch >= timedelta(hours=self._menuValidHours):
            return False
        
        return True

    def _addMenuEntry (self, menu:MenuData, d:date, entry:MenuEntry | None):

        """
        Adds entry to menu if and only if it is valid, eg "dish" must be set.
        Invalid entries are silently discarded.
        """

        if entry and entry.get("dish"):
            isodate = d.isoformat()
            if isodate not in menu:
                menu[isodate] = []

            menu[isodate].append(entry)

    async def _parse_feed(self, raw_feed):

        def parse_helper(raw_feed):
            return feedparser.parse(raw_feed)

        data = await self.asyncExecutor(parse_helper, raw_feed)
        if data.get("bozo"): # feedparser sets bozo=1 if not cleanly parsed, but records could still exist
            bozo_exception = data.get("bozo_exception")
            if not data.get("entries"):
                raise ValueError(f"RSS parsing failed: {bozo_exception}")
            log.warning("RSS not cleanly parsed, but entries exist: %s", bozo_exception)
        return data
    
    def _createMenuEntry (self, order: int, meal_raw: str | None, dish_raw: str, label: str | None) -> MenuEntry:

        return  {
#            "meal_raw": meal_raw,
            "meal": normalizeString(meal_raw),
#            "dish_raw": dish_raw,
            "dish": normalizeString(dish_raw),
            "label": label,
            "order": order
        }

    def _dumpData(self, data:dict):
        if not self.DEBUG: 
            return
        
        if self.DUMP_TO_FILE:
            with open("data_"+self.__class__.__name__ + ".json", "w", encoding="utf-8") as f:
                f.write(f"// provider: {self.provider}, URL: {self.url}\n\n")
                json.dump(data, f, indent=4, ensure_ascii=False)
        else:
            log.info(json.dumps(data, indent=4, ensure_ascii=False))


class FoodItMenu(Menu):

    provider = "foodit.se"

    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
            ):

        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)

    def _fixUrl(self, url:str) -> str:

        if "foodit.se/rss" not in url:
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
                parsed_feed = await self._parse_feed(raw_feed)
                weekMenus.append(parsed_feed)                
    
        feed = weekMenus.pop(0)
        for f in weekMenus:
            feed["entries"].extend(f["entries"])

        return feed

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry
        
        return self._createMenuEntry (order, "Lunch", raw_entry, f"Alt {order}")

    async def _loadMenu(self, aiohttp_session) -> MenuData:

        menuFeed = await self._getFeed(aiohttp_session)
        self._dumpData(menuFeed)

        menu:MenuData = {}

        for day in menuFeed["entries"]:

            entryDate = datetime.strptime(day["title"].split()[1], "%Y%m%d").date()
            coursesList = [s.strip() for s in day['summary'].split(':') if s]
            courseNo = 1
            for course in coursesList:
                menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                self._addMenuEntry(menu, entryDate, menuEntry)
                courseNo = courseNo + 1

        return menu

class MateoMenu(Menu):

    provider = "mateo.se"

    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
            ):

        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json", 
            "Referer": f"https://{self.provider}/",
            }
        
    def _fixUrl(self, url: str) -> str:

        parsed = urlparse(url)
        id = parsed.path.rstrip("/").split("/")[-1]

        if not id.isdigit():
            raise ValueError("school id could not be extracted from url")

        newUrl = "https://meny-api.mateo.se/api/v1/days/" + id
        return newUrl

    async def _fetchMenu (self, aiohttp_session, startDate:date, endDate:date):

        url = f"{self.url}?from={startDate.isoformat()}&to={endDate.isoformat()}"
        async with aiohttp_session.get(url, headers=self.headers, raise_for_status=True) as response:
            html = await response.text()
            return json.loads(html)


    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        if raw_entry["labels"]:
            label = ", ".join(label["name"].strip() for label in raw_entry["labels"])
        else:
            label = raw_entry["type"]

        return self._createMenuEntry (order, "Lunch", raw_entry["name"], label)

    async def _loadMenu(self, aiohttp_session) -> MenuData:

        today = date.today()
        firstDay = today - timedelta(days=today.weekday())
        if today.weekday() >= 5:
           firstDay += timedelta(days=7)

        dayEntries = await self._fetchMenu(aiohttp_session, startDate=firstDay, endDate=(firstDay + timedelta(days=14)))

        self._dumpData(dayEntries)
        menu:MenuData = {}

        for day in dayEntries:
            entryDate = parser.isoparse(day["date"]).date()
            courseNo = 1
            for course in day["meals"]:
                menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                self._addMenuEntry(menu, entryDate, menuEntry)
                courseNo = courseNo + 1
        return menu

class SkolmatenMenu(Menu):

    provider = "skolmaten.se"


    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
            ):

        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json", 
            "Referer": f"https://{self.provider}/",
            "client-token": "web-eaa12e50-c84c-4b4a-9cfe-4e3fcbcd9165"
            }


    def _fixUrl(self, url: str) -> str:

        parsed = urlparse(url)
        schoolName = parsed.path.lstrip("/")

        if schoolName is None:
            raise ValueError("school name could not be extracted from url")


        newUrl = "https://skolmaten.se/api/4/menu/school/" + schoolName
        return newUrl

    async def _getWeek(self, aiohttp_session, url):

        def remove_images(obj):
            if isinstance(obj, dict):
                return {k: remove_images(v) for k, v in obj.items() if k != "image"}
            elif isinstance(obj, list):
                return [remove_images(i) for i in obj]
            return obj

        async with aiohttp_session.get(url, headers=self.headers, raise_for_status=True) as response:
            html = await response.text()
            return json.loads(html, object_hook=remove_images)

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        labels = [a["sv"] for a in raw_entry["MealAttributes"]]
        label = ", ".join(labels)

        return self._createMenuEntry (order, "Lunch", raw_entry["name"], label)

    async def _loadMenu(self, aiohttp_session) -> MenuData:

            weekOffset = 0 if date.today().weekday() < 5 else 1
            thisWeek  = self._getWeekNumber (0 + weekOffset)
            nextWeek  = self._getWeekNumber (1 + weekOffset)

            w1Url = f"{self.url}?year={thisWeek[0]}&week={thisWeek[1]}"
            w2Url = f"{self.url}?year={nextWeek[0]}&week={nextWeek[1]}"

            w1 = await self._getWeek(aiohttp_session, w1Url)
            w2 = await self._getWeek(aiohttp_session, w2Url)
  
            dayEntries = [
                *(w1["WeekState"]["Days"] if isinstance(w1.get("WeekState"), dict) else []),
                *(w2["WeekState"]["Days"] if isinstance(w2.get("WeekState"), dict) else [])
            ]

            self._dumpData(dayEntries)
            menu:MenuData = {}

            for day in dayEntries:
                entryDate = parser.isoparse(day["date"]).date()
                courseNo = 1
                for course in day["Meals"]:
                    menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                    self._addMenuEntry(menu, entryDate, menuEntry)
                    courseNo = courseNo + 1
            return menu



class MatildaMenu (Menu):
    provider = "menu.matildaplatform.com"

    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
            ):
        
        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36"}


    def _fixUrl(self, url: str) -> str:
        return url

    async def _getWeek(self, aiohttp_session, url):
        async with aiohttp_session.get(url, headers=self.headers, raise_for_status=True) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            jsonData = soup.select("#__NEXT_DATA__")[0].string
            return json.loads(jsonData)["props"]["pageProps"]

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        return self._createMenuEntry (order, raw_entry["mealName"], raw_entry["name"], raw_entry["optionName"])
    
    async def _loadMenu(self, aiohttp_session):

        w1 = await self._getWeek(aiohttp_session, self.url)
        w2 = await self._getWeek(aiohttp_session, "https://menu.matildaplatform.com" + w1["nextURL"])

        mealEntries = [*w1["meals"], *w2["meals"]]

        self._dumpData(mealEntries)

        menu:MenuData = {}

        mealNo = 1
        lastDate = None

        for meal in mealEntries:
            
            entryDate = datetime.strptime(meal["date"], "%Y-%m-%dT%H:%M:%S").date() # 2023-06-02T00:00:00

            if lastDate and lastDate != entryDate:
                mealNo = 1
            lastDate = entryDate

            name = meal["name"] if meal["name"] is not None else f"Måltid {mealNo}"
            mealNo += 1
            courseNo = 1

            for course in meal["courses"]:
                # add the meal name to each course
                course["mealName"] = name
                menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                self._addMenuEntry(menu, entryDate, menuEntry)
                courseNo += 1

        return menu


# Beeing absorbed by matildaplatform it seems, but still same format, just domain change
# mpi.mashie.com (migrating to mpi.mashie.matildaplatform.com)
# sodex.mashie.com (migrating to sodex.mashie.matildaplatform.com)
class MashieMenu(Menu):

    provider = "mashie"

    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
        ):
        
        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self._NO_MENU_MESSAGE = "ingen matsedel"
        # important to set user-agent, otherwise site does not return the json data
        self.headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36",
                        "cookie": "cookieLanguage=sv-SE"} # set page lang to Swe
 
    def _fixUrl(self, url:str) -> str:
        # observed variants:
        #   mpi.mashie.com/public/app/Laholms%20kommun/a326a379
        #   sodexo.mashie.com/public/app/Akademikrogen%20skolor/d47bc6bf
        #
        #  all subdomains seem to have a corresponding ../menu/.. url to the ../app/..
        #  the ../menu/.. page contains json data for the menu, so use that instead of scraping the page

        if "/app/" in url:
            url = url.replace("/app/", "/menu/")

        # mashie.com => mashie.matildaplatform.com
        if "mashie.com" in url:
            url = url.replace("mashie.com", "mashie.matildaplatform.com")

        return url

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        return self._createMenuEntry (order=order, 
                                      meal_raw=raw_entry["MenuAlternativeName"],
                                      dish_raw=raw_entry["DayMenuName"],
                                      label=None)

    async def _loadMenu(self, aiohttp_session):

        def preserveTs(m):
            return re.sub(r"\D", "", m.group(0))

        se = await self.asyncExecutor(tz.gettz, "Europe/Stockholm")

        async with aiohttp_session.get(self.url, headers=self.headers, raise_for_status=True) as response:
            html = await response.text()

        soup = BeautifulSoup(html, 'html.parser')
        scriptTag = soup.select_one("script")
        if scriptTag is None:

            if soup.find("h2", string=lambda s: s and self._NO_MENU_MESSAGE in s.lower()):
                log.info("No menu available (holiday/weekend) for %s", self.url)
                return

            raise ValueError("Malformatted/unexpected data")
        
        jsonData = scriptTag.string
        # discard javascript variable assignment, weekMenues = {...
        jsonData = jsonData[jsonData.find("{") - 1:]
        # replace javascipt dates (new Date(1234567...) with only the ts
        jsonData = re.sub(r"new Date\([0-9]+\)", preserveTs, jsonData)
        # json should be fine now
        data = json.loads(jsonData)

        self._dumpData(data)

        menu:MenuData = {}

        for week in data["Weeks"][:2]: # [:2] slice two weeks
            for day in week["Days"]:
                entryDate = datetime.fromtimestamp(day["DayMenuDate"] / 1000, timezone.utc)
                entryDate = entryDate.astimezone(tz=se).date()

                courseNo = 1
                for course in day["DayMenus"]:

                    menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                    self._addMenuEntry(menu, entryDate, menuEntry)
                    courseNo += 1

        return menu


class SkolmatInfoMenu(Menu):

    provider = "meny.skolmat.info"

    def __init__(self,
                 asyncExecutor, url:str,
                 customMenuEntryProcessorCB: Callable | None = None,
                 readableDaySummaryCB: Callable | None = None
            ):

        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self.headers = {
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/99.0.4844.82 Safari/537.36"
            ),
        }

    def _fixUrl(self, url: str) -> str:
        url = url.strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)
        if not parsed.netloc or self.provider not in parsed.netloc:
            raise ValueError("Skolmat.info URL must target meny.skolmat.info")

        if not parsed.path:
            raise ValueError("school path could not be extracted from url")

        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        return self._createMenuEntry(
            order=order,
            meal_raw="Lunch",
            dish_raw=raw_entry.get("dish", ""),
            label=raw_entry.get("label"),
        )

    async def _getWeek(self, aiohttp_session, year:int, week:int) -> str:
        url = f"{self.url}?year={year}&week={week}"
        async with aiohttp_session.get(url, headers=self.headers, raise_for_status=True) as response:
            return await response.text()

    def _parseWeekHtml(self, html_data: str) -> MenuData:
        soup = BeautifulSoup(html_data, "html.parser")
        menu:MenuData = {}

        for time_tag in soup.find_all("time", attrs={"datetime": True}):
            try:
                entryDate = parser.isoparse(time_tag["datetime"]).date()
            except Exception:
                continue

            day_info = time_tag.find_parent("div")
            day_block = day_info.parent if day_info and day_info.parent else None
            if not day_block:
                continue

            course_group = day_info.find_next_sibling("div")
            if not course_group:
                continue

            courseNo = 1
            for course in course_group.find_all("div", class_="space-y-2", recursive=False):
                prose = course.find("div", class_=lambda c: c and "prose" in c)
                dish = prose.get_text(" ", strip=True) if prose else ""

                labels = []
                for label_node in course.find_all("span", class_=lambda c: c and "text-sm" in c):
                    value = normalizeString(label_node.get_text(" ", strip=True))
                    if value and value not in labels:
                        labels.append(value)

                raw_entry = {
                    "dish": dish,
                    "label": ", ".join(labels) if labels else None,
                }

                menuEntry = self._processMenuEntry(entryDate, courseNo, raw_entry)
                self._addMenuEntry(menu, entryDate, menuEntry)
                courseNo += 1

        return menu

    async def _loadMenu(self, aiohttp_session) -> MenuData:
        weekOffset = 0 if date.today().weekday() < 5 else 1
        menu:MenuData = {}

        for offset in range(self._weeks):
            week_data = self._getWeekNumber(weekOffset + offset)
            html_data = await self._getWeek(aiohttp_session, year=week_data[0], week=week_data[1])
            parsed_week = self._parseWeekHtml(html_data)
            for isodate, entries in parsed_week.items():
                menu.setdefault(isodate, []).extend(entries)

        return menu



class MenuGoMenu(Menu):

    provider = "menugo.se"

    def __init__(self, 
                 asyncExecutor, url:str, 
                 customMenuEntryProcessorCB: Callable | None = None, 
                 readableDaySummaryCB: Callable | None = None
            ):

        super().__init__(asyncExecutor, url, customMenuEntryProcessorCB, readableDaySummaryCB)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json", 
            "Referer": f"https://{self.provider}/",
            }

    def _fixUrl(self, url: str) -> str:

        # https://menugo.se/m/0127/Bjorkstugan ->
        # https://menugo.se/FetchTheMenu/{"Kommunkod":"0127","LänkNamn":"Bjorkstugan"} ->
        # https://menugo.se/FetchTheMenu/%7B%22Kommunkod%22%3A%220127%22%2C%22L%C3%A4nkNamn%22%3A%22Kungstappan%22%7D

        parsed = urlparse(url.strip())
        parts = parsed.path.strip("/").split("/")

        # Expected: ["m", "0127", "Bjorkstugan"]
        if len(parts) < 3 or parts[0] != "m":
            raise ValueError(f"Unexpected Menugo URL format: {parsed.path}")

        uri = {
            "Kommunkod": parts[1],
            "LänkNamn": parts[2]
        }
        encoded = quote(json.dumps(uri, ensure_ascii=False), safe="")
        url = f"https://menugo.se/FetchTheMenu/{encoded}"

        return url
    

    async def _fetchMenu (self, aiohttp_session):

        # no date/range arguments in the uri, seems to return a fixed range of weeks, so just fetch and parse
        async with aiohttp_session.get(self.url, headers=self.headers, raise_for_status=True) as response:
            html = await response.text()
            data = json.loads(html)
            return data["CacheObjekt"]

    def _processMenuEntry(self, entryDate, order:int, raw_entry:Any) -> MenuEntry:
        if entry := super()._processMenuEntry(entryDate, order, raw_entry):
            return entry

        label = None
        if raw_entry["Matgrupp"]:
            label = ", ".join(raw_entry["Matgrupp"])

        dish = raw_entry["Namn"].strip()

        if dish == "Meny saknad för denna dag.":
            return None

        meal = None
        if dish.lower().startswith("lunch:"):
            meal = "Lunch"
            dish = dish[len(meal) + 1:].lstrip()
        elif dish.lower().startswith("middag:"):
            meal = "Middag"
            dish = dish[len(meal) + 1:].lstrip()

        return self._createMenuEntry (order, meal, dish, label)

    async def _loadMenu(self, aiohttp_session) -> MenuData:

        today = date.today()
        firstDay = today - timedelta(days=today.weekday())
        if today.weekday() >= 5:
           firstDay += timedelta(days=7)

        endDate = firstDay + timedelta(days=14) 

        data = await self._fetchMenu(aiohttp_session)
        dayEntries = data.get("DatumObjekt", [])

        self._dumpData(dayEntries)
        menu:MenuData = {}

        for day in dayEntries:
            entryDate = parser.isoparse(day["Datum"]).date()
            if entryDate > endDate:
                break

            courseNo = 1
            for course in day["Maträtt"]:
                menuEntry = self._processMenuEntry (entryDate, courseNo, course)
                if menuEntry:
                    self._addMenuEntry(menu, entryDate, menuEntry)
                    courseNo = courseNo + 1
        
        return menu

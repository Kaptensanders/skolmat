import asyncio

from menu import SkolmatInfoMenu


FACILITY_URL = (
    "https://www.skolmat.info/matsedlar"
    "?countyCode=12&municipalityId=1280&facilityId=cmruebdqn000804jsdd2oi356"
)
API_URL = "https://www.skolmat.info/api/public/matsedlar/cmruebdqn000804jsdd2oi356"
LEGACY_URL = "https://meny.skolmat.info/blekinge/karlskrona/asposkolan"


SAMPLE_WEEK = {
    "ok": True,
    "facility": {"id": "cmruebdqn000804jsdd2oi356", "name": "Dammfriskolan"},
    "week": {
        "year": 2026,
        "weekNumber": 6,
        "days": {
            "MONDAY": {
                "isOpen": True,
                "rows": [
                    {"text": "Spaghetti Baljonese serveras med ketchup", "allergens": ["VEGETARIAN"]},
                    {"text": "Spaghetti Bolognese serveras med ketchup", "allergens": ["NÖTKÖTT", "GRISKÖTT"]},
                ],
            },
            "TUESDAY": {
                "isOpen": True,
                "rows": [
                    {"text": "Fiskburgare med bröd, klyftpotatis och örtaioli", "allergens": ["FISK"]},
                    {"text": "", "allergens": []},
                ],
            },
            "SATURDAY": {"isOpen": False, "rows": []},
        },
    },
}

FACILITY_LIST = {
    "ok": True,
    "counties": [
        {
            "code": "10",
            "name": "Blekinge",
            "municipalities": [
                {
                    "id": "1081",
                    "name": "Karlskrona",
                    "groups": [],
                    "facilities": [
                        {"id": "0C9C3377-66D8-4CCD-85D4-46E87D5F3CA2", "name": "Aspöskolan"},
                    ],
                }
            ],
        }
    ],
}


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    async def json(self, content_type=None):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class _FakeSession:
    """Returns a canned payload per requested url and records the calls."""

    def __init__(self, payloads):
        self._payloads = payloads
        self.requests = []

    def get(self, url, headers=None, raise_for_status=False):
        self.requests.append(url)
        for prefix, payload in self._payloads.items():
            if url.startswith(prefix):
                return _FakeResponse(payload)
        raise AssertionError(f"unexpected url: {url}")


def test_skolmatinfo_fix_url_variants():
    assert SkolmatInfoMenu(asyncExecutor=None, url=FACILITY_URL).url == API_URL
    assert SkolmatInfoMenu(asyncExecutor=None, url=API_URL).url == API_URL

    legacy = SkolmatInfoMenu(asyncExecutor=None, url=LEGACY_URL)
    assert legacy._legacyName == "asposkolan"


def test_skolmatinfo_parse_week():
    menu = SkolmatInfoMenu(asyncExecutor=None, url=FACILITY_URL)

    parsed = menu._parseWeek(SAMPLE_WEEK)

    # 2026 week 6 starts on a Monday, Feb 2. Closed days are skipped.
    assert sorted(parsed.keys()) == ["2026-02-02", "2026-02-03"]

    day1 = parsed["2026-02-02"]
    assert len(day1) == 2
    assert day1[0]["meal"] == "Lunch"
    assert day1[0]["dish"] == "Spaghetti Baljonese serveras med ketchup"
    assert day1[0]["label"] == "Vegetarian"
    assert day1[0]["order"] == 1
    assert day1[1]["label"] == "Nötkött, Griskött"
    assert day1[1]["order"] == 2

    day2 = parsed["2026-02-03"]
    assert len(day2) == 1
    assert day2[0]["dish"] == "Fiskburgare med bröd, klyftpotatis och örtaioli"
    assert day2[0]["label"] == "Fisk"


def test_skolmatinfo_resolves_legacy_url():
    menu = SkolmatInfoMenu(asyncExecutor=None, url=LEGACY_URL)
    session = _FakeSession({
        "https://www.skolmat.info/api/public/matsedlar/0C9C3377": SAMPLE_WEEK,
        "https://www.skolmat.info/api/public/matsedlar": FACILITY_LIST,
    })

    asyncio.run(menu._resolveLegacyName(session))

    assert menu.url == "https://www.skolmat.info/api/public/matsedlar/0C9C3377-66D8-4CCD-85D4-46E87D5F3CA2"
    assert menu._legacyName is None


def test_skolmatinfo_unknown_legacy_name_raises():
    menu = SkolmatInfoMenu(asyncExecutor=None, url="https://meny.skolmat.info/blekinge/karlskrona/finns-inte")
    session = _FakeSession({"https://www.skolmat.info/api/public/matsedlar": FACILITY_LIST})

    try:
        asyncio.run(menu._resolveLegacyName(session))
    except ValueError as err:
        assert "finns-inte" in str(err)
    else:
        raise AssertionError("expected ValueError for an unknown school name")

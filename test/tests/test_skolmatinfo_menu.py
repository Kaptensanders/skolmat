import pytest

from menu import SkolmatInfoMenu


PUBLIC_URL = (
    "https://www.skolmat.info/matsedlar?countyCode=10&municipalityId=1081"
    "&facilityId=63C603F7-53F6-4E8C-B84B-6118D0B595F7"
)

SAMPLE_DATA = {
    "ok": True,
    "facility": {
        "id": "63C603F7-53F6-4E8C-B84B-6118D0B595F7",
        "name": "Lyckeby Kunskapscenter",
        "municipalityId": "1081",
        "municipalityName": "Karlskrona",
        "countyCode": "10",
        "countyName": "Blekinge",
    },
    "week": {
        "year": 2026,
        "weekNumber": 35,
        "freeText": "Med reservation för ändringar i matsedeln",
        "freeTextPosition": "TOP",
        "days": {
            "MONDAY": {
                "isOpen": True,
                "rows": [
                    {
                        "id": "17577b05-7b3d-4098-9e62-00b1a82c4c43",
                        "text": "Pasta med spenat och ostsås",
                        "allergens": ["VEGETARIAN"],
                    },
                    {
                        "id": "53f8118a-f127-4c03-a042-12d68bddf86a",
                        "text": "Pasta serveras med ost & skinksås ",
                        "allergens": ["PORK"],
                    },
                ],
            },
            "TUESDAY": {
                "isOpen": True,
                "rows": [
                    {
                        "id": "0522742c-b838-43c5-b8b1-c191f809f6b4",
                        "text": "Krämig örtbakad fisk serveras med kokt potatis ",
                        "allergens": ["FISH"],
                    }
                ],
            },
            "SATURDAY": {
                "isOpen": False,
                "rows": [
                    {
                        "id": "b2624295-20fb-4394-b8b3-ae602a2fbab6",
                        "text": "",
                        "allergens": [],
                    }
                ],
            },
        },
        "persisted": True,
        "updatedAt": "2026-08-25T05:42:59.865Z",
    },
}


def test_skolmatinfo_rewrites_public_url_to_api_url():
    menu = SkolmatInfoMenu(asyncExecutor=None, url=PUBLIC_URL)

    assert menu.url == (
        "https://www.skolmat.info/api/public/matsedlar/"
        "63C603F7-53F6-4E8C-B84B-6118D0B595F7"
    )


def test_skolmatinfo_rejects_url_without_facility_id():
    with pytest.raises(ValueError, match="Invalid URL, expected format"):
        SkolmatInfoMenu(
            asyncExecutor=None,
            url="https://www.skolmat.info/matsedlar?countyCode=10",
        )


def test_skolmatinfo_parse_week_data():
    menu = SkolmatInfoMenu(asyncExecutor=None, url=PUBLIC_URL)

    parsed = menu._parseWeekData(SAMPLE_DATA)

    assert sorted(parsed.keys()) == ["2026-08-24", "2026-08-25"]

    monday = parsed["2026-08-24"]
    assert monday == [
        {
            "meal": "Lunch",
            "dish": "Pasta med spenat och ostsås",
            "label": None,
            "order": 1,
        },
        {
            "meal": "Lunch",
            "dish": "Pasta serveras med ost & skinksås",
            "label": None,
            "order": 2,
        },
    ]

    tuesday = parsed["2026-08-25"]
    assert tuesday == [
        {
            "meal": "Lunch",
            "dish": "Krämig örtbakad fisk serveras med kokt potatis",
            "label": None,
            "order": 1,
        }
    ]

from menu import SkolmatInfoMenu


SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="sv-se">
<body>
<main class="grow">
    <div class="container px-content py-12">
        <div class="space-y-10">
            <div class="flex items-start gap-x-4 sm:gap-x-8">
                <div class="w-28 sm:w-36 shrink-0">
                    <time datetime="2026-02-02">2026-02-02</time>
                </div>
                <div class="space-y-3">
                    <div class="space-y-2">
                        <div class="prose max-w-none">
                            <p>Spaghetti Baljonese serveras med ketchup</p>
                        </div>
                        <div class="flex flex-wrap items-center gap-3 mt-2">
                            <span class="text-sm text-neutral-700">Vegetariskt</span>
                        </div>
                    </div>
                    <div class="space-y-2">
                        <div class="prose max-w-none">
                            <p>Speghetti Bolognese serveras med ketchup</p>
                        </div>
                        <div class="flex flex-wrap items-center gap-3 mt-2">
                            <span class="text-sm text-neutral-700">Nötkött</span>
                            <span class="text-sm text-neutral-700">Griskött</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="flex items-start gap-x-4 sm:gap-x-8">
                <div class="w-28 sm:w-36 shrink-0">
                    <time datetime="2026-02-03">2026-02-03</time>
                </div>
                <div class="space-y-3">
                    <div class="space-y-2">
                        <div class="prose max-w-none">
                            <p>Fiskburgare med bröd, klyftpotatis och örtaioli</p>
                        </div>
                        <div class="flex flex-wrap items-center gap-3 mt-2">
                            <span class="text-sm text-neutral-700">Fisk</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</main>
</body>
</html>
"""


def test_skolmatinfo_parse_week_html():
    menu = SkolmatInfoMenu(asyncExecutor=None, url="https://meny.skolmat.info/blekinge/karlskrona/lyckeby-kunskapscenter")

    parsed = menu._parseWeekHtml(SAMPLE_HTML)

    assert sorted(parsed.keys()) == ["2026-02-02", "2026-02-03"]

    day1 = parsed["2026-02-02"]
    assert len(day1) == 2
    assert day1[0]["meal"] == "Lunch"
    assert day1[0]["dish"] == "Spaghetti Baljonese serveras med ketchup"
    assert day1[0]["label"] == "Vegetariskt"
    assert day1[0]["order"] == 1
    assert day1[1]["label"] == "Nötkött, Griskött"
    assert day1[1]["order"] == 2

    day2 = parsed["2026-02-03"]
    assert len(day2) == 1
    assert day2[0]["meal"] == "Lunch"
    assert day2[0]["dish"] == "Fiskburgare med bröd, klyftpotatis och örtaioli"
    assert day2[0]["label"] == "Fisk"

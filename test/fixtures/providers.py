
# processors
from processors.skutehagens_skola import entryProcessor as skolmaten1bProcessor
from processors.karlskoga_aldreomsorg import entryProcessor as matilda5bProcessor
from processors.arhem_aldreboende import entryProcessor as mashie3bProcessor

PROVIDERS = {
    "foodit":       {"name": "Blåsut/Dalen förskolor",  "url": "https://webmenu.foodit.se/?r=1&m=180&p=1035&c=10228&w=0&v=Week&l=undefined", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten0":   {"name": "Skolmaten broken URL",    "url": "https://skolmaten.se/skutehagens-sk", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},    
    "skolmaten1":   {"name": "Skutehagsskolan",         "url": "https://skolmaten.se/skutehagens-skolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten2":   {"name": "Påskbergsskolan", "url": "https://skolmaten.se/paskbergsskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten3":   {"name": "Klarebergsskolan 4-6, 7-9", "url": "https://skolmaten.se/klarebergsskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten4":   {"name": "Stenbockskolan", "url": "https://skolmaten.se/stenbockskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "skolmaten5":   {"name": "Hålta förskola", "url": "https://skolmaten.se/halta-forskola", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo1":       {"name": "Bosgårdsskolan", "url": "https://meny.mateo.se/molndal/66", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo2":       {"name": "Stallbackens förskola", "url": "https://meny.mateo.se/molndal/29", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mateo3":       {"name": "Emyhills förskola", "url": "https://meny.mateo.se/kavlinge-utbildning/88", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda1":     {"name": "Skutskär skola", "url": "https://menu.matildaplatform.com/meals/week/63fc6e2dccb95f5ce56d8ada_skolor", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda2":     {"name": "Parkskolan restaurang", "url": "https://menu.matildaplatform.com/meals/week/63fc8f84ccb95f5ce570a0d4_parkskolan-restaurang", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda3":     {"name": "Dalajärs förskola", "url": "https://menu.matildaplatform.com/meals/week/6682a34d6337e8ced9340214_dalajars-forskola", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda4":     {"name": "Kramfors Äldreboenden", "url": "https://menu.matildaplatform.com/meals/week/682308b1e431ee42ec97f4c3_aldreboenden", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda5":     {"name": "Karlskoga Äldreomsorg", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "matilda5b":    {"name": "Karlskoga Äldreomsorg", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": matilda5bProcessor, "readableDaySummaryCB": None},
    "mashie1":      {"name": "Ekhaga", "url": "https://mpi.mashie.com/public/app/Bjuvs%20kommun/c19fee26", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie2":      {"name": "Ekhaga", "url": "https://mpi.mashie.matildaplatform.com/public/app/Bjuvs%20kommun/c19fee26", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie3":      {"name": "Arhem äldreboende", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie3b":     {"name": "Arhem äldreboende", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": mashie3bProcessor, "readableDaySummaryCB": None},
    "mashie4":      {"name": "Brinkskolan", "url": "https://sodexo.mashie.com/public/menu/T%C3%A4by%20skolor%20Norr/5678b8c3", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
    "mashie4b":     {"name": "Brinkskolan", "url": "https://sodexo.mashie.matildaplatform.com/public/menu/T%C3%A4by%20skolor%20Norr/5678b8c3", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None}
}


# ha bootstrap standard set

# PROVIDERS = {
#     "foodit":       {"name": "foodit - Blåsut/Dalen förskolor",  "url": "https://webmenu.foodit.se/?r=1&m=180&p=1035&c=10228&w=0&v=Week&l=undefined", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "skolmaten1":   {"name": "skolmaten - Skutehagsskolan", "url": "https://skolmaten.se/skutehagens-skolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "skolmaten2":   {"name": "skolmaten - Påskbergsskolan", "url": "https://skolmaten.se/paskbergsskolan", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "skolmaten5":   {"name": "skolmaten - Hålta förskola", "url": "https://skolmaten.se/halta-forskola", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "mateo1":       {"name": "mateo - Bosgårdsskolan", "url": "https://meny.mateo.se/molndal/66", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "mateo2":       {"name": "mateo- Stallbackens förskola", "url": "https://meny.mateo.se/molndal/29", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "matilda1":     {"name": "matilda - Skutskär skola", "url": "https://menu.matildaplatform.com/meals/week/63fc6e2dccb95f5ce56d8ada_skolor", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "matilda4":     {"name": "matilda - Kramfors Äldreboenden", "url": "https://menu.matildaplatform.com/meals/week/682308b1e431ee42ec97f4c3_aldreboenden", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "matilda5":     {"name": "matilda - Karlskoga Äldreomsorg - Org", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "matilda5b":    {"name": "matilda - Karlskoga Äldreomsorg - Processed", "url": "https://menu.matildaplatform.com/meals/week/67b816e201a159adbb065685_aldreomsorg-matsedel", "customMenuEntryProcessorCB": matilda5bProcessor, "readableDaySummaryCB": None},
#     "mashie3":      {"name": "mashie - Arhem äldreboende - Org", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None},
#     "mashie3b":     {"name": "mashie - Arhem äldreboende - Processed", "url": "https://mpi.mashie.com/public/app/Sigtuna%20Kommun/c32fae7a", "customMenuEntryProcessorCB": mashie3bProcessor, "readableDaySummaryCB": None},
#     "mashie4b":     {"name": "mashie - Brinkskolan", "url": "https://sodexo.mashie.matildaplatform.com/public/menu/T%C3%A4by%20skolor%20Norr/5678b8c3", "customMenuEntryProcessorCB": None, "readableDaySummaryCB": None}
# }





![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=)
![Version](https://img.shields.io/github/v/release/Kaptensanders/skolmat-card)
![Installs](https://img.shields.io/badge/dynamic/json?label=Installs&logo=home-assistant&query=%24.skolmat.total&url=https%3A%2F%2Fanalytics.home-assistant.io%2Fcustom_integrations.json)

# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools

## Description
This component is only valid in Sweden. It leverages data from skolmaten.se, webmenu.foodit.se or menu.matildaplatform.com to create a sensor entity from a configured data source (url).
The sensor state will be todays available course(es) and the attributes will contain the full menu for the next two weeks.

You can use the sensor as you please or install the lovelace custom card to display the menu for today or for the week (https://github.com/Kaptensanders/skolmat-card)

![image](https://user-images.githubusercontent.com/24979195/154963878-013bb9c0-80df-4449-9a8e-dc54ef0a3271.png)

## Installation
1. Install with HACS
2. Add to configuration.yaml:
```yaml
sensor:
  - platform: skolmat
    name: Skutehagen # Name of school here
    url: "https://skolmaten.se/skutehagens-skolan/rss/weeks" # url to your rss here
```
4. Validate config and restart HA
5. Your sensor entity will show up as skolmat.[school name]
3. Optionally, also with HACS, install the corresponding lovelace card: skolmat-card 

## Find the menu url

#### skolmaten.se ####
  1. Open https://skolmaten.se/ and follow the links to find your school.
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://skolmaten.se/skutehagens-skolan/`

#### webmenu.foodit.se ####
  1. Open https://webmenu.foodit.se/ and follow the links to find your school.
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://webmenu.foodit.se/?r=6&m=617&p=883&c=10023&w=0&v=Week&l=undefined`

#### menu.matildaplatform.com ####
  1. Open https://menu.matildaplatform.com/ and find your school by using the search box
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://menu.matildaplatform.com/meals/week/63fc93fcccb95f5ce5711276_indianberget`

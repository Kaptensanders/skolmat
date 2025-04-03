![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=)
![Version](https://img.shields.io/github/v/release/Kaptensanders/skolmat)

<h3 style="color:red; font-weight:bold;">Note: skolmaten.se has updated their url's and api, please update your config accordingly and upgrade to latest version:</h3>


# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools

## Description
This component is only valid in Sweden. It leverages data from skolmaten.se, webmenu.foodit.se, menu.matildaplatform.com or mpi.mashie.com to create a sensor entity from a configured data source (url).
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
    url: "https://myprovider.se/myschoolname" # url to your school page, see below
    unique_id: "my_skolmat_sensor" # Optional, better for managing entities, but will change the entity type.
```
4. Validate config and restart HA
5. Your sensor entity will show up as skolmat.[school name]
3. Optionally, also with HACS, install the corresponding lovelace card: skolmat-card 

## Find the menu url

#### skolmaten.se ####
  1. Open https://skolmaten.se/ and follow the links to find your school.
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://skolmaten.se/skutehagens-skolan`

#### webmenu.foodit.se ####
  1. Open https://webmenu.foodit.se/ and follow the links to find your school.
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://webmenu.foodit.se/?r=6&m=617&p=883&c=10023&w=0&v=Week&l=undefined`

#### menu.matildaplatform.com ####
  1. Open https://menu.matildaplatform.com/ and find your school by using the search box
  2. When you arrive at the page with this weeks menu, copy the url\
    Like: `https://menu.matildaplatform.com/meals/week/63fc93fcccb95f5ce5711276_indianberget`

#### mashie.com ####
  NOTE: mashie.com has different subdomains like mpi, sodexo, and possibly more. Example below is for mpi.mashie.com and you may have another way of obtaining the url depending on your subdomain.
  If the url to your weekly menu contains .../public/app/... or .../public/app/... you should be fine. Otherwise let me know.

  1. Open https://mpi.mashie.com/public/app and find your school by using the search box
  2. When you arrive at the page where you can see the menu, copy the url\
    Like: `https://mpi.mashie.com/public/app/Laholms%20kommun/a326a379`

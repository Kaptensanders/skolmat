# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools

## Description
This component is only valid in Sweden. It creates a sensor entity from a configured rss feed from https://skolmaten.se/. 
The sensor state will be todays available course(es) and the attributes will contain the full menu for the next two weeks.

You can use the sensor as you please or install the lovelace custom card to display the menu for today or for the week (https://github.com/Kaptensanders/skolmat-card)

![image](https://user-images.githubusercontent.com/24979195/154963878-013bb9c0-80df-4449-9a8e-dc54ef0a3271.png)

## Dev status
This component was developed and tested with HA Core 2021.12.10. Except for bugs there may be corner cases with the rss feed data not discovered and handled yet. Such as, what happens when the schools are closed for summer etc.

## Installation
1. Put the contents of the repo in `.../<ha config>/custom_components/skolmat/` (or clone this repo to your custom_components folder)
2. Restart HA
3. Add to configuration.yaml:
```yaml
sensor:
  - platform: skolmat
    name: Skutehagen # Name of school here
    rss: "https://skolmaten.se/skutehagens-skolan/rss/weeks" # your rss here
    format: first # Course to show as sensor state. first, second or both (will be separated with |)
```
4. Validate config and restart HA
5. Your sensor entity will show up as skolmat.[school name]
6. Check out the https://github.com/Kaptensanders/skolmat-card if you want the lovelace menu card

### Find the rss feed
1. Go to https://skolmaten.se/ and follow the links to find your school.
2. When you arrive at the page where you can see the menu, click the RSS link at the end and choose the link for the current **week**.
  Like: `https://skolmaten.se/skutehagens-skolan/rss/weeks` (shold end with `/rss/weeks`)
  
## TODO:
* HACS installation 

  

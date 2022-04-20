# skolmat custom component for Home Assistant
Skolmat custom component for the food menu in Swedish schools

## Description
This component is only valid in Sweden. It leverages data from skolmaten.se, IST AB, Andreas Egerup, to create a sensor entity from a configured rss feed.
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
    rss: "https://skolmaten.se/skutehagens-skolan/rss/weeks" # your rss here
    format: first # Course to show as sensor state. first, second or both (will be separated with |)
```
4. Validate config and restart HA
5. Your sensor entity will show up as skolmat.[school name]
3. Optionally, also with HACS, install the corresponding lovelace card: skolmat-card 

### Find the rss feed
1. Go to https://skolmaten.se/ and follow the links to find your school.
2. When you arrive at the page where you can see the menu, click the RSS link at the end and choose the link for the current **week**.
  Like: `https://skolmaten.se/skutehagens-skolan/rss/weeks` (shold end with `/rss/weeks`)
  

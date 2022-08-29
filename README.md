# telegeo

This is a python package for scraping Telegram data based on geolocation.

## Installing
```py
pip install telegeo
```

## Dependencies:
(If nothing odd happens, users will install all the following dependencies of telegeo automatically after running "pip install telegeo"):  
`pandas`  
`geopy`  
`plotly`  
`tqdm`  
`telethon`  

## How to use
`step1:` import telegeo
```py
from telegeo import telegeo
```

`step2:` generating all coordinates within the specified latitude and longitude range.  
use the map_range() fucntion in telegeo to generate the coordinates you need.

users should provide the following parameters⬇  
★**lat_max**: max latitude of the map range.  
★**lon_max**: max longitude of the map range.  
★**lat_min**: min latitude of the map range.  
★**lon_min**: min longitude of the map range.  
★**distance**: the distance between two coordinates on the map.
★**save_path**: the path and filename for saving a csv file, which records all the coordinates.  
_(see Figure 1 for the first 5 parameters)_

Example:   
Move every 500 meters to generate all coordinates covering Hong Kong.
And, save as csv.
```py
telegeo.map_range(22.560100,114.404948,22.155232,113.835564,0.5,'geo_range_hk_r500.csv')
```
`step3:` generate a interactive map for displaying and checking the coordinates on a world map.  
use the map_show() function in telegeo to create the map based on the above csv file.

```py
telegeo.map_show('geo_range_hk_r500.csv')
```
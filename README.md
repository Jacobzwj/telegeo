# telegeo

This is a python package for scraping Telegram:iphone: based on geolocation:earth_asia:.

[:loudspeaker:Check this package on PyPI](https://pypi.org/project/telegeo/)

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
telegeo.map_range(lat_max = 22.560100,
                  lon_max = 114.404948,
                  lat_min = 22.155232,
                  lon_min = 113.835564,
                  distance = 0.5,
                  save_path = 'geo_range_hk_r500.csv')
```
`step3:` generate a interactive map for displaying and checking the coordinates on a world map.  
use the map_show() function in telegeo to create the map based on the above csv file.

```py
telegeo.map_show(save_path = 'geo_range_hk_r500.csv')
```
![Figure 2](https://user-images.githubusercontent.com/60833574/187110262-5f72ae26-171d-4493-9844-e67ced0e90d7.png)

`step4:` some of the coordinates may not belong to your target city, choose a standard to filter the map
```py
telegeo.map_center(lat_max = 22.560100,
                  lon_max = 114.404948,
                  lat_min = 22.155232,
                  lon_min = 113.835564)
```
the map_center() function will return us the geo information of the center point on our map, see the following results:
```py
The centroid is →→(22.357914821609455, 114.12025600000001)
↓ Copy one standard to filter the coordinates generated from map_range() ↓ (e.g. 'state': '香港 Hong Kong') 
{'road': '荃灣路 Tsuen Wan Road', 'quarter': '葵盛圍 Kwai Shing Circuit', 'suburb': '下葵涌 Ha Kwai Chung', 'town': '葵涌 Kwai Chung', 'county': '葵青區 Kwai Tsing District', 'region': '新界 New Territories', 'state': '香港 Hong Kong', 'ISO3166-2-lvl3': 'CN-HK', 'country': '中国', 'country_code': 'cn'}
```


More tutorial: To Be Continued...

import geopy
from geopy.distance import geodesic
import plotly.express as px
from telethon import TelegramClient, sync
# sync very important
from telethon import functions, types
import pandas as pd
import os
import csv
import time
from tqdm import tqdm


def map_move(lat, lon, distance, bearing):
    origin = geopy.Point(lat, lon)
    destination = geodesic(kilometers=distance).destination(origin, bearing)
    lat, lon = destination.latitude, destination.longitude
    return (lat, lon, distance, bearing)


def map_range(lat_max, lon_max, lat_min, lon_min, distance, save_path):
    # 找到最右侧一列起始点: 向左移动500, 向下移动500
    lat_s, lon_s, distance, bearing = map_move(lat_max, lon_max, distance, 270)
    lat_s, lon_s, distance, bearing = map_move(lat_s, lon_s, distance, 180)
    # 找到最右侧一列lat终点：向上移动500
    lat_e = map_move(lat_min, lon_max, distance, 360)[0]

    # print(lat_s)
    # print(lon_s)
    # 向下生成lat_range
    lat_range = []
    while True:
        lat_range.append(lat_s)
        lat_s = map_move(lat_s, lon_s, distance, 180)[0]

        if lat_s <= lat_e:
            lat_range.append(lat_s)
            break

    # 生成最左侧一列lon终点（list）：lon_min在lat_range的所有维度上向右移500m，形成一个lon_e_list
    lon_e_range = []
    for lat in lat_range:
        lon_e = map_move(lat, lon_min, distance, 90)[1]
        lon_e_range.append(lon_e)
    # print(lon_e_range)

    # 按照lat_range循环，分别向左不停移动500m，直到退出范围边缘(long_e_range)
    for lat, lon_e in tqdm(zip(lat_range, lon_e_range), total=len(lat_range)):
        lon = lon_s
        lat_lon = {"lat": [lat], "lon": [lon]}
        while True:
            df = pd.DataFrame.from_dict(lat_lon)
            hdr = False if os.path.isfile(save_path) else True
            df.to_csv(save_path, header=hdr, index=None, mode='a', encoding='utf-8')
            lon = map_move(lat, lon, distance, 270)[1]
            lat_lon = {"lat": [lat], "lon": [lon]}
            if lon <= lon_e:
                lon = lon_s
                break


def map_show(save_path):
    geo = pd.read_csv(save_path)
    fig = px.scatter_mapbox(geo, lat="lat", lon="lon")
    fig.update_mapboxes(style='open-street-map')
    fig.show()


def api_login(api_id, api_hash):
    client = TelegramClient('telegeo_api', api_id, api_hash)
    client.start()
    return client


def near_group(client, data_path):
    date_record = pd.to_datetime("today").strftime("%Y-%m-%d_%H%M%S")
    path = 'saved_data/'
    filename = 'geo_user_group' + date_record + '.csv'
    if not os.path.exists(path):
        os.makedirs(path)

    fp = open(path + filename, 'wt', newline='', encoding='utf-8')
    writer = csv.writer(fp)
    writer.writerow(
        ('lat', 'lon', 'user_id', 'user_first_name', 'user_last_name', 'user_username', 'user_phone', 'user_bot',
         'user_bot_chat_history', 'user_bot_nochats', 'user_bot_info_version', 'user_bot_inline_geo',
         'user_bot_inline_placeholder', 'user_verified', 'user_restricted', 'user_fake', 'user_access_hash',
         'user_status', 'user_restriction_platfrom', 'user_restriction_reason', 'user_restriction_text',
         'user_lang_code',
         'channel_id', 'channel_title', 'channel_date', 'channel_creator', 'channel_username',
         'channel_gigagroup', 'channel_megagroup', 'channel_broadcast', 'channel_verified', 'channel_restricted',
         'channel_participants_count',
         'channel_access_hash', 'channel_restriction_platform1', 'channel_restriction_reason1',
         'channel_restriction_text1', 'channel_restriction_platform2', 'channel_restriction_reason2',
         'channel_restriction_text2',
         'user_info_json'))
    time.sleep(1)

    def geo_chatname(lat, lon, radius):
        result = client(functions.contacts.GetLocatedRequest(
            geo_point=types.InputGeoPoint(
                lat=lat,
                long=lon,
                accuracy_radius=radius), self_expires=42))

        users = result.users
        channels = result.chats
        user_infos = users + channels
        for user_info in user_infos:
            user_info_json = user_info.to_json()
            # the users who take part in group chats may be Users or Channels.
            if '"_": "User"' in user_info_json:
                user_id = user_info.id
                user_first_name = user_info.first_name
                user_last_name = user_info.last_name
                user_username = user_info.username
                user_phone = user_info.phone
                user_bot = user_info.bot
                user_bot_chat_history = user_info.bot_chat_history
                user_bot_nochats = user_info.bot_nochats
                user_bot_info_version = user_info.bot_info_version
                user_bot_inline_geo = user_info.bot_inline_geo
                user_bot_inline_placeholder = user_info.bot_inline_placeholder
                user_verified = user_info.verified
                user_restricted = user_info.restricted
                user_fake = user_info.fake
                user_access_hash = user_info.access_hash
                user_status = user_info.status
                try:
                    user_restriction_platfrom = user_info.restriction_reason[0].platform
                    user_restriction_reason = user_info.restriction_reason[0].reason
                    user_restriction_text = user_info.restriction_reason[0].text
                except Exception as e:
                    user_restriction_platfrom = None
                    user_restriction_reason = None
                    user_restriction_text = None
                user_lang_code = user_info.lang_code

                channel_id = None
                channel_title = None
                channel_date = None
                channel_creator = None
                channel_username = None
                channel_gigagroup = None
                channel_megagroup = None
                channel_broadcast = None
                channel_verified = None
                channel_restricted = None
                channel_participants_count = None
                channel_access_hash = None
                channel_restriction_platform1 = None
                channel_restriction_reason1 = None
                channel_restriction_text1 = None
                channel_restriction_platform2 = None
                channel_restriction_reason2 = None
                channel_restriction_text2 = None


            elif '"_": "Channel"' in user_info_json:
                user_id = None
                user_first_name = None
                user_last_name = None
                user_username = None
                user_phone = None
                user_bot = None
                user_bot_chat_history = None
                user_bot_nochats = None
                user_bot_info_version = None
                user_bot_inline_geo = None
                user_bot_inline_placeholder = None
                user_verified = None
                user_restricted = None
                user_fake = None
                user_access_hash = None
                user_status = None
                user_restriction_platfrom = None
                user_restriction_reason = None
                user_restriction_text = None
                user_lang_code = None

                channel_id = user_info.id
                channel_title = user_info.title
                channel_date = user_info.date
                channel_creator = user_info.creator
                channel_username = user_info.username
                channel_gigagroup = user_info.gigagroup
                channel_megagroup = user_info.megagroup
                channel_broadcast = user_info.broadcast
                channel_verified = user_info.verified
                channel_restricted = user_info.restricted
                channel_participants_count = user_info.participants_count
                channel_access_hash = user_info.access_hash
                try:
                    channel_restriction_platform1 = user_info.restriction_reason[0].platform
                    channel_restriction_reason1 = user_info.restriction_reason[0].reason
                    channel_restriction_text1 = user_info.restriction_reason[0].text
                    channel_restriction_platform2 = user_info.restriction_reason[1].platform
                    channel_restriction_reason2 = user_info.restriction_reason[1].reason
                    channel_restriction_text2 = user_info.restriction_reason[1].text
                except Exception as e:
                    channel_restriction_platform1 = None
                    channel_restriction_reason1 = None
                    channel_restriction_text1 = None
                    channel_restriction_platform2 = None
                    channel_restriction_reason2 = None
                    channel_restriction_text2 = None

            writer.writerow((lat, lon, user_id, user_first_name, user_last_name, user_username, user_phone, user_bot,
                             user_bot_chat_history, user_bot_nochats, user_bot_info_version, user_bot_inline_geo,
                             user_bot_inline_placeholder, user_verified, user_restricted, user_fake, user_access_hash,
                             user_status, user_restriction_platfrom, user_restriction_reason, user_restriction_text,
                             user_lang_code,
                             channel_id, channel_title, channel_date, channel_creator, channel_username,
                             channel_gigagroup,
                             channel_megagroup, channel_broadcast, channel_verified, channel_restricted,
                             channel_participants_count,
                             channel_access_hash, channel_restriction_platform1, channel_restriction_reason1,
                             channel_restriction_text1, channel_restriction_platform2, channel_restriction_reason2,
                             channel_restriction_text2,
                             user_info_json))

    ###############setting: group_list for scraping+query for search##############

    # ave_path=telegeo.map_range(22.560100,114.404948,22.155232,113.835564,0.5,'geo_range_hk_r500.csv')
    geo = pd.read_csv(data_path)
    lats = geo.lat.to_list()[:10]
    lons = geo.lon.to_list()[:10]
    for lat, lon in tqdm(zip(lats, lons), total=len(lats)):
        geo_chatname(lat, lon, 500)
        time.sleep(50)

    fp.close()
    time.sleep(1)

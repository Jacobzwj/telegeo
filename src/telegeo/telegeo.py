import geopy
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import plotly.express as px
from telethon import TelegramClient, sync
# sync very important, don't delete it
from telethon import functions, types
import pandas as pd
import os
import csv
from tqdm import tqdm
from math import cos, sin, atan2, sqrt, pi, radians, degrees
from geopy.point import Point
import datetime
import time


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


def map_center(lat_max, lon_max, lat_min, lon_min):
    coordinates = [[lat_max, lon_max], [lat_max, lon_min], [lat_min, lon_max], [lat_min, lon_min]]
    x = 0
    y = 0
    z = 0
    length = len(coordinates)
    for lat, lon in coordinates:
        lon = radians(float(lon))
        lat = radians(float(lat))

        x += cos(lat) * cos(lon)
        y += cos(lat) * sin(lon)
        z += sin(lat)

    x = float(x / length)
    y = float(y / length)
    z = float(z / length)

    centroid = (degrees(atan2(z, sqrt(x * x + y * y))), degrees(atan2(y, x)))
    print("The centroid is →→" + str(centroid))
    locator = Nominatim(user_agent="check_centroid")
    centroid = str(centroid).replace("(", "").replace(")", "")
    location = locator.reverse(centroid)
    print("↓ Copy one standard to filter the coordinates generated from map_range() ↓ (e.g. 'state': '香港 Hong Kong') ")
    print(location.raw['address'])


def map_filter(data_path, target):
    df = pd.read_csv(data_path)
    # df = df[:50]
    locator = Nominatim(user_agent="map_filter")

    def reverse_geocoding(lat, lon):
        try:
            location = locator.reverse(Point(lat, lon))
            return location.raw['address']
        except Exception as e:
            print(e)
            return None

    tqdm.pandas()
    df['address'] = df.progress_apply(lambda x: reverse_geocoding(x.lat, x.lon), axis=1)
    df.to_csv(str(data_path).split(".csv")[0] + "_address.csv", index=False)
    df['address'] = df['address'].astype('str')
    df = df[df['address'].str.contains(target)]
    df.to_csv(str(data_path).split(".csv")[0] + "_filter.csv", index=False)


def api_login(api_id, api_hash, session_name):
    client = TelegramClient(session_name, api_id, api_hash)
    client.start()
    return client


def near_entity(client, data_path, sleep_seconds, move_num, start_index=0):
    date_record = pd.to_datetime("today").strftime("%Y-%m-%d_%H%M%S")
    path = 'save_near_entity/'
    filename1 = 'near_user_' + date_record + '.csv'
    filename2 = 'near_channel_' + date_record + '.csv'
    if not os.path.exists(path):
        os.makedirs(path)

    fp1 = open(path + filename1, 'wt', newline='', encoding='utf-8')
    writer1 = csv.writer(fp1)
    writer1.writerow(
        ('lat', 'lon',
         'user_id', 'user_first_name', 'user_last_name', 'user_username', 'user_phone', 'user_bot',
         'user_bot_chat_history', 'user_bot_nochats', 'user_bot_info_version', 'user_bot_inline_geo',
         'user_bot_inline_placeholder', 'user_verified', 'user_restricted', 'user_fake', 'user_access_hash',
         'user_status', 'user_restriction_platfrom', 'user_restriction_reason', 'user_restriction_text',
         'user_lang_code',
         'user_info_json'))

    fp2 = open(path + filename2, 'wt', newline='', encoding='utf-8')
    writer2 = csv.writer(fp2)
    writer2.writerow(
        ('lat', 'lon',
         'channel_id', 'channel_title', 'channel_date', 'channel_creator', 'channel_username',
         'channel_gigagroup', 'channel_megagroup', 'channel_broadcast', 'channel_verified', 'channel_restricted',
         'channel_participants_count',
         'channel_access_hash', 'channel_restriction_platform1', 'channel_restriction_reason1',
         'channel_restriction_text1', 'channel_restriction_platform2', 'channel_restriction_reason2',
         'channel_restriction_text2',
         'channel_info_json'))

    def geo_entity(lat, lon, radius):
        result = client(functions.contacts.GetLocatedRequest(
            geo_point=types.InputGeoPoint(
                lat=lat,
                long=lon,
                accuracy_radius=radius), self_expires=42))

        users = result.users
        channels = result.chats
        for user_info in users:
            user_info_json = user_info.to_json()
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
            writer1.writerow(
                (lat, lon,
                 user_id, user_first_name, user_last_name, user_username, user_phone, user_bot,
                 user_bot_chat_history, user_bot_nochats, user_bot_info_version, user_bot_inline_geo,
                 user_bot_inline_placeholder, user_verified, user_restricted, user_fake, user_access_hash,
                 user_status, user_restriction_platfrom, user_restriction_reason, user_restriction_text,
                 user_lang_code,
                 user_info_json))

        for user_info in channels:
            channel_info_json = user_info.to_json()
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

            writer2.writerow((lat, lon,
                              channel_id, channel_title, channel_date, channel_creator, channel_username,
                              channel_gigagroup,
                              channel_megagroup, channel_broadcast, channel_verified, channel_restricted,
                              channel_participants_count,
                              channel_access_hash, channel_restriction_platform1, channel_restriction_reason1,
                              channel_restriction_text1, channel_restriction_platform2, channel_restriction_reason2,
                              channel_restriction_text2,
                              channel_info_json))

    geo = pd.read_csv(data_path)
    lats = geo.lat.to_list()[start_index:move_num]
    lons = geo.lon.to_list()[start_index:move_num]
    for lat, lon in tqdm(zip(lats, lons), total=len(lats)):
        geo_entity(lat, lon, 500)
        time.sleep(sleep_seconds)

    fp1.close()
    fp2.close()


def near_entity_resume(client, data_path, data_path_user, data_path_channel, sleep_seconds, move_num):
    with open(data_path_user, 'rb') as f_u:
        for tail_u in f_u:
            pass  # locate the last line

    with open(data_path_channel, 'rb') as f_c:
        for tail_c in f_c:
            pass  # locate the last line

    lat_tail_u = float(str(tail_u).split(',')[0].split("b'")[1])
    lon_tail_u = float(str(tail_u).split(',')[1])

    lat_tail_c = float(str(tail_c).split(',')[0].split("b'")[1])
    lon_tail_c = float(str(tail_c).split(',')[1])

    if lat_tail_u <= lat_tail_c:
        lat_tail = lat_tail_u
    else:
        lat_tail = lat_tail_c

    if lon_tail_u <= lon_tail_c:
        lon_tail = lon_tail_u
    else:
        lon_tail = lon_tail_c

    geo = pd.read_csv(data_path)
    last_index = geo.loc[(geo['lat'] == lat_tail) & (geo['lon'] == lon_tail)].index[0]

    print("continue to conduct near_entity() from index " + str(last_index + 1) + " of the data_path file")
    start_index = last_index + 1
    near_entity(client, data_path, sleep_seconds, move_num=move_num + start_index, start_index=start_index)


def dedup(data_path):
    df = pd.read_csv(data_path)
    if df.columns[2] == "user_id":
        print(str(len(df)) + " users collected through near_entity(), start deduplication...")
        df = df.drop_duplicates("user_id")
        print(str(len(df)) + " users remained after deduplication.")
    elif df.columns[2] == "channel_id":
        print(str(len(df)) + " channels collected through near_entity() function, start deduplication...")
        df = df.drop_duplicates("channel_id")
        print(str(len(df)) + " channels remained after deduplication.")
    df.to_csv(str(data_path).split(".csv")[0] + "_dedup.csv", index=False)


def keywords_search_channel(client, data_path_channel, keywords, date_time, after_before, save_mode):
    if save_mode == "all":
        print("save_mode: all → save all the channels' data in one csv file")
        date_record = pd.to_datetime("today").strftime("%Y-%m-%d_%H%M%S")
        path = 'save_keywords_all/'
        filename = 'keywords_all_' + date_record + '.csv'
        if not os.path.exists(path):
            os.makedirs(path)

        fp = open(path + filename, 'wt', newline='', encoding='utf-8')
        writer = csv.writer(fp)
        writer.writerow(('group_id', 'group_title', 'group_date', 'group_creator', 'group_username', 'group_gigagroup',
                         'group_megagroup', 'group_broadcast', 'group_verified',
                         'group_restricted', 'group_participants_count', 'group_access_hash',
                         'group_restriction_platform1',
                         'group_restriction_reason1', 'group_restriction_text1',
                         'group_restriction_platform2', 'group_restriction_reason2', 'group_restriction_text2',
                         'keyword', 'chat_id', 'chat_channel_id', 'chat_date', 'chat_message', 'chat_media_id',
                         'chat_media_url', 'chat_media_title', 'chat_media_type', 'chat_media_description',
                         'chat_user_id',
                         'chat_fwd_from', 'chat_via_bot_id', 'chat_reply_to', 'chat_reply_markup',
                         'chat_entities', 'chat_views', 'chat_forwards', 'chat_replies_replies',
                         'chat_replies_replies_pts',
                         'chat_replies_comments', 'chat_replies_recent_repliers', 'chat_post_author',
                         'user_id', 'user_first_name', 'user_last_name', 'user_username', 'user_phone', 'user_bot',
                         'user_bot_chat_history', 'user_bot_nochats', 'user_bot_info_version', 'user_bot_inline_geo',
                         'user_bot_inline_placeholder', 'user_verified', 'user_restricted', 'user_fake',
                         'user_access_hash',
                         'user_status', 'user_restriction_platfrom', 'user_restriction_reason', 'user_restriction_text',
                         'user_lang_code',
                         'channel_id', 'channel_title', 'channel_date', 'channel_creator', 'channel_username',
                         'channel_gigagroup', 'channel_megagroup', 'channel_broadcast', 'channel_verified',
                         'channel_restricted', 'channel_participants_count',
                         'channel_access_hash', 'channel_restriction_platform1', 'channel_restriction_reason1',
                         'channel_restriction_text1', 'channel_restriction_platform2', 'channel_restriction_reason2',
                         'channel_restriction_text2', 'error',
                         'group_info_json', 'chat_search_json', 'user_info_json'))

        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

        if after_before == "after":
            after_before = True
        elif after_before == "before":
            after_before = False
        else:
            print("you should input either 'after' or 'before'")

        def search_in_channel(entity):
            try:
                group_info = client.get_entity(entity)
                group_info_json = group_info.to_json()

                # all the group_info data:
                group_id = group_info.id
                group_title = group_info.title
                group_date = group_info.date
                group_creator = group_info.creator
                group_username = group_info.username
                group_gigagroup = group_info.gigagroup
                group_megagroup = group_info.megagroup
                group_broadcast = group_info.broadcast
                group_verified = group_info.verified
                group_restricted = group_info.restricted
                group_participants_count = group_info.participants_count
                group_access_hash = group_info.access_hash
                try:
                    group_restriction_platform1 = group_info.restriction_reason[0].platform
                    group_restriction_reason1 = group_info.restriction_reason[0].reason
                    group_restriction_text1 = group_info.restriction_reason[0].text
                    group_restriction_platform2 = group_info.restriction_reason[1].platform
                    group_restriction_reason2 = group_info.restriction_reason[1].reason
                    group_restriction_text2 = group_info.restriction_reason[1].text
                except Exception as e:
                    group_restriction_platform1 = None
                    group_restriction_reason1 = None
                    group_restriction_text1 = None
                    group_restriction_platform2 = None
                    group_restriction_reason2 = None
                    group_restriction_text2 = None

                for q in keywords:
                    keyword = q
                    chat_search = client.iter_messages(group_id, search=q, offset_date=date_time, reverse=after_before)
                    # n = 0

                    for chat in chat_search:
                        chat_search_json = chat.to_json()
                        chat_id = chat.id

                        chat_channel_id = chat.peer_id.channel_id

                        chat_date = chat.date
                        chat_message = chat.message
                        try:
                            chat_media_id = chat.media.webpage.id
                        except Exception as e:
                            chat_media_id = None
                        try:
                            chat_media_url = chat.media.webpage.url
                        except Exception as e:
                            chat_media_url = None
                        try:
                            chat_media_title = chat.media.webpage.title
                        except Exception as e:
                            chat_media_title = None
                        try:
                            chat_media_type = chat.media.webpage.type
                        except Exception as e:
                            chat_media_type = None
                        try:
                            chat_media_description = chat.media.webpage.description
                        except Exception as e:
                            chat_media_description = None
                        try:
                            chat_user_id = chat.from_id.user_id
                        except Exception as e:
                            if chat.from_id is not None:
                                chat_user_id = chat.from_id.channel_id
                            else:
                                chat_user_id = chat_channel_id

                        chat_fwd_from = chat.fwd_from
                        chat_via_bot_id = chat.via_bot_id
                        chat_reply_to = chat.reply_to
                        chat_reply_markup = chat.reply_markup
                        chat_entities = chat.entities
                        chat_views = chat.views
                        chat_forwards = chat.forwards
                        try:
                            chat_replies_replies = chat.replies.replies
                            chat_replies_replies_pts = chat.replies.replies_pts
                            chat_replies_comments = chat.replies.comments
                            chat_replies_recent_repliers = chat.replies.recent_repliers
                        except Exception as e:
                            chat_replies_replies = None
                            chat_replies_replies_pts = None
                            chat_replies_comments = None
                            chat_replies_recent_repliers = None
                        chat_post_author = chat.post_author

                        # all the user_info data:
                        user_info = client.get_entity(chat_user_id)

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

                        error = None
                        writer.writerow(
                            (group_id, group_title, group_date, group_creator, group_username, group_gigagroup,
                             group_megagroup, group_broadcast, group_verified,
                             group_restricted, group_participants_count, group_access_hash,
                             group_restriction_platform1, group_restriction_reason1,
                             group_restriction_text1, group_restriction_platform2, group_restriction_reason2,
                             group_restriction_text2,
                             keyword, chat_id, chat_channel_id, chat_date, chat_message, chat_media_id,
                             chat_media_url, chat_media_title, chat_media_type, chat_media_description,
                             chat_user_id, chat_fwd_from, chat_via_bot_id, chat_reply_to, chat_reply_markup,
                             chat_entities, chat_views, chat_forwards, chat_replies_replies,
                             chat_replies_replies_pts, chat_replies_comments, chat_replies_recent_repliers,
                             chat_post_author,
                             user_id, user_first_name, user_last_name, user_username, user_phone, user_bot,
                             user_bot_chat_history, user_bot_nochats, user_bot_info_version,
                             user_bot_inline_geo,
                             user_bot_inline_placeholder, user_verified, user_restricted, user_fake,
                             user_access_hash, user_status, user_restriction_platfrom, user_restriction_reason,
                             user_restriction_text, user_lang_code,
                             channel_id, channel_title, channel_date, channel_creator, channel_username,
                             channel_gigagroup, channel_megagroup, channel_broadcast, channel_verified,
                             channel_restricted, channel_participants_count,
                             channel_access_hash, channel_restriction_platform1, channel_restriction_reason1,
                             channel_restriction_text1, channel_restriction_platform2,
                             channel_restriction_reason2, channel_restriction_text2, error,
                             group_info_json, chat_search_json, user_info_json))
                        # n = n + 1
                        # if (n % 1000) == 0:
                        # time.sleep(10)
                        # print("sleeping 10 seconds")

            except Exception as e:
                error = e
                group_id = entity
                writer.writerow((group_id, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                 None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                 None,
                                 None, None, None, None, None, None, None, None, None, None, None,
                                 None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                 None,
                                 None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                                 None,
                                 None, None, None, None, None, None, None, None, None, error, None, None, None))
                pass

        group_pool = pd.read_csv(data_path_channel)
        group_pool.dropna(subset=['channel_id'], inplace=True)
        group_pool.channel_id = group_pool.channel_id.astype(int)
        group_pool = group_pool.channel_id.to_list()

        for g in tqdm(group_pool):
            search_in_channel(g)
            with open(path + 'lastID_for_resume.txt', 'w') as f_resume_all:
                record = str(g) + '~ ' + data_path_channel + '~ ' + str(keywords) + '~ ' + str(date_time) + '~ ' + str(
                    after_before) + '~ ' + str(save_mode)
                f_resume_all.write(record)

        fp.close()

        print(str(len(group_pool)) + " channels have been collected!")

    elif save_mode == "channel":
        print("save_mode: channel → save each channel in one csv file")
        # date_record = pd.to_datetime("today").strftime("%Y-%m-%d_%H%M%S")
        path = 'save_keywords_channel/'
        if not os.path.exists(path):
            os.makedirs(path)

        date_time = datetime.datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')

        if after_before == "after":
            after_before = True
        elif after_before == "before":
            after_before = False
        else:
            print("you should input either 'after' or 'before'")

        def search_in_channel(entity):
            filename2 = 'channel_id_' + str(entity) + '.csv'
            fp2 = open(path + filename2, 'wt', newline='', encoding='utf-8')
            writer2 = csv.writer(fp2)
            writer2.writerow(
                ('group_id', 'group_title', 'group_date', 'group_creator', 'group_username', 'group_gigagroup',
                 'group_megagroup', 'group_broadcast', 'group_verified',
                 'group_restricted', 'group_participants_count', 'group_access_hash',
                 'group_restriction_platform1',
                 'group_restriction_reason1', 'group_restriction_text1',
                 'group_restriction_platform2', 'group_restriction_reason2', 'group_restriction_text2',
                 'keyword', 'chat_id', 'chat_channel_id', 'chat_date', 'chat_message', 'chat_media_id',
                 'chat_media_url', 'chat_media_title', 'chat_media_type', 'chat_media_description',
                 'chat_user_id',
                 'chat_fwd_from', 'chat_via_bot_id', 'chat_reply_to', 'chat_reply_markup',
                 'chat_entities', 'chat_views', 'chat_forwards', 'chat_replies_replies',
                 'chat_replies_replies_pts',
                 'chat_replies_comments', 'chat_replies_recent_repliers', 'chat_post_author',
                 'user_id', 'user_first_name', 'user_last_name', 'user_username', 'user_phone', 'user_bot',
                 'user_bot_chat_history', 'user_bot_nochats', 'user_bot_info_version', 'user_bot_inline_geo',
                 'user_bot_inline_placeholder', 'user_verified', 'user_restricted', 'user_fake',
                 'user_access_hash',
                 'user_status', 'user_restriction_platfrom', 'user_restriction_reason', 'user_restriction_text',
                 'user_lang_code',
                 'channel_id', 'channel_title', 'channel_date', 'channel_creator', 'channel_username',
                 'channel_gigagroup', 'channel_megagroup', 'channel_broadcast', 'channel_verified',
                 'channel_restricted', 'channel_participants_count',
                 'channel_access_hash', 'channel_restriction_platform1', 'channel_restriction_reason1',
                 'channel_restriction_text1', 'channel_restriction_platform2', 'channel_restriction_reason2',
                 'channel_restriction_text2', 'error',
                 'group_info_json', 'chat_search_json', 'user_info_json'))
            try:
                group_info = client.get_entity(entity)
                group_info_json = group_info.to_json()

                # all the group_info data:
                group_id = group_info.id
                group_title = group_info.title
                group_date = group_info.date
                group_creator = group_info.creator
                group_username = group_info.username
                group_gigagroup = group_info.gigagroup
                group_megagroup = group_info.megagroup
                group_broadcast = group_info.broadcast
                group_verified = group_info.verified
                group_restricted = group_info.restricted
                group_participants_count = group_info.participants_count
                group_access_hash = group_info.access_hash
                try:
                    group_restriction_platform1 = group_info.restriction_reason[0].platform
                    group_restriction_reason1 = group_info.restriction_reason[0].reason
                    group_restriction_text1 = group_info.restriction_reason[0].text
                    group_restriction_platform2 = group_info.restriction_reason[1].platform
                    group_restriction_reason2 = group_info.restriction_reason[1].reason
                    group_restriction_text2 = group_info.restriction_reason[1].text
                except Exception as e:
                    group_restriction_platform1 = None
                    group_restriction_reason1 = None
                    group_restriction_text1 = None
                    group_restriction_platform2 = None
                    group_restriction_reason2 = None
                    group_restriction_text2 = None

                for q in keywords:
                    keyword = q
                    chat_search = client.iter_messages(group_id, search=q, offset_date=date_time, reverse=after_before)
                    # n = 0

                    for chat in chat_search:
                        chat_search_json = chat.to_json()
                        chat_id = chat.id

                        chat_channel_id = chat.peer_id.channel_id

                        chat_date = chat.date
                        chat_message = chat.message
                        try:
                            chat_media_id = chat.media.webpage.id
                        except Exception as e:
                            chat_media_id = None
                        try:
                            chat_media_url = chat.media.webpage.url
                        except Exception as e:
                            chat_media_url = None
                        try:
                            chat_media_title = chat.media.webpage.title
                        except Exception as e:
                            chat_media_title = None
                        try:
                            chat_media_type = chat.media.webpage.type
                        except Exception as e:
                            chat_media_type = None
                        try:
                            chat_media_description = chat.media.webpage.description
                        except Exception as e:
                            chat_media_description = None
                        try:
                            chat_user_id = chat.from_id.user_id
                        except Exception as e:
                            if chat.from_id is not None:
                                chat_user_id = chat.from_id.channel_id
                            else:
                                chat_user_id = chat_channel_id

                        chat_fwd_from = chat.fwd_from
                        chat_via_bot_id = chat.via_bot_id
                        chat_reply_to = chat.reply_to
                        chat_reply_markup = chat.reply_markup
                        chat_entities = chat.entities
                        chat_views = chat.views
                        chat_forwards = chat.forwards
                        try:
                            chat_replies_replies = chat.replies.replies
                            chat_replies_replies_pts = chat.replies.replies_pts
                            chat_replies_comments = chat.replies.comments
                            chat_replies_recent_repliers = chat.replies.recent_repliers
                        except Exception as e:
                            chat_replies_replies = None
                            chat_replies_replies_pts = None
                            chat_replies_comments = None
                            chat_replies_recent_repliers = None
                        chat_post_author = chat.post_author

                        # all the user_info data:
                        user_info = client.get_entity(chat_user_id)

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

                        error = None
                        writer2.writerow(
                            (group_id, group_title, group_date, group_creator, group_username, group_gigagroup,
                             group_megagroup, group_broadcast, group_verified,
                             group_restricted, group_participants_count, group_access_hash,
                             group_restriction_platform1, group_restriction_reason1,
                             group_restriction_text1, group_restriction_platform2, group_restriction_reason2,
                             group_restriction_text2,
                             keyword, chat_id, chat_channel_id, chat_date, chat_message, chat_media_id,
                             chat_media_url, chat_media_title, chat_media_type, chat_media_description,
                             chat_user_id, chat_fwd_from, chat_via_bot_id, chat_reply_to, chat_reply_markup,
                             chat_entities, chat_views, chat_forwards, chat_replies_replies,
                             chat_replies_replies_pts, chat_replies_comments, chat_replies_recent_repliers,
                             chat_post_author,
                             user_id, user_first_name, user_last_name, user_username, user_phone, user_bot,
                             user_bot_chat_history, user_bot_nochats, user_bot_info_version,
                             user_bot_inline_geo,
                             user_bot_inline_placeholder, user_verified, user_restricted, user_fake,
                             user_access_hash, user_status, user_restriction_platfrom, user_restriction_reason,
                             user_restriction_text, user_lang_code,
                             channel_id, channel_title, channel_date, channel_creator, channel_username,
                             channel_gigagroup, channel_megagroup, channel_broadcast, channel_verified,
                             channel_restricted, channel_participants_count,
                             channel_access_hash, channel_restriction_platform1, channel_restriction_reason1,
                             channel_restriction_text1, channel_restriction_platform2,
                             channel_restriction_reason2, channel_restriction_text2, error,
                             group_info_json, chat_search_json, user_info_json))
                        # n = n + 1
                        # if (n % 1000) == 0:
                        # time.sleep(10)
                        # print("sleeping 10 seconds")

            except Exception as e:
                error = e
                group_id = entity
                writer2.writerow(
                    (group_id, None, None, None, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                     None,
                     None, None, None, None, None, None, None, None, None, None, None,
                     None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                     None,
                     None, None, None, None, None, None, None, None, None, None, None, None, None, None,
                     None,
                     None, None, None, None, None, None, None, None, None, error, None, None, None))
                pass

            fp2.close()

        group_pool = pd.read_csv(data_path_channel)
        group_pool.dropna(subset=['channel_id'], inplace=True)
        group_pool.channel_id = group_pool.channel_id.astype(int)
        group_pool = group_pool.channel_id.to_list()

        for g in tqdm(group_pool):
            search_in_channel(g)
            with open(path + 'lastID_for_resume.txt', 'w') as f_resume:
                record = str(g) + '~ ' + data_path_channel + '~ ' + str(keywords) + '~ ' + str(date_time) + '~ ' + str(
                    after_before) + '~ ' + str(save_mode)
                f_resume.write(record)

        print(str(len(group_pool)) + " channels have been collected!")

    else:
        print('save_mode should be "all" or "channel". Please check your input.')
        pass


def keywords_search_channel_resume(client, data_path_resume):
    date_record = pd.to_datetime("today").strftime("%Y-%m-%d_%H%M%S")
    client = client
    with open(data_path_resume) as f_resume:
        record = f_resume.readline()
        record = record.split('~ ')
        lastID = int(record[0])
        data_path_keywords = record[1]
        keywords = record[2]
        date_time = record[3]
        after_before = record[4]
        if after_before== True:
            after_before = "after"
        elif after_before == False:
            after_before = "before"
        else:
            print("resume file error due to the wrong after_before")
        save_mode = str(record[-1]).strip()

    dfo = pd.read_csv(data_path_keywords)
    var = dfo[dfo.channel_id == lastID].index[0]
    dfr = dfo.iloc[var:]
    new_file = data_path_keywords.split(".csv")[0] + "_resume_" + date_record + '.csv'
    dfr.to_csv(new_file, index=False)
    keywords = eval(keywords)
    keywords_search_channel(client=client,
                            data_path_channel=new_file,
                            keywords=keywords,
                            date_time=date_time,
                            after_before=after_before,
                            save_mode=save_mode)

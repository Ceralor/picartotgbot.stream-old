#!/usr/bin/python3
from app import app, bot, mysql
from helpers import get_mysql_cursor, mysql_fetch_assoc
from picarto_profiles import *
import requests, json

con,cur = get_mysql_cursor(mysql)
cur.execute("SELECT * FROM `users` WHERE `paused` = 0")
unpaused_users = mysql_fetch_assoc(cur)
cur.close()
con.close()

for user in unpaused_users:
    online_pull = get_online_channels_followed(user["picarto_access_token"])
    print(online_pull)
    if user["picarto_lastonline"] is None:
        previous_online = {}
    else:
        previous_online = json.loads(user["picarto_lastonline"])
    message = "TEST, msg @Ceralor if OK! "
    if len(online_pull)>0:
        new_streams = [ x for x in online_pull.values() if (x["user_id"] not in online_pull.keys()) \
        and ( \
            (user["show_nsfw"] == True and x["adult"] == False) or \
            x["adult"] == False)\
        and ( \
            (user["show_games"] == True and x["gaming"] == True) or \
            x["gaming"] == False)]
        if len(new_streams)>0:
            message += "The following users are now streaming:\n"
            message += "\n".join([x["name"] for x in new_streams])
        else:
            if [x for x in online_pull.keys()].sort == previous_online.sort():
                message += "No new streamers, only old ones."
            else:
                message += "No one you follow is currently streamin that meets your settings. Ask @Ceralor to adjust them for you until he implements changing them."
    else:
        message += "No one you follow is currently streaming."
    #bot.send_message(user["tguser_id"],message)
    print(str(user["tguser_id"])+message)
    if len(online_pull.keys())>0:
        online_json = json.dumps([x for x in online_pull.keys()])
    else:
        online_json = "[]"
    con,cur = get_mysql_cursor(mysql)
    cur.execute("UPDATE `users` SET `picarto_lastonline` = %s WHERE `tguser_id` = %s", \
        [online_json, \
        user["tguser_id"]])
    con.commit()
    cur.close()
    con.close()

con,cur = get_mysql_cursor(mysql)
cur.execute("select tguser_id from users")
users = cur.fetchall()
for user in users:
    bot.send_message(user,"Thank you so much for helping me test this, I appreciate it greatly!")
cur.close()
con.close()

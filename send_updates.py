#!/usr/bin/python3
from app import app, bot, mysql
from helpers import get_mysql_cursor, mysql_fetch_assoc
from flask import url_for, render_template
from picarto_profiles import *
import requests, json

con,cur = get_mysql_cursor(mysql)
cur.execute("SELECT * FROM `users` WHERE `paused` = 0 and `picarto_access_token` is not null")
unpaused_users = mysql_fetch_assoc(cur)
cur.close()
con.close()

for user in unpaused_users:
    online_pull = get_online_channels_followed(user["picarto_access_token"])
    prev_on_json = user["picarto_lastonline"] or "[]"
    previous_online = json.loads(prev_on_json)
    if len(online_pull)>0:
        streams = online_pull.values()
        new_streams = [ stream for stream in streams if (int(stream["adult"]) <= user["show_nsfw"]) \
            and (int(stream["gaming"]) <= user["show_games"]) \
            and (stream["user_id"] not in previous_online) ]
            ##and (stream["private"] == False) ]
        if len(new_streams)>0:
            for stream in new_streams:
                streamer_name = stream["name"]
                suffix = (" (NSFW)" if stream["adult"] else "") + (" (Game)" if stream["gaming"] else "")
                preview_url = "https://relay.omgdragons.com:8443/picarto_preview/"+stream["name"]
                with app.app_context():
                	message = render_template("now_streaming_message.txt",suffix=suffix,preview_url=preview_url,streamer_name=streamer_name)
                	bot.send_message(user["tguser_id"],message,parse_mode="Markdown")
                #bot.send_message(54326855,message,parse_mode="Markdown")
    online_json = json.dumps([x for x in online_pull.keys()]) if len(online_pull.keys())>0 else "[]"
    con,cur = get_mysql_cursor(mysql)
    cur.execute("UPDATE `users` SET `picarto_lastonline` = %s WHERE `tguser_id` = %s", \
        [online_json, \
        user["tguser_id"]])
    con.commit()
    cur.close()
    con.close()

# con,cur = get_mysql_cursor(mysql)
# cur.execute("select tguser_id from users")
# users = cur.fetchall()
# for user in [stream[0] for x in users]:
#     #print(user)
#     bot.send_message(user,"Thank you so much for helping me test this, I appreciate it greatly!")
# cur.close()
# con.close()

from flask import Flask, render_template, request, json
from telescope import Bot
from flask.ext.mysql import MySQL
from datetime import datetime, timedelta
import json, requests, picarto_profiles
from helpers import get_mysql_cursor, mysql_fetch_assoc
app = Flask(__name__)

with open("config.json") as fh:
    app.config.update(json.load(fh))
    app.secret_key = app.config["TG_API_KEY"]

bot = Bot(app)

mysql = MySQL()
mysql.init_app(app)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/picarto_auth", methods=["POST","GET"])
def picarto_auth():
    if (request.args.get("code") == None) or (request.args.get("state") == None):
        return render_template("auth_failed.html") + " There's not needed args."
    con,cur = get_mysql_cursor(mysql)
    user_id = request.args.get("state")
    cur.callproc('check_tg_user',[user_id])
    data = cur.fetchall()
    if len(data) is 0:
        cur.execute("delete from `users` where `tguser_id` = %s", [user_id])
        return render_template("auth_failed.html") + " Your user ID isn't set up yet."
    data = { "code":request.args.get("code"),\
        "redirect_uri" : "https://puffydrake.com/oauth.php",\
        "client_id" : app.config["picarto_client_id"],\
        "client_secret" : app.config["picarto_client_secret"],\
        "scope" : "readpriv", "grant_type" : "authorization_code"}
    r = requests.post("https://oauth.picarto.tv/token", data = data)
    response = r.json()
    if response["scope"] != "readpriv":
        return render_template("auth_failed.html") + " The scope did not reply correctly." + str(response)
    dt = timedelta(seconds=response["expires_in"]-86400)
    today = datetime.today()
    expire_datetime = today + dt
    cur.execute("UPDATE `users` SET `picarto_access_token` = %s, `picarto_refresh_token` = %s, `picarto_token_expires` = %s WHERE `tguser_id` = %s",\
        (response["access_token"], response["refresh_token"], expire_datetime,user_id))
    con.commit()
    cur.close()
    con.close()
    bot.send_message(user_id,render_template("auth_success.txt"))
    return render_template("auth_success.html")

@bot.command("start")
def start_auth(message):
    con,cur = get_mysql_cursor(mysql)
    user_id = message["from"]["id"]
    cur.callproc('check_tg_user',[user_id])
    con.commit()
    cur.close()
    return render_template("welcome_auth.txt", user_id=user_id, client_id=app.config["picarto_client_id"])

@bot.command("help")
def get_help(message):
    chat_id = message["from"]["id"]
    reply_message = render_template("bot_help.txt")
    reply_markup = {"inline_keyboard": [ \
        [{"text":"Get online streamers you follow","callback_data":"/who_online"}], \
        [{"text":"Check and change your settings","callback_data":"/settings"}], \
        [{"text":"Reauthorize me with your Picarto account","callback_data":"/reauth"}] \
    ]}
    bot.send_message(chat_id,reply_message,reply_markup=reply_markup,disable_web_page_preview=True)
    return None

@bot.command("settings")
def get_settings(message):
    con,cur = get_mysql_cursor(mysql)
    tguser_id = message["from"]["id"]
    print(tguser_id)
    cur.execute("SELECT * FROM `users` WHERE `tguser_id` = %s LIMIT 1",[tguser_id])
    results = mysql_fetch_assoc(cur)
    print(str(results))
    return "Muted: "+str(bool(results[0]["paused"]))

@bot.command("mute")
@bot.command("games")
@bot.command("nsfw")
def not_yet(message):
    return "Sorry, I'm not quite there yet. But soon!"

@bot.command("who_online")
def get_online_streamers(message):
    con,cur = get_mysql_cursor(mysql)
    tguser_id = message["from"]["id"]
    #bot.send_message(tguser_id,"One sec...")
    cur.execute("SELECT * FROM `users` WHERE `tguser_id` = %s",[tguser_id])
    user = mysql_fetch_assoc(cur)[0]
    channels = picarto_profiles.get_online_channels_followed(user["picarto_access_token"])
    #channels_followed = [ x["user_id"] for x in picarto_profiles(results[1])["following"]] 
    #print(str(channels))
    names = [ x["name"] for x in channels.values() if (int(x["adult"]) <= user["show_nsfw"]) and (int(x["gaming"]) <= user["show_games"]) ]
    names_string = "\n".join(names)
    if len(names_string) > 0:
        return "These people are streaming:\n" + names_string
    else:
        return "No one's currently streaming that you follow."


@bot.command("reauth")
def reauth(message):
    con,cur = get_mysql_cursor(mysql)
    user_id = message["from"]["id"]
    cur.callproc('check_tg_user',[user_id])
    con.commit()
    return render_template("reauth.txt", user_id=message["from"]["id"], client_id=app.config["picarto_client_id"])

@bot.command("delete")
def delete_user(message):
    params = bot.find_params(message["text"])
    if params == None:
        return "You must add 'yes' as an argument"
    elif params == "yes":
        con,cur = get_mysql_cursor(mysql)
        cur.execute("DELETE FROM `users` where `tguser_id` = %s",[message["from"]["id"]])
        con.commit()
        return "Sorry to see you go! Come back soon!"
    else:
        return "Didn't understand what you said. You must say 'yes' after the command."

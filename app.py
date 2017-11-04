from flask import Flask, render_template, request, json
from telescope import Bot
from flask.ext.mysql import MySQL
from datetime import datetime, timedelta
import json, requests

app = Flask(__name__)

with open("config.json") as fh:
    app.config.update(json.load(fh))
    app.secret_key = app.config["TG_API_KEY"]

bot = Bot(app)

mysql = MySQL()
mysql.init_app(app)

def get_mysql_cursor():
    conn = mysql.connect()
    cursor = conn.cursor()
    return (conn,cursor)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/picarto_auth", methods=["POST","GET"])
def picarto_auth():
    if (request.args.get("code") == None) or (request.args.get("state") == None):
        return render_template("auth_failed.html") + " There's not needed args."
    con,cur = get_mysql_cursor()
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
    cur.execute("UPDATE `users` SET `picarto_access_token` = %s, `picarto_refresh_token` = %s, `picarto_token_expires` = %s",\
        [response["access_token"], response["refresh_token"], expire_datetime])
    con.commit()
    cur.close()
    con.close()
    bot.send_message(user_id,render_template("auth_success.txt"))
    return render_template("auth_success.html")

@bot.command("start")
def start_auth(message):
    con,cur = get_mysql_cursor()
    user_id = message["from"]["id"]
    cur.callproc('check_tg_user',[user_id])
    con.commit()
    cur.close()
    return render_template("welcome_auth.txt", user_id=user_id, client_id=app.config["picarto_client_id"])

@bot.command("help")
@bot.command("settings")
@bot.command("who_online")
@bot.command("mute")
@bot.command("games")
@bot.command("nsfw")
def get_who_online(message):
    return "Sorry, I'm not quite there yet. But soon!"

@bot.command("reauth")
def reauth(message):
    con,cur = get_mysql_cursor()
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
        con,cur = get_mysql_cursor()
        cur.execute("DELETE FROM `users` where `tguser_id` = %s",[message["from"]["id"]])
        con.commit()
        return "Sorry to see you go! Come back soon!"
    else:
        return "Didn't understand what you said. You must say 'yes' after the command."

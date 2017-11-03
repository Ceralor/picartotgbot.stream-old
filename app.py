from flask import Flask, render_template
from telescope import Bot
from flask.ext.mysql import MySQL
import json

app = Flask(__name__)

with open("config.json") as fh:
	app.config = json.load(fh)

bot = Bot(app)

mysql = MySQL()
mysql.init_app(app)

def get_mysql_cursor():
	conn = mysql.connect()
	cursor = conn.cursor()
	return cursor

@app.route("/")
def hello():
	return render_template("index.html")

@bot.command("start")
def start_auth(message):
	cur = get_mysql_cursor()
	
	return "Hello"

@bot.command("who_online")
def get_who_online(message):
	return "No one. Ever."

@bot.command("interact")
def bot_interact(message):
	# Get the rest of the message string
	params_text = bot.find_params(message["text"])
	if params_text == "":
		msg = "Hey... You didn't say anything!"
	else:
		msg = "Hey, you also said " + params_text
	return msg

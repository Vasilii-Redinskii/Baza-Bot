import os
import asyncio

from flask import Flask, request

import telebot

from app.settings import TG_TOKEN, HEROKU_URL
from app.tg_bot import bot


server = Flask(__name__)

# Constant to choose webhook or polling, webhook for production
# worp = 'polling'
worp = 'webhook'


if worp == 'polling':
    bot.delete_webhook()
    asyncio.run(bot.polling())

elif worp == 'webhook':
    @server.route('/' + TG_TOKEN, methods=['POST'])
    def get_message():
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200


    @server.route("/")
    def webhook():
        bot.remove_webhook()
        bot.set_webhook(url=HEROKU_URL + TG_TOKEN)
        return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

from app import app
import asyncio
import os
import telebot
from telebot import types

from app.log import log_expect, log_info
from app.models import BotHandler
from app.settings import TG_TOKEN, SHEET_URL, FOLDER_ID, INDEX, MAIN_MENU
from app.utils import create_button

bot = telebot.TeleBot(TG_TOKEN, parse_mode=None)


# create buttons constants
BTN_ACCEPT = create_button('accept', '✅ Принять')
BTN_CANCEL = create_button('cancel', '🔙 Назад')
BTN_MAIN = create_button('main', '📝 Начало')
BTN_UPDATE = create_button('update', '🔄 Обновить')


nl = '\n'


# responses to button presses from inline
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    asyncio.run(handle_callback(call))


async def handle_callback(call):
    try:
        user_id = call.from_user.id
        bot_handler = BotHandler(user_id, bot)
        bot_handler.local_dict['call'] = call
        bot_handler.save_state()
        if call.message:
            # buttons of cells in first colon
            if call.data in bot_handler.main_list:
                bot_handler.go_next_level(call)
            # buttons of cells in this colon
            elif call.data in bot_handler.local_dict.get('interval_values'):
                new_row = bot_handler.local_dict.get('cell_row') + bot_handler.local_dict.get('interval_values').index(call.data)
                bot_handler.go_next_level(call, bot_handler.local_dict.get('next_col'), row=new_row)
            elif call.data.split() and (call.data.split()[0] == INDEX):
                if call.data == f'{INDEX} - {MAIN_MENU}':
                    bot_handler.choose_section(call.message)
                else:
                    prev_element = bot_handler.step_list[int(call.data.split()[1])]
                    bot_handler.go_cur_level(call.message.chat.id, prev_element)
            elif call.data == 'Next':
                bot_handler.go_next_row(call, bot_handler.local_dict.get('cell_row'))
            else:
                bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    except Exception as e:
        log_expect(f"Error callback_inline: {e}")


# first message
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    asyncio.run(handle_welcome(message))


async def handle_welcome(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        bot_handler = BotHandler(user_id, bot)

        if not bot_handler.user_exists():
            bot_handler.add_user(username, first_name, last_name)

        img = open('hello.png', 'rb')
        bot.send_sticker(message.chat.id, img)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        btn1 = types.KeyboardButton(BTN_MAIN['text'])
        # btn2 = types.KeyboardButton(BTN_UPDATE['text'])
        btn3 = types.KeyboardButton(BTN_CANCEL['text'])
        # btn4 = types.KeyboardButton(BTN_ACCEPT['text'])
        #
        # markup.add(btn1, btn2, btn3, btn4)
        markup.add(btn1, btn3)

        bot.reply_to(message, f'Привет! Я бот - твой помощник. \n\n'
                              f'Для того чтобы начать с главного меню, нажми кнопку "📝 Начало".\n\n'
                              # f'Выбери нужный раздел и перейди в него, нажми кнопку "✅ Принять".\n\n'
                              f'Вернуться на предыдущий раздел или отменить выбор, нажми кнопку "🔙 Назад".\n\n'
                              f'Для обновления меня в нужном разделе, нажми кнопку "🔄 Обновить".',
                              reply_markup=markup)

    except Exception as e:
        log_expect(f"Error sending welcome message: {e}")


# responses to button presses
@bot.message_handler(content_types=['text'])
def send_text(message):
    asyncio.run(handle_text(message))


async def handle_text(message):
    try:
        user_id = message.from_user.id
        bot_handler = BotHandler(user_id, bot)
        # buttons for main list
        if message.text == BTN_MAIN['text']:
            if bot_handler.main_list is not None:
                bot_handler.main_list.clear()
            bot_handler.choose_section(message)
        # buttons for main list
        elif message.text == BTN_CANCEL['text']:
            if bot_handler.local_dict.get('next_col') > 2:
                bot_handler.go_prev_level(message)
            elif bot_handler.local_dict.get('next_col') == 2:
                bot_handler.choose_section(message)
            else:
                bot.reply_to(message, f'Для того чтобы начать с главного меню, нажми кнопку "📝 Начало".\n\n',
                                      reply_markup=None)
    except Exception as e:
        log_expect(f"Error text message: {e}")

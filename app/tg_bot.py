from app import app
import asyncio
import os
import telebot
from telebot import types

from app.log import log_expect, log_info
from app.models import BotHandler
from app.settings import TG_TOKEN, FOLDER_ID, INDEX, MAIN_MENU, ADMIN_ID
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
                bot_handler.go_next_level(call, merge_list=bot_handler.merge_list)
            # buttons of cells in this colon
            elif call.data in bot_handler.local_dict.get('interval_values'):
                new_row = bot_handler.local_dict.get('cell_row') + bot_handler.local_dict.get('interval_values').index(call.data)
                bot_handler.go_next_level(call, bot_handler.local_dict.get('next_col'), row=new_row,
                                          merge_list=bot_handler.merge_list)
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
        bot_handler = BotHandler(user_id, bot)
        bot_handler.check_user(message)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        btn1 = types.KeyboardButton(BTN_MAIN['text'])
        btn2 = types.KeyboardButton(BTN_UPDATE['text'])
        btn3 = types.KeyboardButton(BTN_CANCEL['text'])
        # btn4 = types.KeyboardButton(BTN_ACCEPT['text'])
        #
        # markup.add(btn1, btn2, btn3, btn4)

        if user_id == ADMIN_ID:
            markup.add(btn1, btn2, btn3)
        else:
            markup.add(btn1, btn3)

        bot_handler.welcome_message(message)

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
        bot_handler.check_user(message)
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
        # update work table from maim table
        elif message.text == BTN_UPDATE['text']:
            if user_id == ADMIN_ID:
                bot_handler.update_table()
                bot.send_message(message.chat.id, 'Таблица обновлена', reply_markup=None)

    except Exception as e:
        log_expect(f"Error text message: {e}")

from app import app
import asyncio
import os
import telebot
from telebot import types

from app.account_viewer import view_account, disconnect_client
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
BTN_ACC_VIEW = create_button('acc_view', '👀 Просмотр аккаунтов')
BTN_ACC_DISCONNECT = create_button('acc_disconnect', '🚫 Закрыть сессию')

nl = '\n'

is_view_account_running = False


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
    if message.from_user.id == bot.get_me().id:
        return
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
        # Для просмотра всех групп со своего аккаунта из тг бота - раскоммитеть
        # btn4 = types.KeyboardButton(BTN_ACC_VIEW['text'])
        # btn5 = types.KeyboardButton(BTN_ACC_DISCONNECT['text'])

        if user_id == ADMIN_ID:
            markup.add(btn1, btn2, btn3)
            # Для просмотра всех групп со своего аккаунта из тг бота - раскоммитеть
            # markup.add(btn1, btn2, btn3, btn4, btn5)
        else:
            markup.add(btn1, btn3)

        bot_handler.welcome_message(message, markup)

    except Exception as e:
        log_expect(f"Error sending welcome message: {e}")


# responses to button presses
@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.from_user.id == bot.get_me().id:
        return
    asyncio.run(handle_text(message))


async def handle_text(message):
    global is_view_account_running
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

        # Для просмотра всех групп со своего аккаунта из тг бота - раскоммитеть
        # view accounts from Google Sheet
        # elif message.text == BTN_ACC_VIEW['text']:
        #     if user_id == ADMIN_ID:
        #         table_id = bot_handler.get_table_id()
        #         if not is_view_account_running:
        #             is_view_account_running = True
        #             try:
        #                 # Асинхронно вызываем функцию view_account
        #                 await view_account(table_id)
        #                 bot.send_message(message.chat.id, 'Просмотр аккаунтов завершен.', reply_markup=None)
        #             except Exception as e:
        #                 log_expect(f"Error during view_account execution: {e}")
        #                 bot.send_message(message.chat.id,
        #                                  'Произошла ошибка при просмотре аккаунтов.', reply_markup=None)
        #             finally:
        #                 is_view_account_running = False
        #         else:
        #             bot.send_message(message.chat.id,
        #                              'Просмотр аккаунтов уже запущен. Пожалуйста, дождитесь завершения.',
        #                              reply_markup=None)
        # elif message.text == BTN_ACC_DISCONNECT['text']:
        #     if user_id == ADMIN_ID:
        #         await disconnect_client()
        #         bot.send_message(message.chat.id, 'Соединение с клиентом Telethon разорвано.', reply_markup=None)

        # log info from message
        else:
            log_info(f"Received message: {message.text}\n"
                     f"id user: {user_id}\n"
                     f"username: {message.from_user.username}\n"
                     f"chat ID: {message.chat.id}\n"
                     f"is_bot: {message.from_user.is_bot}")
            if message.from_user.id == ADMIN_ID:
                if message.forward_from_chat:
                    chat_id = message.forward_from_chat.id
                    chat_title = message.forward_from_chat.title
                    chat_username = message.forward_from_chat.username
                    bot.send_message(message.chat.id,
                                     f'Чат ID: {chat_id if "chat_id" in locals() else "Неизвестно"}\n'
                                     f'Название чата: {chat_title if "chat_title" in locals() else "Неизвестно"}\n'
                                     f'Username: {chat_username if "chat_username" in locals() else "Неизвестно"}\n',
                                     reply_markup=None)
            bot.send_message(message.chat.id, 'Неизвестная команда. Пожалуйста, выберите кнопку или начните заново.',
                             reply_markup=None)

    except Exception as e:
        log_expect(f"Error text message: {e}")


# get other messages
@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice',
                                    'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title',
                                    'new_chat_photo', 'delete_chat_photo', 'group_chat_created',
                                    'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id',
                                    'migrate_from_chat_id', 'pinned_message', 'web_app_data', 'invoice',
                                    'successful_payment', 'connected_website', 'poll', 'dice',
                                    'message_auto_delete_timer_changed', 'forum_topic_created',
                                    'forum_topic_closed', 'forum_topic_reopened', 'video_chat_started',
                                    'video_chat_ended', 'video_chat_participants_invited', 'proximity_alert_triggered',
                                    'write_access_allowed', 'general_forum_topic_hidden',
                                    'general_forum_topic_unhidden', 'unpin_all_chat_messages', 'users_shared',
                                    'chat_shared'])
def handle_all_other_messages(message):
    if message.from_user.id == bot.get_me().id:
        return
    log_info(f"Received message\n"
             f"id user: {message.from_user.id}\n"
             f"username: {message.from_user.username}\n"
             f"chat ID: {message.chat.id}\n"
             f"is_bot: {message.from_user.is_bot}")
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, 'Неизвестная команда. Пожалуйста, выберите кнопку или начните заново.\n',
                         reply_markup=None)
    bot.send_message(message.chat.id, 'Неизвестная команда. Пожалуйста, выберите кнопку или начните заново.\n',
                     reply_markup=None)

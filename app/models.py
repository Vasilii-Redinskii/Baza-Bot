from sqlalchemy import create_engine, Column, Integer, String, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from telebot import types

from app.google_drive import download_file_from_gdrive
from app.google_sheets import get_interval, get_row_cells, get_colomn_cells
from app.log import log_expect, log_info
from app.utils import create_button
from app.settings import INDEX, MAIN_MENU

# create DB and engine
engine = create_engine('sqlite:///users.db')
Base = declarative_base()


# Users model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    local_dict = Column(PickleType)
    step_list = Column(PickleType)
    main_list = Column(PickleType)
    menu_list = Column(PickleType)


# Create table
Base.metadata.create_all(engine)


# Create session
Session = sessionmaker(bind=engine)
session = Session()


class BotHandler:
    def __init__(self, user_id, bot):
        self.user_id = user_id
        self.bot = bot
        self.local_dict = {'next_col': 0, 'cell_row': 1}
        self.step_list = []
        self.main_list = []
        self.menu_list = []
        self.load_state()

    # create buttons list
    @staticmethod
    def create_button_list(button_list):
        try:
            btn_list = []
            for cell in button_list:
                btn_s = create_button(cell, cell)
                btn = types.InlineKeyboardButton(btn_s['text'], callback_data=btn_s['key'])
                btn_list.append(btn)
            return btn_list
        except Exception as e:
            log_expect(f"Error creating list of buttons: {e}")
            return []

    # go to current level
    def go_cur_level(self, chat_id, value):
        try:
            self.local_dict = value
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*self.create_button_list(value.get('interval_values')))
            self.bot.send_message(chat_id, value.get('name_level'), reply_markup=markup)
            self.save_state()
        except Exception as e:
            log_expect(f"Error transition to current level: {e}")
            self.bot.send_message(chat_id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    # Check cells and go to previous level
    def go_prev_level(self, message):
        try:
            prev_level_list = []
            for index, step in enumerate(self.step_list):
                prev_level_list.append(f'{INDEX} {index} - {step.get("name_level")}')
            prev_level_list.append(f'{INDEX} - {MAIN_MENU}')
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*self.create_button_list(prev_level_list))
            self.bot.send_message(message.chat.id, "Предыдущие шаги", reply_markup=markup)
            self.save_state()

        except Exception as e:
            log_expect(f"Error when go to the previous level: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    # Check cells and go to next level
    def go_next_level(self, call, column=1, **kwargs):
        try:
            new_interval = get_interval(call.data, column, **kwargs)
            if new_interval.get('type_level') == 'Level':
                self.local_dict = new_interval
                self.step_list.append(new_interval)
                if len(new_interval.get('interval_values')) != 0:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(*self.create_button_list(new_interval.get('interval_values')))
                    self.bot.send_message(call.message.chat.id, new_interval.get('name_level'), reply_markup=markup)
                else:
                    self.go_next_level(call, column + 1, row=kwargs.get('row'))
            elif new_interval.get('type_level') == 'Text':
                if len(new_interval.get('interval_values')) != 0:
                    if new_interval.get('picture'):
                        photo_file = open(download_file_from_gdrive(new_interval.get('picture')), 'rb')
                        self.bot.send_photo(call.message.chat.id, photo=photo_file)
                    self.bot.send_message(call.message.chat.id, new_interval.get('interval_values')[0], reply_markup=None)
                else:
                    self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала',
                                          reply_markup=None)
            else:
                self.choose_section(call.message)
            self.save_state()

        except Exception as e:
            log_expect(f"Error when go to the next level: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    # Choose activity sends
    def choose_section(self, message):
        # create buttons for menu
        try:
            if self.main_list is None or len(self.main_list) == 0:
                self.main_list = get_colomn_cells(1)
            if self.menu_list is None or len(self.menu_list) == 0:
                self.menu_list = get_row_cells(1)
            if self.step_list is not None:
                self.step_list.clear()
            button_list = self.create_button_list(self.main_list[1:])
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*button_list)
            self.bot.send_message(message.chat.id, self.main_list[0], reply_markup=markup)
            self.save_state()

        except Exception as e:
            log_expect(f"Error selecting partition: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    def save_state(self):
        user = session.query(User).filter_by(user_id=self.user_id).first()

        if user:
            user.local_dict = self.local_dict
            user.step_list = self.step_list
            user.main_list = self.main_list
            user.menu_list = self.menu_list
            session.commit()

    def load_state(self):
        user = session.query(User).filter_by(user_id=self.user_id).first()

        if user:
            self.local_dict = user.local_dict if user.local_dict else {'next_col': 0, 'cell_row': 1}
            self.step_list = user.step_list if user.step_list else []
            self.main_list = user.main_list if user.main_list else []
            self.menu_list = user.menu_list if user.menu_list else []

    def user_exists(self):
        return session.query(User).filter_by(user_id=self.user_id).first() is not None

    def add_user(self, username, first_name, last_name):
        new_user = User(user_id=self.user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(new_user)
        session.commit()

    def clean(self):
        pass


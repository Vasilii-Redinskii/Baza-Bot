from sqlalchemy import create_engine, Column, Integer, String, PickleType, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from telebot import types

from app.google_drive import download_file_from_gdrive, copy_table_from_drive_to_folder
from app.google_sheets import get_interval, get_row_cells, get_column_cells, get_merge_list, write_cell,\
    get_settings_dict, get_title_of_sheet, get_all_cels
from app.log import log_expect, log_info
from app.utils import create_button
from app.settings import INDEX, MAIN_MENU, SHEET_ID, FOLDER_WRITE_ID, PICTURE_LINK

# create DB and engine
engine = create_engine('sqlite:///users.db')
Base = declarative_base()

# Create table
Base.metadata.create_all(engine)


# Create session
Session = sessionmaker(bind=engine)
session = Session()


# Main table model
class MainTable(Base):
    __tablename__ = 'main_table'
    id = Column(Integer, primary_key=True)
    table_id = Column(String)
    main_list = Column(PickleType)
    menu_list = Column(PickleType)
    merge_list = Column(PickleType)

    sheet_table = relationship("SheetTable", back_populates="main_table", cascade="all, delete-orphan")


# Sheet table model
class SheetTable(Base):
    __tablename__ = 'sheet_table'
    id = Column(Integer, primary_key=True)
    table_id = Column(String, ForeignKey('main_table.id'))
    sheet_name = Column(String)

    main_table = relationship("MainTable", back_populates="sheet_table")
    settings_table = relationship("SettingsTable", back_populates="sheet_table", cascade="all, delete-orphan")


# Settings table model
class SettingsTable(Base):
    __tablename__ = 'settings_table'
    id = Column(Integer, primary_key=True)
    sheet_id = Column(String, ForeignKey('sheet_table.id'))
    sheet_name = Column(String)
    wellcome_text = Column(String)
    wellcome_picture = Column(String)
    wellcome_picture_link = Column(String)

    sheet_table = relationship("SheetTable", back_populates="settings_table")


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


sheet_id = session.query(MainTable).first().table_id


class BotHandler:
    def __init__(self, user_id, bot):
        self.user_id = user_id
        self.bot = bot
        self.local_dict = {'next_col': 0, 'cell_row': 1}
        self.step_list = []
        self.main_list = []
        self.menu_list = []
        self.merge_list = []

        self.load_state()

    def check_user(self, message):
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        if not self.user_exists():
            self.add_user(username, first_name, last_name)

    def choose_photo_link(self, value, chat_id):
        if len(value.get('interval_values')) != 0:
            if value.get('picture') or value.get('picture') != '':
                if PICTURE_LINK in value.get('picture'):
                    photo_file = open(download_file_from_gdrive(value.get('picture')), 'rb')
                else:
                    photo_file = value.get('picture')
                photo_message = self.bot.send_photo(chat_id, photo=photo_file)
                if photo_file != value.get('picture'):
                    cell = f'R{self.local_dict.get("cell_row")}C{self.local_dict.get("next_col")+3}'
                    write_cell(sheet_id, photo_message.photo[0].file_id, cell)
            markup = types.InlineKeyboardMarkup()
            markup.add(*self.create_button_list(["Next"]))
            self.bot.send_message(chat_id, value.get('interval_values')[0],
                                  reply_markup=markup)
        else:
            self.bot.send_message(chat_id, 'Нет информации об объекте, начните сначала',
                                  reply_markup=None)
        return

    # create buttons list
    @staticmethod
    def create_button_list(button_list):
        try:
            btn_list = []
            for cell in button_list:
                if cell:
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
                if step.get('interval_values'):
                    prev_level_list.append(f'{INDEX} {index} - {step.get("name_level")[:20]}')
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
            new_interval = get_interval(sheet_id, call.data, column, **kwargs)
            if new_interval.get('type_level') == 'Level':
                self.local_dict = new_interval
                self.step_list.append(new_interval)
                if len(new_interval.get('interval_values')) != 0:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(*self.create_button_list(new_interval.get('interval_values')))
                    self.bot.send_message(call.message.chat.id, new_interval.get('name_level'), reply_markup=markup)
                else:
                    self.go_next_level(call, column + 1, **kwargs)
            elif new_interval.get('type_level') == 'Text':
                self.choose_photo_link(new_interval, call.message.chat.id)
            else:
                self.choose_section(call.message)
            self.save_state()

        except Exception as e:
            log_expect(f"Error when go to the next level: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    # Check cells and go to next row
    def go_next_row(self, call, row):
        try:
            new_interval = get_interval(sheet_id, call.data, self.local_dict.get('next_col'), row=row+1,
                                        merge_list=self.merge_list)
            self.local_dict['cell_row'] = row+1
            self.choose_photo_link(new_interval, call.message.chat.id)
            self.save_state()

        except Exception as e:
            log_expect(f"Error when go to the next level: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    # Choose start section
    def choose_section(self, message):
        # create buttons for menu
        try:
            if self.main_list is None or len(self.main_list) == 0:
                self.main_list = get_column_cells(sheet_id, 1)
            if self.menu_list is None or len(self.menu_list) == 0:
                self.menu_list = get_row_cells(sheet_id, 1)
            if self.step_list is not None:
                self.step_list.clear()
            if self.merge_list is not None:
                try:
                    self.merge_list = get_merge_list(sheet_id)
                except Exception as e:
                    log_expect(f"Error selecting partition: {e}")
                    update_table(message)

            button_list = self.create_button_list(self.main_list[1:])
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*button_list)
            self.bot.send_message(message.chat.id, self.main_list[0], reply_markup=markup)
            self.save_state()

        except Exception as e:
            log_expect(f"Error selecting partition: {e}")
            self.bot.send_message(call.message.chat.id, 'Нет информации об объекте, начните сначала', reply_markup=None)

    def save_state(self):
        table = session.query(MainTable).first()
        user = session.query(User).filter_by(user_id=self.user_id).first()

        if user:
            user.local_dict = self.local_dict
            user.step_list = self.step_list
            table.main_list = self.main_list
            table.menu_list = self.menu_list
            table.merge_list = self.merge_list
            session.commit()

    def load_state(self):
        table = session.query(MainTable).first()
        user = session.query(User).filter_by(user_id=self.user_id).first()

        if user:
            self.local_dict = user.local_dict if user.local_dict else {'next_col': 0, 'cell_row': 1}
            self.step_list = user.step_list if user.step_list else []
        if table:
            self.main_list = table.main_list if table.main_list else []
            self.menu_list = table.menu_list if table.menu_list else []
            self.merge_list = table.merge_list if table.merge_list else []
        else:
            self.update_table()

    def user_exists(self):
        return session.query(User).filter_by(user_id=self.user_id).first() is not None

    def add_user(self, username, first_name, last_name):
        new_user = User(user_id=self.user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(new_user)
        session.commit()

    def clean(self):
        pass

    @staticmethod
    def get_table_id():
        table = session.query(MainTable).first()
        return table.table_id if table else None

    @staticmethod
    def update_table():
        id_copied_table = copy_table_from_drive_to_folder(SHEET_ID, FOLDER_WRITE_ID)
        table = session.query(MainTable).first()
        if table:
            table.table_id = id_copied_table
        else:
            table = MainTable(table_id=id_copied_table)
            session.add(table)
        table.main_list = get_column_cells(id_copied_table, 1)
        table.menu_list = get_row_cells(id_copied_table, 1)
        table.merge_list = get_merge_list(id_copied_table)

        # Удаление всех записей из SettingsTable и SheetTable
        session.query(SettingsTable).delete()
        session.query(SheetTable).delete()

        # Создание новых записей SheetTable
        sheet_name_list = get_title_of_sheet(id_copied_table)
        sheets = [SheetTable(sheet_name=name, table_id=id_copied_table) for name in sheet_name_list]
        sheet_name = 'Settings'
        settings_dict = {}
        try:
            sheet_list = get_all_cels(id_copied_table, sheet_name)
            settings_dict = get_settings_dict(sheet_list)
            for values in sheet_list.get('valueRanges')[0].get('values'):
                if values[0] == 'sheet_id':
                    cell = f'{sheet_name}!R{sheet_list.get("valueRanges")[0].get("values").index(values)+1}C{2}'
                    write_cell(id_copied_table, str(id_copied_table), cell)
        except Exception as e:
            log_expect(f"Error selecting partition: {e}")
            self.bot.send_message(call.message.chat.id, f'Нет информации о листе "{sheet_name}", добавьте лист или '
                                                        f'проверьте его название, начните сначала', reply_markup=None)

        # Получение допустимых полей класса SettingsTable
        valid_fields = {column.name for column in SettingsTable.__table__.columns}

        # Фильтрация словаря
        filtered_dict = {key: value for key, value in settings_dict.items() if key in valid_fields}

        # Создание объекта SettingsTable из отфильтрованного словаря
        settings_item = SettingsTable(**filtered_dict)

        try:
            session.add_all(sheets + [settings_item])
            session.commit()
        except Exception as e:
            session.rollback()
            log_expect(f"Transaction failed: {e}")

    def welcome_message(self, message, markup=None):
        wellcome_table = session.query(SettingsTable).first()
        wellcome_text = wellcome_table.wellcome_text if wellcome_table.wellcome_text \
            else f'Привет! Я бот - твой помощник. \n\n ' \
                 f'Для того чтобы начать с главного меню, нажми кнопку "📝 Начало".\n\n ' \
                 f'Вернуться на предыдущий раздел или отменить выбор, нажми кнопку "🔙 Назад".\n\n'
        try:
            if wellcome_table.wellcome_picture:
                self.bot.send_photo(message.chat.id, photo=wellcome_table.wellcome_picture)

            elif wellcome_table.wellcome_picture_link:
                photo_file = open(download_file_from_gdrive(wellcome_table.wellcome_picture_link), 'rb')
                photo_message = self.bot.send_photo(message.chat.id, photo=photo_file)
                # TODO save id picture to sell
                # sheet_id = session.query(MainTable).first().table_id
                # cell = f'R{self.local_dict.get("cell_row")}C{self.local_dict.get("next_col") + 3}'
                # write_cell(sheet_id, photo_message.photo[0].file_id, cell)
                self.bot.reply_to(message, photo_message.photo[0].file_id, reply_markup=markup)

        except Exception as e:
            log_expect(f"Error transition to current level: {e}")

        self.bot.send_message(message.chat.id, wellcome_text, reply_markup=markup)
        return

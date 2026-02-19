from telethon import TelegramClient
import datetime
# Для просмотра всех групп со своего аккаунта из тг бота - раскоммитеть
# from app.settings import API_ID, API_HASH, PHONE_NUMBER, SHEET_ID
from app.google_sheets import get_title_of_sheet, get_settings_dict, get_all_cels, write_cell
from app.log import log_expect

# Your API credentials and phrases
# Для просмотра всех групп со своего аккаунта из тг бота - раскоммитеть
# api_id = API_ID
# api_hash = API_HASH
# phone_number = PHONE_NUMBER
api_id = "API_ID"
api_hash = "API_HASH"
phone_number = "PHONE_NUMBER"
phrases = ["переезд", "аэропорт", "трансфер"]


def disconnect_client():
    """
    Disconnects the Telethon client.
    """
    try:
        if client.is_connected():
            client.disconnect()
            print("Telethon client has been disconnected.")
        else:
            print("Telethon client is not connected.")
    except Exception as e:
        log_expect(f"Error disconnecting client: {e}")


# A helper function to get messages from a dialog
async def get_message_from_dialog(client, dialog_number, items, last_message_id=None):
    phrase_list = [item.strip() for item in items.split(',')]
    """
    Fetches messages from a specified dialog and prints those
    containing any of the given phrases.
    """
    try:
        chat_messages = client.iter_messages(int(dialog_number), offset_id=last_message_id,
                                             reverse=True)

        # The RuntimeError happens here. Since get_message_from_dialog is an async function
        # and client.iter_messages returns an async iterator, we must use `async for`.
        async for message in chat_messages:
            # Check if the message has text and contains any of the phrases
            message_text = message.text
            if message_text is not None and (any(phrase.lower() in message_text.lower() for phrase in phrase_list)):
                sender_name = message.sender.first_name if message.sender.first_name else "Неизвестный отправитель"
                sender_last_name = message.sender.last_name if message.sender.last_name else ""
                full_sender_name = f"{sender_name} {sender_last_name}".strip()
                message_link = ""
                if message.peer_id:
                    message_link = f"\nСсылка на сообщение: https://t.me/c/{message.peer_id.channel_id}/{message.id}"

                await client.send_message('me', f"--- Найдено совпадение ---\n"
                                                f"Автор: {full_sender_name}\n"
                                                f"Сообщение: {message_text}\n"
                                                f"Дата: {message.date}\n"
                                                f"ID сообщения: {message.id}"
                                                f"{message_link}\n"
                                                f"--------------------------\n")
            last_message_id = message.id

    except Exception as e:
        log_expect(f"Error in get_message_from_dialog: {e}")

    return last_message_id


async def view_account(sheet_id=SHEET_ID):
    # Initialize the Telegram client
    client = TelegramClient('my_session', api_id, api_hash,
                            device_model="iPhone 13 Pro Max",
                            system_version="14.8.1",
                            app_version="8.4",
                            lang_code="en",
                            system_lang_code="en-US")

    try:
        async with client:

            # Get dialogs
            dialogs = await client.get_dialogs()

            # Check for chats in the Google Sheet
            sheet_name = 'Chats'
            sheet_list = get_all_cels(sheet_id, sheet_name)
            title_dict = get_settings_dict(sheet_list, 0, 2)
            message_id_dict = get_settings_dict(sheet_list, 0, 3)
            count_values = len(sheet_list.get('valueRanges')[0].get('values'))
            index = 1
            for dialog in dialogs:
                if (dialog.is_group or dialog.is_channel) and str(abs(dialog.id)) not in title_dict.keys():
                    cell_id = f'R{count_values + index}C{1}'
                    cell_name = f'R{count_values + index}C{2}'
                    full_range_id = f"'{sheet_name}'!{cell_id}"
                    full_range_name = f"'{sheet_name}'!{cell_name}"
                    write_cell(sheet_id, str(abs(dialog.id)), full_range_id)
                    write_cell(sheet_id, dialog.name, full_range_name)
                    index += 1

            for index, (key, value) in enumerate(title_dict.items()):
                if key.isdigit() and value != '':
                    if message_id_dict.get(key, 0).isdigit():
                        mes_value = int(message_id_dict.get(key, 0))
                    else:
                        mes_value = 0
                    last_message_id = int(mes_value) if key in message_id_dict else None
                    new_message_id = await get_message_from_dialog(client, key, value, last_message_id)
                    if new_message_id != last_message_id and new_message_id is not None:
                        cell = f'R{index+1}C{4}'
                        full_range = f"'{sheet_name}'!{cell}"
                        write_cell(sheet_id, new_message_id, full_range)
                else:
                    print(f"Skipping non-numeric key in spreadsheet: {key} or value is empty.")

    except Exception as e:
        log_expect(f"Error in main while processing spreadsheet data: {e}")
        disconnect_client()

    finally:
        if client.is_connected():
            disconnect_client()

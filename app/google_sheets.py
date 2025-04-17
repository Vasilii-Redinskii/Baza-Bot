import datetime
import gspread
from app.settings import CREDENTIALS, SHEET_ID, SCOPES_SHEET
from googleapiclient.discovery import build
from google.oauth2 import service_account
# from app import models

# get access parameters
credentials = service_account.Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES_SHEET)
service = build("sheets", "v4", credentials=credentials)
SERVICE = gspread.service_account_from_dict(CREDENTIALS)


sheet = service.spreadsheets()


# check cell
def check_picture_cell(cell_list, index):
    try:
        value = cell_list[index]
    except:
        value = ''
    return value


# get merge list
def get_merge_list(sheet_id, num_sheet=0):
    merge_list = sheet.get(spreadsheetId=sheet_id).execute()['sheets'][num_sheet]['merges']
    return merge_list


# get all cells in the sheet
def get_all_cels(sheet_id, name_sheet):
    value = sheet.values().batchGet(spreadsheetId=sheet_id, ranges=[name_sheet]).execute()
    return value


# return list of all cells in column
def get_column_cells(sheet_id, column):
    wsheet = SERVICE.open_by_key(sheet_id).get_worksheet(0)
    col_list = list(filter(None, wsheet.col_values(column)))
    return col_list[1:]


# return list of all cells in column
def get_row_cells(sheet_id, row):
    wsheet = SERVICE.open_by_key(sheet_id).get_worksheet(0)
    row_list = list(filter(None, wsheet.row_values(row)))
    final_list = []
    for index, cell in enumerate(row_list):
        final_list.append({'id': index+1, 'value': cell})
    return final_list


def get_settings_dict(sheet_id, name):
    sheet_list = get_all_cels(sheet_id, name)
    settings_dict = {}
    for value in sheet_list.get('valueRanges')[0].get('values'):
        if len(value) > 1:
            try:
                settings_dict[value[0]] = value[1]
            except:
                pass
    return settings_dict


def get_title_of_sheet(sheet_id):
    sheet_list = sheet.get(spreadsheetId=sheet_id).execute().get('sheets', [])
    title_list = []
    for item in sheet_list:
        title = item.get('properties').get('title')
        title_list.append(title)
    return title_list


def get_interval(sheet_id, level, column, **kwargs):
    if column == 1:
        wsheet = SERVICE.open_by_key(sheet_id).get_worksheet(0)
        cell_row = wsheet.findall(level, None, column)[0].row
    else:
        cell_row = kwargs.get('row')
    level_value = sheet.values().batchGet(spreadsheetId=sheet_id,
                                          ranges=[f'R1C{column+1}:R2C{column+1}',
                                                  f'R{cell_row}C{column+1}:R{cell_row}C{column+1}',
                                                  f'R{cell_row}C{column}:R{cell_row}C{column}',
                                                  f'A1:1',
                                                  f'A{cell_row}:{cell_row}'
                                                  ]).execute()
    try:
        type_level = level_value.get('valueRanges')[0].get('values')[0][0]
    except:
        type_level = 'Empty'
    try:
        name_level = level_value.get('valueRanges')[0].get('values')[1][0]
    except:
        name_level = 'Пусто'
    value_dict = {'next_col': column+1, 'cell_row': cell_row, 'type_level': type_level,
                  'name_level': name_level}
    merge_list = kwargs.get('merge_list')
    for merge_cell in merge_list:
        if merge_cell.get('startColumnIndex') < column <= merge_cell.get('endColumnIndex') and \
                merge_cell.get('startRowIndex') < cell_row <= merge_cell.get('endRowIndex') and \
                merge_cell.get('startRowIndex') != merge_cell.get('endRowIndex')-1:
            start_cell = f'R{merge_cell.get("startRowIndex")+1}C{merge_cell.get("endColumnIndex")+1}'
            finish_cell = f'R{merge_cell.get("endRowIndex")}C{merge_cell.get("endColumnIndex") + 1}'
            merge_interval = f'{start_cell}:{finish_cell}'
            values_interval = sheet.values().get(spreadsheetId=sheet_id, range=merge_interval).execute()
            value_dict['interval'] = [values_interval.get('range'), merge_interval]
            value_dict['interval_values'] = [x[0] if len(x) != 0 else x for x in values_interval.get('values')]
            return value_dict

    value_dict['interval'] = [level_value.get('range'), f'R{cell_row}C{column+1}']
    if level_value.get('valueRanges')[1].get('values'):
        value_dict['interval_values'] = [x[0] for x in level_value.get('valueRanges')[1].get('values')]
        if type_level == 'Text':
            text_index = level_value.get('valueRanges')[4].get('values')[0].index(value_dict['interval_values'][0])
            picture_id = check_picture_cell(level_value.get('valueRanges')[4].get('values')[0], text_index + 2)
            picture_link = check_picture_cell(level_value.get('valueRanges')[4].get('values')[0], text_index + 1)
            if picture_id != '':
                value_dict['picture'] = picture_id
            else:
                value_dict['picture'] = picture_link
    else:
        value_dict['interval_values'] = []
    return value_dict


# write cell
def write_cell(sheet_id, value, cell):
    body = {
        'values': [
            [value],
        ]
    }
    sheet.values().update(spreadsheetId=sheet_id, range=cell, valueInputOption="RAW", body=body).execute()
    return

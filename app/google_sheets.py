import datetime
import gspread
import os.path
import time
from app.settings import CREDENTIALS, SHEET_ID, SCOPES_SHEET
from googleapiclient.discovery import build
from google.oauth2 import service_account

# get access parameters
credentials = service_account.Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES_SHEET)
service = build("sheets", "v4", credentials=credentials)
SERVICE = gspread.service_account_from_dict(CREDENTIALS)
SHEET = SERVICE.open_by_key(SHEET_ID)
WORKSHEET = SHEET.get_worksheet(0)
SHEET_RANGE = "Sheet1"

sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE, majorDimension="COLUMNS",
                            valueRenderOption="FORMATTED_VALUE").execute()
merge_list = sheet.get(spreadsheetId=SHEET_ID).execute()['sheets'][0]['merges']

print(result)


# return list of all cells in column
def get_colomn_cells(column):
    col_list = list(filter(None, WORKSHEET.col_values(column)))
    return col_list[1:]


# return list of all cells in column
def get_row_cells(row):
    row_list = list(filter(None, WORKSHEET.row_values(row)))
    final_list = []
    for index, cell in enumerate(row_list):
        final_list.append({'id': index+1, 'value': cell})
    return final_list


def get_interval(level, column, **kwargs):
    if column == 1:
        cell_row = WORKSHEET.findall(level, None, column)[0].row
    else:
        cell_row = kwargs.get('row')
    level_value = sheet.values().batchGet(spreadsheetId=SHEET_ID,
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
    for merge_cell in merge_list:
        if merge_cell.get('startColumnIndex') < column <= merge_cell.get('endColumnIndex') and \
                merge_cell.get('startRowIndex') < cell_row <= merge_cell.get('endRowIndex') and \
                merge_cell.get('startRowIndex') != merge_cell.get('endRowIndex')-1:
            start_cell = f'R{merge_cell.get("startRowIndex")+1}C{merge_cell.get("endColumnIndex")+1}'
            # Check how many rows are in the merged cell as different count is needed
            if (merge_cell.get('endRowIndex') - merge_cell.get('startRowIndex')) % 2 != 0:
                finish_cell = f'R{merge_cell.get("endRowIndex")}C{merge_cell.get("endColumnIndex")+1}'
            else:
                finish_cell = f'R{merge_cell.get("endRowIndex")+1}C{merge_cell.get("endColumnIndex") + 1}'
            merge_interval = f'{start_cell}:{finish_cell}'
            values_interval = sheet.values().get(spreadsheetId=SHEET_ID, range=merge_interval).execute()
            value_dict['interval'] = [values_interval.get('range'), merge_interval]
            value_dict['interval_values'] = [x[0] for x in values_interval.get('values')]
            return value_dict

    value_dict['interval'] = [level_value.get('range'), f'R{cell_row}C{column+1}']
    if level_value.get('valueRanges')[1].get('values'):
        value_dict['interval_values'] = [x[0] for x in level_value.get('valueRanges')[1].get('values')]
        if type_level == 'Text':
            text_index = level_value.get('valueRanges')[4].get('values')[0].index(value_dict['interval_values'][0])
            try:
                value_dict['picture'] = level_value.get('valueRanges')[4].get('values')[0][text_index+1]
            except:
                value_dict['picture'] = []
    else:
        value_dict['interval_values'] = []
    return value_dict

from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.discovery import build
from app.settings import CREDENTIALS, SCOPES
import io
import datetime
import os


credentials = service_account.Credentials.from_service_account_info(CREDENTIALS, scopes=SCOPES)
service = build('drive', 'v3', credentials=credentials)


# function to download file from Google Drive
def download_file_from_gdrive(url):
    url = url.replace('https://drive.google.com/file/d/', '')
    index = url.find('/')
    url = url[:index]
    request = service.files().get_media(fileId=url)
    file_id = f'{url}.jpg'
    fh = io.FileIO(file_id, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    return file_id


# copies a table from Google Drive to a specified folder on Google Drive.
def copy_table_from_drive_to_folder(source_file_id, folder_id):
    """
    :param source_file_id: ID of the source file on Google Drive.
    :param folder_id: ID of the destination folder on Google Drive.
    :return: ID of the newly copied file.
    """
    try:
        # Get file metadata
        file_metadata = service.files().get(fileId=source_file_id, fields='name, mimeType',).execute()
        copy_file_name = f'Copy of {file_metadata["name"]}'
        mime_type = file_metadata['mimeType']

        # Check the file type and create the appropriate file type on Drive
        if mime_type.startswith('application/vnd.google-apps'):
            # Search for a file with the same name in the destination folder
            query = f"'{folder_id}' in parents and name = '{copy_file_name}' and trashed = false"
            response = service.files().list(q=query, fields='files(id)').execute()
            files = response.get('files', [])
            if files:
                # Update existing file if found
                existing_file_id = files[0]['id']
                service.files().delete(fileId=existing_file_id).execute()

            # Copy the file to the new folder if not found
            copied_file = service.files().copy(
                fileId=source_file_id,
                body={
                    'name': copy_file_name,
                    'parents': [folder_id]
                }
            ).execute()

            # Copy backup the file to the new folder
            copied_backup_file = service.files().copy(
                fileId=source_file_id,
                body={
                    'name': f'{datetime.datetime.now()}{copy_file_name}',
                    'parents': [folder_id]
                }
            ).execute()

            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{copied_file['id']}/edit"
            print(
                f"File '{copy_file_name}' successfully copied to folder with ID: {folder_id}. "
                f"New file ID: {copied_file['id']}"
                f"URL table : {spreadsheet_url}")

            return copied_file['id']

    except Exception as e:
        print(f"Error copying file: {e}")
        return None

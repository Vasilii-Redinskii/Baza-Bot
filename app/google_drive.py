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

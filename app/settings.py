import os
from dotenv import load_dotenv


load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

CREDENTIALS = {
  "type": "service_account",
  "project_id": os.getenv("PROJECT_ID", ""),
  "private_key_id": os.getenv("PRIVATE_KEY_ID", ""),
  "private_key": os.getenv("PRIVATE_KEY", '').replace('\\n', '\n'),
  "client_email": os.getenv("CLIENT_EMAIL", ""),
  "client_id": os.getenv("CLIENT_ID", ""),
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": os.getenv("CLIENT_SER_URL", ""),

}


FOLDER_ID = os.getenv("FOLDER_ID", "")
HEROKU_URL = os.getenv("HEROKU_URL", "")
PASSWORD = os.getenv("PASSWORD", "")
SCOPES = ['https://www.googleapis.com/auth/drive']
SCOPES_SHEET = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_ID = os.getenv("SHEET_ID", "")
SHEET_URL = os.getenv("SHEET_URL", "")
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
TG_TOKEN = os.getenv("TG_TOKEN", "")

INDEX = 'Шаг'
MAIN_MENU = 'Основное меню'
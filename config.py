import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'users.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STATIC_ROOT = os.path.join(basedir, 'app/static')
    ALLOWED_EXTENSIONS = ('png', 'jpg', 'jpeg')
import os

class config:
    SECRET_KEY = 'simoon321'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///school_db.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # for profile pics
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

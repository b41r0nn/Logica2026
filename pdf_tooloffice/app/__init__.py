import os

from flask import Flask

from .cleanup import start_cleanup_scheduler
from .database import init_db
from .routes import bp

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'logs.db')
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB


def create_app():
	app = Flask(__name__)
	app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
	app.config['DATABASE_PATH'] = DATABASE_PATH
	app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
	app.config['SECRET_KEY'] = os.urandom(24)

	os.makedirs(UPLOAD_FOLDER, exist_ok=True)
	os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

	init_db(DATABASE_PATH)
	start_cleanup_scheduler(UPLOAD_FOLDER, DATABASE_PATH)

	app.register_blueprint(bp)
	return app

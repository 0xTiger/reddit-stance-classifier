import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import import_string

from config import Config

config: Config = import_string(os.environ['APP_SETTINGS'])
app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)
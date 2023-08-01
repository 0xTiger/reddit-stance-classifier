import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

class Config:
    DEBUG = not os.environ['ENV'] == 'prod'
    DEVELOPMENT = not os.environ['ENV'] == 'prod'
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    POSTGRES_USER = os.environ['POSTGRES_USER']
    POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
    POSTGRES_HOST = os.environ['POSTGRES_HOST']
    WEBSITE_DB = os.environ['WEBSITE_DB']
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{WEBSITE_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DOMAIN_URL = 'https://reddit-lean.com/' if os.environ['ENV'] == 'prod' else 'http://127.0.0.1:5000/'

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
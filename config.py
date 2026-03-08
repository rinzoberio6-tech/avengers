import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-ekalusugan'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ekalusugan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

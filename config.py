import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-ekalusugan'
    
    # Handle Render's DATABASE_URL beginning with postgres:// (SQLAlchemy expects postgresql://)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///ekalusugan.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

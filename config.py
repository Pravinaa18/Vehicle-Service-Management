import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'autocare-super-secret-key-2026-prod')
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
    DEBUG = True

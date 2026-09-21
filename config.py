import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'autocare-super-secret-key-2026-prod')
    # Use /tmp on Vercel (read-only filesystem except /tmp)
    if os.environ.get('VERCEL') == '1':
        DATABASE = '/tmp/database.db'
    else:
        DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
    DEBUG = os.environ.get('VERCEL') != '1'

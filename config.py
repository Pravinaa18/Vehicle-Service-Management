import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_path():
    override = os.environ.get('DATABASE_PATH')
    if override:
        return override

    if os.environ.get('VERCEL'):
        tmp_path = os.path.join('/tmp', 'autocare_database.db')
        if not os.path.exists(tmp_path) and os.path.exists(os.path.join(BASE_DIR, 'database.db')):
            import shutil
            shutil.copy2(os.path.join(BASE_DIR, 'database.db'), tmp_path)
        return tmp_path

    return os.path.join(BASE_DIR, 'database.db')


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'autocare-super-secret-key-2026-prod')
    DATABASE = get_database_path()
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

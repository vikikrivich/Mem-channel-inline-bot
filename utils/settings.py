"""
Файл настроек бота
"""
import logging
import os
from dotenv import load_dotenv


class BaseSettings:
    """Base settings class"""
    ROOT_DIR: str = os.getcwd()

    LOGGING_FORMAT: str = "[{asctime}]: {filename:>7}/{lineno:<5} :: {message}"
    LOGGING_LEVEL_DISPLAY = logging.DEBUG
    LOGGING_LEVEL_FILESTREAM = logging.WARN
    LOGGING_FILENAME: str = 'project.log'

    def __init__(self):
        self.TOKEN = None
        self.SUPABASE_URL = None
        self.SUPABASE_KEY = None
        self.CHANNEL_ID = None
        self.MY_TELEGRAM_ID = None
        self.PROXY_URL = None

    def load_from_dotenv(self):
        dotenv_path = os.path.join(self.ROOT_DIR, '.env')

        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        else:
            with open('.env', 'w') as env:
                env.write(
                    'TOKEN=\n'
                    'SUPABASE_URL=\n'
                    'SUPABASE_KEY=\n'
                    'CHANNEL_ID=\n'
                    'MY_TELEGRAM_ID=\n'
                    'PROXY_URL='\n
                )

        self.TOKEN = os.environ.get('TOKEN')
        self.SUPABASE_URL = os.environ.get('SUPABASE_URL')
        self.SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
        self.CHANNEL_ID = os.environ.get('CHANNEL_ID')
        self.PROXY_URL = os.environ.get('PROXY_URL')
        
        my_id = os.environ.get('MY_TELEGRAM_ID')
        self.MY_TELEGRAM_ID = int(my_id) if my_id and my_id.isdigit() else None
        
        return True


settings = BaseSettings()
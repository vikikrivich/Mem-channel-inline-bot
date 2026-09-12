"""
 Файл настроек бота
"""
import logging
import os
from dotenv import load_dotenv


class BaseSettings:
    """Base settings class"""
    ROOT_DIR: str = os.getcwd()

    # 'FORMAT': '[{asctime}] [{levelname:>7}] [{name}] :: {message}',
    LOGGING_FORMAT: str = "[{asctime}]: {filename:>7}/{lineno:<5} :: {message}"
    LOGGING_LEVEL_DISPLAY = logging.DEBUG
    LOGGING_LEVEL_FILESTREAM = logging.WARN
    LOGGING_FILENAME: str = 'project.log'

    def __init__(self):
        self.TOKEN = None

    def load_from_dotenv(self):
        dotenv_path = os.path.join(self.ROOT_DIR, '.env')

        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path)
        else:
            with open('.env', 'w') as env:
                env.write('# TOKEN=')

        self.TOKEN = os.environ.get('TOKEN')
        return True


settings = BaseSettings()
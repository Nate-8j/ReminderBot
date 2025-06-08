import os
from dotenv import find_dotenv, load_dotenv

from aiogram import Bot, Dispatcher

load_dotenv(find_dotenv())
bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()


from common.scheduler import ReminderManager
reminder_manager = ReminderManager()

from common.database.db_repository import Repository
DB_URL = os.getenv('DB_URL')

repository = Repository(DB_URL)

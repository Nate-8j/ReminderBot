import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

DB_URL = os.getenv('DB_URL')
BOT_TOKEN = os.getenv('TOKEN')

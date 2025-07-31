import asyncio
from aiogram import types
from aiogram import Dispatcher

from common.database.db_repository import Repository
from common.scheduler import ReminderManager
from config import DB_URL
from kbds.bot_cmds_list import private

from handlers.user_handlers import UserHandlers
from handlers.reminders.one_time import OneTimeHandlers
from handlers.reminders.regular import RegularHandlers
from handlers.reminders.get_list import ListHandlers

from common.bot_instance import bot

import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('apscheduler').setLevel(logging.DEBUG)


dp = Dispatcher()

repository = Repository(DB_URL)
reminder_manager = ReminderManager(repository)

user_handlers = UserHandlers(repository)
one_time_handlers = OneTimeHandlers(bot, reminder_manager, repository)
regular_handlers = RegularHandlers(bot, reminder_manager, repository)
list_handlers = ListHandlers(reminder_manager, repository)

dp.include_router(user_handlers.get_router())
dp.include_router(one_time_handlers.get_router())
dp.include_router(regular_handlers.get_router())
dp.include_router(list_handlers.get_router())


async def main():
    asyncio.create_task(reminder_manager.start_apscheduler())

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

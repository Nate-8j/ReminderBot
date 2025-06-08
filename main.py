import asyncio

from aiogram import types

from config import reminder_manager, bot, dp
from common.bot_cmds_list import private
from hendlers.user_private import  usr_prv

dp.include_router(usr_prv)


async def main():
    asyncio.create_task(reminder_manager.start_apscheduler())

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


asyncio.run(main())

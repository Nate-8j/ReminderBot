import asyncio

from aiogram import types

from config import reminder_manager, bot, dp
from common.bot_cmds_list import private
from hendlers.user_private import  usr_prv

dp.include_router(usr_prv)


async def main():
    await reminder_manager.init_scheduler_event()

    try:
        asyncio.create_task(reminder_manager.start_apscheduler())
    finally:
        await reminder_manager.close_scheduler()

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

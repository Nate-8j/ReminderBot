import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from config import bot, DB_URL

async def sending_reminder(chat_id: int, text: str):
    message_text = (
        "🔔 Напоминание:\n"
        "--------------------------------\n"
        f"«<i>{text}</i>»"
    )
    await bot.send_message(chat_id, message_text, parse_mode="HTML")


async def sending_repeat(chat_id: int, text: str):
    message_text = (
        "❕ Повторить:\n"
        "--------------------------------\n"
        f"«<i>{text}</i>»"
    )
    await bot.send_message(chat_id, message_text, parse_mode="HTML")


class ReminderManager:
    def __init__(self):
        self.engine = create_async_engine(DB_URL)
        self.scheduler_ready = asyncio.Event()
        self.data_store = SQLAlchemyDataStore(self.engine)
        self.scheduler = AsyncScheduler(self.data_store)

    async def start_apscheduler(self):
        async with self.scheduler:
            self.scheduler_ready.set()
            await self.scheduler.run_until_stopped()

    async def add_onetime_reminder(self, chat_id: int, text: str, remind_time: datetime):
        await self.scheduler_ready.wait()

        job_id = await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=DateTrigger(run_time=remind_time),
            args=(chat_id, text)
        )
        return job_id


    async def add_regular_reminder(self, chat_id: int, text: str, trigger: CronTrigger):
        await self.scheduler_ready.wait()

        job_id = await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=trigger,
            args=(chat_id, text)
        )
        return job_id

    async def add_interval_repetition(self, chat_id: int, text: str, remind_time: datetime):
        await self.scheduler_ready.wait()

        job_id = await self.scheduler.add_schedule(
            func_or_task_id=sending_repeat,
            trigger=DateTrigger(run_time=remind_time),
            args=(chat_id, text)
        )
        return job_id





import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from config import bot


async def sending_reminder(remind_data: dict):
    message_text = (
        "🔔 Напоминание:\n"
        "--------------------------------\n"
        f"«<i>{remind_data['text']}</i>»"
    )
    await bot.send_message(remind_data['chat_id'], message_text, parse_mode="HTML")


class ReminderManager:
    def __init__(self):
        self.engine = create_async_engine(
            os.getenv("ASYNC_DB_URL"),
            pool_size=20,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True

        )
        self.data_store = SQLAlchemyDataStore(self.engine)
        self.scheduler = AsyncScheduler(self.data_store)
        self.scheduler_ready = None

    async def init_scheduler_event(self):
        loop = asyncio.get_event_loop()
        self.scheduler_ready = loop.create_future()

    async def start_apscheduler(self):
        async with self.scheduler:
            self.scheduler_ready.set_result(None)
            await self.scheduler.run_until_stopped()

    async def close_scheduler(self):
        await self.engine.dispose()

    @asynccontextmanager
    async def get_scheduler(self):
        async with self.scheduler:
            yield self.scheduler

    async def add_onetime_reminder(
            self,
            chat_id: int,
            text: str,
            remind_time: datetime,
            small_text: str,
            type_: str,
            time_next_reminder: str
    ):
        await self.scheduler_ready

        await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=DateTrigger(run_time=remind_time),
            args=({
                      'chat_id': chat_id,
                      'text': text,
                      'small_text': small_text,
                      'type_': type_,
                      'time_next_reminder': time_next_reminder
                  },)
        )

    async def add_regular_reminder(
            self,
            chat_id: int,
            text: str,
            trigger: CronTrigger,
            small_text: str,
            type_: str,
            time_next_reminder: str
    ):
        await self.scheduler_ready

        await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=trigger,
            args=({
                      'chat_id': chat_id,
                      'text': text,
                      'small_text': small_text,
                      'type_': type_,
                      'time_next_reminder': time_next_reminder
                  },)
        )

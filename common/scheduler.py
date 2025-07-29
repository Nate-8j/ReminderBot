import asyncio
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler import AsyncScheduler, JobReleased, ScheduleRemoved
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from common.database.db_repository import Repository


async def sending_reminder(remind_data):
    message_text = (
        "🔔 Напоминание:\n"
        "--------------------------------\n"
        f"«<i>{remind_data['text']}</i>»"
    )
    await bot.send_message(chat_id=remind_data['chat_id'], text=message_text, parse_mode="HTML")

class ReminderManager:
    def __init__(self, repository: Repository, bot):
        self.repository = repository
        self.bot = bot

        self.engine = create_async_engine(
            os.getenv("ASYNC_DB_URL"),
            pool_size=20,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True

        )
        self.data_store = SQLAlchemyDataStore(self.engine)
        self.scheduler = AsyncScheduler(self.data_store)

        self.scheduler_ready = asyncio.Future()

    async def init_scheduler_event(self):
        if self.scheduler_ready.done():
            self.scheduler_ready = asyncio.Future()

    async def handle_job_released(self, event: [JobReleased, ScheduleRemoved]):
        pass
        schedule_id = event.schedule_id
        await self.repository.delete_reminder(schedule_id)
        # schedule = await self.scheduler.get_schedule(schedule_id)
        # if schedule is None or schedule.next_fire_time is not None:
        #     return

    async def start_apscheduler(self):
        self.scheduler_ready.set_result(None)

        async with self.scheduler:
            self.scheduler.subscribe(self.handle_job_released, [JobReleased, ScheduleRemoved], is_async=True)
            await self.scheduler.run_until_stopped()

    async def close_scheduler(self):
        await self.engine.dispose()

    async def add_onetime_reminder(self, chat_id: int, text: str, remind_time: datetime):
        await self.scheduler_ready
        job_id = await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=DateTrigger(run_time=remind_time),
            args=({'chat_id': chat_id, 'text': text},)
        )
        return job_id

    async def add_regular_reminder(self, chat_id: int, text: str, trigger: CronTrigger, ):
        await self.scheduler_ready
        job_id = await self.scheduler.add_schedule(
            func_or_task_id=sending_reminder,
            trigger=trigger,
            args=({'chat_id': chat_id, 'text': text},)
        )
        return job_id

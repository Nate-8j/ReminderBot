import asyncpg



class Repository:

    def __init__(self, bsn: str):
        self.bsn = bsn

    async def connect(self):
        return await asyncpg.connect(self.bsn)

    # noinspection PyMethodMayBeStatic
    async def get_text_from_db(self, name: str):
        conn = await self.connect()
        row = await conn.fetchrow('SELECT text FROM help_text WHERE name = $1', name)
        await conn.close()
        return row['text'].replace(r"\n", "\n")

    # noinspection PyMethodMayBeStatic
    async def add_user(self, chat_id, name, time_zone):
        conn = await self.connect()
        await conn.execute(
            'INSERT INTO users (chat_id, name, time_zone) VALUES ($1, $2, $3)',
            chat_id, name, time_zone
        )
        await conn.close()

    # noinspection PyMethodMayBeStatic
    async def add_reminder(self, chat_id, job_id, text, type_):
        conn = await self.connect()
        try:
            await conn.execute(
                """
                INSERT INTO reminders (chat_id, job_id, text, type)
                VALUES ($1, $2, $3, $4)
                """,
                chat_id, job_id, text, type_
            )
        finally:
            await conn.close()

    # noinspection PyMethodMayBeStatic
    async def get_time_zone(self, chat_id):
        conn = await self.connect()
        time_zone = await conn.fetchrow('SELECT time_zone FROM users WHERE chat_id = $1', chat_id)
        await conn.close()
        return time_zone['text']

    # noinspection PyMethodMayBeStatic
    async def get_reminder(self, chat_id):
        conn = await self.connect()
        rows = await conn.fetch('SELECT * FROM reminders WHERE chat_id = $1', chat_id)
        await conn.close()
        return rows


    # noinspection PyMethodMayBeStatic
    async def delete_reminder(self, job_id):
        conn = await self.connect()
        await conn.execute(
            'DELETE FROM reminders WHERE job_id = $1',
            job_id
        )
        await conn.close()

    # noinspection PyMethodMayBeStatic
    async def delete_not_active_reminders(self, to_delete):
        conn = await self.connect()
        await conn.execute(
            "DELETE FROM reminders WHERE job_id = ANY($1::text[])",
            list(to_delete)
        )
        await conn.close()

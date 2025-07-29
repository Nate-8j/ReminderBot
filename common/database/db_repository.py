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
    async def get_time_zone(self, chat_id):
        conn = await self.connect()
        time_zone = await conn.fetchrow('SELECT time_zone FROM users WHERE chat_id = $1', chat_id)
        await conn.close()
        return time_zone['text']

    async def add_reminder(self, job_id, txt, small_txt, user_id, type_, time_next_reminder):
        conn = await self.connect()
        await conn.execute(
            """INSERT INTO reminders (job_id, txt, small_txt, user_id, type_, time_next_reminder)
            VALUES ($1, $2, $3, $4, $5, $6)""",
            job_id, txt, small_txt, user_id, type_, time_next_reminder
        )
        await conn.close()

    async def get_reminders(self, user_id: int):
        conn = await self.connect()
        query = "SELECT job_id, small_txt, type_, time_next_reminder FROM reminders WHERE user_id = $1"
        rows = await conn.fetch(query, user_id)
        data = [dict(row) for row in rows]
        await conn.close()
        return data

    async def delete_reminder(self, job_id):
        conn = await self.connect()
        await conn.execute("DELETE FROM reminders WHERE job_id = $1", job_id)
        await conn.close()

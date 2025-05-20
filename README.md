# ReminderBot

📅 Telegram bot for creating one-time, recurring, and spaced repetition reminders.

This bot helps users manage their daily tasks, set regular notifications, and use scientifically proven **spaced repetition intervals** to memorize vocabulary, formulas, or any other information.

---

## ✅ Features

- One-time reminders with custom date & time.
- Recurring reminders:
  - Daily
  - Weekly (with multiple days of the week)
  - Monthly
  - Yearly
- Interval-based repetition reminders (based on **Spaced Repetition System**):
  - 1 day
  - 3 days
  - 7 days
  ...

You can list and delete your active reminders at any time.

---

## 🧩 Technologies Used

- [aiogram 3.x](https://github.com/aiogram/aiogram ) — async Telegram bot framework
- [apscheduler 3.x](https://github.com/agronholm/apscheduler ) — task scheduling
- [asyncpg](https://github.com/MagicStack/asyncpg ) — async PostgreSQL driver
- [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy ) — for scheduler storage
- [aiogram-calendar](https://github.com/aiogram-md/aiogram_calendar ) — calendar UI for choosing dates

---

## 🛠 Installation

1. Clone the repo

2. Create .env file:
  DB_URL=...
  BOT_TOKEN=your_telegram_bot_token

3. Create database and tables

4. Start the bot:
  python main.py

---

## 📂 Project Structure

aiogram_bot/
    common/
        database/
            db_repository.py
            psql.sql
        scheduler.py
    handlers/
        admin_private.py
        user_private.py
    kbds/
        inline.py
        reply.py
    .env
    main.py

---

## 🤝 Contact

If you have questions or want to contribute, feel free to reach out!
Telegram: @jk_n7548







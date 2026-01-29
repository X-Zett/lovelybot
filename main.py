import os
import random
import asyncio
import asyncpg
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from keep_alive import keep_alive

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для подключения к БД
async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

# Инициализация таблиц
async def init_db():
    conn = await get_db_connection()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS memories (id SERIAL PRIMARY KEY, file_id TEXT);
        CREATE TABLE IF NOT EXISTS expenses (id SERIAL PRIMARY KEY, amount INT);
        CREATE TABLE IF NOT EXISTS wishes (id SERIAL PRIMARY KEY, user_id BIGINT, text TEXT);
        CREATE TABLE IF NOT EXISTS important_dates (id SERIAL PRIMARY KEY, info TEXT);
    ''')
    await conn.close()

# --- 1. Банк воспоминаний ---
@dp.message(F.photo)
async def save_memory(message: types.Message):
    conn = await get_db_connection()
    await conn.execute('INSERT INTO memories (file_id) VALUES ($1)', message.photo[-1].file_id)
    await conn.close()
    await message.reply("📸 Сохранил в базу воспоминаний!")

@dp.message(Command("random_memory"))
async def get_memory(message: types.Message):
    conn = await get_db_connection()
    row = await conn.fetchrow('SELECT file_id FROM memories ORDER BY RANDOM() LIMIT 1')
    await conn.close()
    if row:
        await message.answer_photo(row['file_id'], caption="Помнишь это? ❤️")
    else:
        await message.answer("Копилка пуста.")

# --- 2. Колесо выбора (без БД, это просто логика) ---
@dp.message(Command("choose"))
async def choose_random(message: types.Message):
    options = message.text.replace("/choose", "").split(",")
    if len(options) > 1:
        await message.answer(f"🎲 Судьба выбрала: {random.choice(options).strip()}")

# --- 3. Бюджет ---
@dp.message(Command("spend"))
async def add_expense(message: types.Message):
    try:
        amount = int(message.text.split()[1])
        conn = await get_db_connection()
        await conn.execute('INSERT INTO expenses (amount) VALUES ($1)', amount)
        total = await conn.fetchval('SELECT SUM(amount) FROM expenses')
        await conn.close()
        await message.answer(f"💰 Записал {amount}. Итого потрачено: {total}")
    except:
        await message.answer("Пиши: /spend 500")

# --- 4. Секретные желания ---
@dp.message(Command("wish"))
async def add_wish(message: types.Message):
    if message.chat.type == 'private':
        wish_text = message.text.replace("/wish", "").strip()
        conn = await get_db_connection()
        await conn.execute('INSERT INTO wishes (user_id, text) VALUES ($1, $2)', message.from_user.id, wish_text)
        await conn.close()
        await message.answer("🤫 Секрет сохранен!")

@dp.message(Command("random_wish"))
async def get_random_wish(message: types.Message):
    conn = await get_db_connection()
    row = await conn.fetchrow('SELECT text FROM wishes ORDER BY RANDOM() LIMIT 1')
    await conn.close()
    if row:
        await message.answer(f"🎲 Случайное желание: {row['text']}")

# --- 5. Даты ---
@dp.message(Command("dates"))
async def show_dates(message: types.Message):
    # Можно добавить управление через БД, но пока оставим списком
    await message.answer("🗓 15 мая — Знакомство\n🗓 20 августа — Годовщина")

async def main():
    await init_db()
    keep_alive()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
import asyncpg
import config

# Bot token can be obtained via https://t.me/BotFather
TOKEN = config.BOT_TOKEN

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()

# Создание пула подключений к БД
async def create_db_pool():
    return await asyncpg.create_pool(
        user='myuser',
        password='mypassword',
        database='mydatabase',
        host='localhost'
    )


@dp.message(CommandStart())
async def command_start_handler(message: Message, pool: asyncpg.Pool) -> None:
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO subscribers (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING",
                message.chat.id
            )
        await message.answer(f"🚀 Hello, {html.bold(message.from_user.full_name)}! You're now subscribed to updates!")
    except Exception as e:
        logging.error(f"Subscription error: {e}")
        await message.answer("❌ Failed to subscribe. Please try later.")

@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


async def main() -> None:
    pool = await create_db_pool()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp["pool"] = pool

    # And the run events dispatching
    await dp.start_polling(bot)
    await pool.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

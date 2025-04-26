import asyncio
from enum import StrEnum
import logging
import sys
from typing import Dict

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from numpy import float64
from xgboost import XGBRegressor
import pandas as pd
import asyncpg
import config

TOKEN = config.BOT_TOKEN
MODEL_PATH = "./bot/xgb_model.json"

try:
    model = XGBRegressor()
    model.load_model(MODEL_PATH)
except Exception as e:
    model = None
    logging.error(f"Failed to load model: {e}")


class PhoneForm(StatesGroup):
    version = State()
    condition = State()
    is_pro = State()
    is_max = State()
    capacity = State()
    rating = State()
    reviews = State()
    subscribers = State()
    subscriptions = State()
    done_deals = State()
    active_deals = State()
    docs_confirmed = State()
    phone_confirmed = State()


dp = Dispatcher()

# Создание пула подключений к БД
async def create_db_pool():
    return await asyncpg.create_pool(
        user='myuser',
        password='mypassword',
        database='mydatabase',
        host='localhost'
    )


start_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/predict_price")]],
    resize_keyboard=True,
    input_field_placeholder="Choose action"
)

class VersionOptions(StrEnum):
    VERSION_6 = "6"
    VERSION_7 = "7"
    VERSION_8 = "8"
    VERSION_10 = "10"
    VERSION_11 = "11"
    VERSION_12 = "12"
    VERSION_13 = "13"
    VERSION_14 = "14"
    VERSION_15 = "15"
    VERSION_16 = "16"


class StateOptions(StrEnum):
    NEW = "Новое"
    EXCELLENT = "Отличное"
    GOOD = "Хорошее"
    SATISFACTORY = "Удовлетворительно"

class ConfirmOptions(StrEnum):
    YES = "Да"
    NO = "Нет"

class MemoryOptions(StrEnum):
    MEMORY_16 = "16"
    MEMORY_32 = "32"
    MEMORY_64 = "64"
    MEMORY_128 = "128"
    MEMORY_256 = "256"
    MEMORY_512 = "512"
    MEMORY_1024 = "1024"

class RatingOptions(StrEnum):
    RATING_0 = "0"
    RATING_1 = "1"
    RATING_2 = "2"
    RATING_3 = "3"
    RATING_4 = "4"
    RATING_5 = "5"

version_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=option.value) for option in list(VersionOptions)[i:i+3]]
        for i in range(0, len(list(VersionOptions)), 3)
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите версию"
)

state_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=option.value)]
        for option in StateOptions
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите состояние"
)

confirm_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=option.value)]
        for option in ConfirmOptions
    ],
    resize_keyboard=True,
    input_field_placeholder="Подтвердите"
)

memory_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=option.value)]
        for option in MemoryOptions
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите объем памяти"
)

rating_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=option.value)]
        for option in RatingOptions
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите рейтинг"
)


@dp.message(CommandStart())
async def command_start_handler(message: Message, pool: asyncpg.Pool) -> None:
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO subscribers (chat_id) VALUES ($1) ON CONFLICT (chat_id) DO NOTHING",
                message.chat.id
            )
        await message.answer(
            f"🚀 Hello, {html.bold(message.from_user.full_name)}! You're now subscribed to updates!\n"
            "Click /predict_price to predict your price!",
            reply_markup=start_keyboard
        )
    except Exception as e:
        logging.error(f"Subscription error: {e}")
        await message.answer("❌ Failed to subscribe. Please try later.")


@dp.message(Command("cancel"))
@dp.message(F.text.casefold() == "отмена")
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Процесс отменен", reply_markup=start_keyboard)


@dp.message(Command("predict_price"))
async def start_prediction(message: Message, state: FSMContext):
    if not model:
        await message.answer("⚠️ Сервис временно недоступен. Попробуйте позже.")
        return

    await message.answer(
        "Давайте оценим ваш телефон! Для отмены введите /cancel\n\n"
        "Введите версию телефона",
        reply_markup=version_keyboard
    )
    await state.set_state(PhoneForm.version)


@dp.message(PhoneForm.version, F.text.in_(VersionOptions))
async def process_version(message: Message, state: FSMContext):
    await state.update_data(version=message.text)
    await message.answer("Выберите состояние телефона", reply_markup=state_keyboard)
    await state.set_state(PhoneForm.condition)


@dp.message(PhoneForm.condition, F.text.in_(StateOptions))
async def process_condition(message: Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await message.answer("Это Pro версия?", reply_markup=confirm_keyboard)
    await state.set_state(PhoneForm.is_pro)


@dp.message(PhoneForm.is_pro, F.text.in_(ConfirmOptions))
async def process_is_pro(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("⚠️ Пожалуйста, ответьте 'да' или 'нет'")
        return

    await state.update_data(is_pro=message.text.lower() == "да")
    await message.answer("Это Max версия?", reply_markup=confirm_keyboard)
    await state.set_state(PhoneForm.is_max)


@dp.message(PhoneForm.is_max, F.text.in_(ConfirmOptions))
async def process_is_max(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("⚠️ Пожалуйста, ответьте 'да' или 'нет'")
        return

    await state.update_data(is_max=message.text.lower() == "да")
    await message.answer("Введите объем памяти (в ГБ):", reply_markup=memory_keyboard)
    await state.set_state(PhoneForm.capacity)


@dp.message(PhoneForm.capacity, F.text.in_(MemoryOptions))
async def process_capacity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return
    await state.update_data(capacity=int(message.text))
    await message.answer("Введите ваш рейтинг (от 0 до 5):", reply_markup=rating_keyboard)
    await state.set_state(PhoneForm.rating)


@dp.message(PhoneForm.rating, F.text.in_(RatingOptions))
async def process_rating(message: Message, state: FSMContext):
    try:
        rating = float(message.text)
        if rating < 0 or rating > 5:
            raise ValueError("Рейтинг должен быть от 0 до 5")
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите число от 0 до 5")
        return

    await state.update_data(rating=rating)
    await message.answer("Введите количество отзывов:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(PhoneForm.reviews)


@dp.message(PhoneForm.reviews)
async def process_reviews(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return

    await state.update_data(reviews=int(message.text))
    await message.answer("Введите количество подписчиков:")
    await state.set_state(PhoneForm.subscribers)


@dp.message(PhoneForm.subscribers)
async def process_subscribers(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return

    await state.update_data(subscribers=int(message.text))
    await message.answer("Введите количество подписок:")
    await state.set_state(PhoneForm.subscriptions)


@dp.message(PhoneForm.subscriptions)
async def process_subscriptions(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return

    await state.update_data(subscriptions=int(message.text))
    await message.answer("Введите количество сделок:")
    await state.set_state(PhoneForm.done_deals)


@dp.message(PhoneForm.done_deals)
async def process_done_deals(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return

    await state.update_data(done_deals=int(message.text))
    await message.answer("Введите количество активных сделок:")
    await state.set_state(PhoneForm.active_deals)


@dp.message(PhoneForm.active_deals)
async def process_active_deals(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите число")
        return

    await state.update_data(active_deals=int(message.text))
    await message.answer("Ваши документы подтверждены?", reply_markup=confirm_keyboard)
    await state.set_state(PhoneForm.docs_confirmed)


@dp.message(PhoneForm.docs_confirmed, F.text.in_(ConfirmOptions))
async def process_docs_confirmed(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("⚠️ Пожалуйста, ответьте 'да' или 'нет'")
        return

    await state.update_data(docs_confirmed=message.text.lower() == "да")
    await message.answer("Ваш номер телефона подтвержден?", reply_markup=confirm_keyboard)
    await state.set_state(PhoneForm.phone_confirmed)


@dp.message(PhoneForm.phone_confirmed, F.text.in_(ConfirmOptions))
async def process_phone_confirmed(message: Message, state: FSMContext):
    if message.text.lower() not in ["да", "нет"]:
        await message.answer("⚠️ Пожалуйста, ответьте 'да' или 'нет'")
        return

    await state.update_data(phone_confirmed=message.text.lower() == "да")
    data = await state.get_data()
    await state.clear()

    # Преобразование данных для модели
    try:
        features = prepare_features(data)
        # print all features
        logging.info(f"Features for prediction: {features}")

        prediction = model.predict(features)
        await message.answer(
            f"📊 Предполагаемая стоимость: {prediction[0]:.2f} ₽\n"
            "Спасибо за использование сервиса!",
            reply_markup=start_keyboard
        )
    except Exception as e:
        logging.error(f"Prediction error: {e}")
        await message.answer("⚠️ Ошибка при расчете стоимости. Попробуйте позже.")


def prepare_features(data: Dict) -> pd.DataFrame:
    """Преобразование сырых данных в формат для модели"""
    columns = [
        'version', 'condition_Новое', 'condition_Отличное',
        'condition_Хорошее', 'condition_Удовлетворительное',
        'capacity', 'rating', 'reviews',
        'subscribers', 'subscriptions', 'done_deals',
        'active_deals', 'is_pro_False', 'is_pro_True',
        'is_max_False', 'is_max_True', 'docs_confirmed_False',
        'docs_confirmed_True', 'phone_confirmed_False',
        'phone_confirmed_True'
    ]
    features = pd.DataFrame([data])

    features['condition_Новое'] = features['condition'].apply(
        lambda x: 1 if x == 'Новое' else 0)
    features['condition_Отличное'] = features['condition'].apply(
        lambda x: 1 if x == 'Отличное' else 0)
    features['condition_Хорошее'] = features['condition'].apply(
        lambda x: 1 if x == 'Хорошее' else 0)
    features['condition_Удовлетворительное'] = features['condition'].apply(
        lambda x: 1 if x == 'Удовлетворительное' else 0)
    features['version'] = features['version'].astype(float64)
    features['capacity'] = features['capacity'].astype(int)
    features['subscriptions'] = features['subscriptions'].astype(float64)
    features['done_deals'] = features['done_deals'].astype(float64)
    features['reviews'] = features['reviews'].astype(float64)
    features['rating'] = features['rating'].astype(float64)
    features['active_deals'] = features['active_deals'].astype(float64)
    features['subscribers'] = features['subscribers'].astype(float64)
    features['is_pro_True'] = features['is_pro'].apply(
        lambda x: 1 if x else 0)
    features['is_pro_False'] = features['is_pro'].apply(
        lambda x: 0 if x else 1)
    features['is_max_True'] = features['is_max'].apply(
        lambda x: 1 if x else 0)
    features['is_max_False'] = features['is_max'].apply(
        lambda x: 0 if x else 1)
    features['docs_confirmed_True'] = features['docs_confirmed'].apply(
        lambda x: 1 if x else 0)
    features['docs_confirmed_False'] = features['docs_confirmed'].apply(
        lambda x: 0 if x else 1)
    features['phone_confirmed_True'] = features['phone_confirmed'].apply(
        lambda x: 1 if x else 0)
    features['phone_confirmed_False'] = features['phone_confirmed'].apply(
        lambda x: 0 if x else 1)

    return features[columns]


async def main() -> None:
    pool = await create_db_pool()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML))
    dp["pool"] = pool

    # And the run events dispatching
    await dp.start_polling(bot)
    await pool.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

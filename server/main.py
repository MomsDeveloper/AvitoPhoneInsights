import asyncio
# from kafka import KafkaConsumer
import json
import traceback
import pandas as pd
import analytics.preprocessor as prep
from aiokafka import AIOKafkaConsumer
from analytics.models import Product, Seller
from aiogram import Bot
import bot.config as config
import asyncpg

async def create_db_pool():
    return await asyncpg.create_pool(
        user='myuser',
        password='mypassword',
        database='mydatabase',
        host='localhost'
    )

async def process_price_coeff(conn, phone_id):
    query = """
    SELECT version, is_pro, is_max, capacity, condition, price
    FROM product
    WHERE link = $1
    """
    result = await conn.fetch(query, phone_id)
    if not result:
        return None
    version, is_pro, is_max, capacity, condition, price = result[0]
    # Получаем среднюю цену для группы
    query = """
    SELECT AVG(price) as avg_price
    FROM product
    WHERE version = $1 AND is_pro = $2 AND is_max = $3 AND capacity = $4 AND condition = $5
    """
    result = await conn.fetch(query, version, is_pro, is_max, capacity, condition)
    if not result:
        return None
    avg_price = result[0]['avg_price']

    price_coeff = price / avg_price if avg_price else None

    return price_coeff

async def filter_message(conn, chat_id, product):
    query = """
    SELECT is_pro, is_max, capacity, condition, version, rating
    FROM subscribers_filters
    WHERE chat_id = $1
    """

    result = await conn.fetch(query, chat_id)
    if (not result) or len(result) == 0:
        return True

    filters = { 
        'is_pro': result[0]['is_pro'],
        'is_max': result[0]['is_max'],
        'capacity': result[0]['capacity'],
        'condition': result[0]['condition'],
        'version': result[0]['version'],
        'rating': result[0]['rating'],
    }
    # Проверяем фильтры
    for key, value in filters.items():
        if getattr(product, key, None) != value and ((value is not None)):
            return False
    return True

async def phone_consumer(topic: str, bootstrap_servers: str):
    bot = Bot(token=config.BOT_TOKEN)
    pool = await create_db_pool()

    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    await consumer.start()
    
    try:
        async for message in consumer:
            print(f"Received message: {message.value}")
            try:
                phone_data = json.loads(message.value.decode('utf-8'))
                phone_df = prep.clean_phone([phone_data])
                added_products = []

                async with pool.acquire() as conn:
                    async with conn.transaction():
                        for _, row in phone_df.iterrows():
                            # Подготовка данных
                            row = row.copy()
                            for col in ['characteristics', 'about']:
                                if isinstance(row[col], dict):
                                    row[col] = json.dumps(row[col])
                            
                            product = Product(**row.where(pd.notna(row), None).to_dict())
                            
                            # Вставка в БД
                            columns = ', '.join(row.index)
                            values = [getattr(product, col) for col in row.index]
                            await conn.execute(
                                f"INSERT INTO product ({columns}) VALUES ({', '.join(f'${i+1}' for i in range(len(values)))});",
                                *values
                            )
                            added_products.append(product)
                        
                        # Высчитываем коэффициент цены
                        price_coeff = await process_price_coeff(conn, product.link)
                        if price_coeff is None or price_coeff >= 1:
                            continue
                        # Рассылка уведомлений
                        subscribers = await conn.fetch("SELECT chat_id FROM subscribers")
                        for product in added_products:
                            message_text = f"📱 New phone: {product.title}\n💰 Price: {product.price} \n Link: {product.link} \n Coeff: {price_coeff}" 
                            for sub in subscribers:
                                try:
                                    # Проверка фильтров
                                    if not await filter_message(conn, sub['chat_id'], product):
                                        continue
                                    # Отправка сообщения
                                    await bot.send_message(sub['chat_id'], message_text)
                                except Exception as e:
                                    print(traceback.format_exc())
                                    print(f"Error sending to {sub['chat_id']}: {e}")
            except Exception as e:
                print(f"Error processing message: {e}")
    finally:
        await consumer.stop()
        await bot.close()
        await pool.close()


async def seller_consumer(topic: str, bootstrap_servers: str):
    pool = await create_db_pool()
    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    await consumer.start()
    print("Seller consumer started")
    try:
        async for message in consumer:
            try:
                seller_data = json.loads(message.value.decode('utf-8'))
                seller_df = prep.clean_seller([seller_data])
                
                sellers_headers = seller_df.columns
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        for _, row in seller_df.iterrows():
                            row = row.copy()
                            row = row.where(pd.notna(row), None)
                            
                            seller = Seller(**row.to_dict())
                            
                            await conn.execute(
                                f"INSERT INTO seller ({', '.join(sellers_headers)}) VALUES ({', '.join(f'${i+1}' for i in range(len(sellers_headers)))})",
                                *(getattr(seller, col) for col in sellers_headers)
                            )
            except Exception as e:
                print(f"Error adding seller: {e}")
    finally:
        await consumer.stop()
        await pool.close()
     

async def main():
    phone_task = asyncio.create_task(phone_consumer("phone_listings", "localhost:9092"))
    seller_task = asyncio.create_task(seller_consumer("seller_listings", "localhost:9092"))

    await asyncio.gather(phone_task, seller_task)

asyncio.run(main())

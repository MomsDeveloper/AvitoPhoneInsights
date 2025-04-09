import asyncio
import psycopg2
# from kafka import KafkaConsumer
import json 
import pandas as pd
import analytics.preprocessor as prep
from aiokafka import AIOKafkaConsumer
from analytics.models import Product, Seller

conn = psycopg2.connect("dbname=mydatabase user=myuser password=mypassword host=localhost port=5432")
cursor = conn.cursor()

async def phone_consumer(topic: str, bootstrap_servers: str):
    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    await consumer.start()
    print("Phone consumer started")
    try:
        async for message in consumer:
            try:
                phone_data = json.loads(message.value.decode('utf-8'))
                phone_df = prep.clean_phone([phone_data])
                phones_headers = phone_df.columns

                for _, row in phone_df.iterrows():
                    row = row.copy()
                    if isinstance(row['characteristics'], dict):
                        row['characteristics'] = json.dumps(row['characteristics'])
                    if isinstance(row['about'], dict):
                        row['about'] = json.dumps(row['about'])
                    
                    row = row.where(pd.notna(row), None)
                    product = Product(**row.to_dict())
                    
                    cursor.execute(
                        f"INSERT INTO product ({', '.join(phones_headers)}) VALUES ({', '.join(['%s'] * len(phones_headers))})",
                        tuple(getattr(product, col) for col in phones_headers)
                    )

                conn.commit()
            except Exception as e:
                print(f"Error adding product: {e}")
                conn.rollback()
    finally:
        await consumer.stop()

async def seller_consumer(topic: str, bootstrap_servers: str):
    consumer = AIOKafkaConsumer(topic, bootstrap_servers=bootstrap_servers)
    await consumer.start()
    print("Seller consumer started")
    try:
        async for message in consumer:
            try:
                seller_data = json.loads(message.value.decode('utf-8'))
                seller_df = prep.clean_seller([seller_data])
                
                sellers_headers = seller_df.columns
                for _, row in seller_df.iterrows():
                    row = row.copy()
                    row = row.where(pd.notna(row), None)
                    
                    seller = Seller(**row.to_dict())
                    
                    cursor.execute(
                        f"INSERT INTO seller ({', '.join(sellers_headers)}) VALUES ({', '.join(['%s'] * len(sellers_headers))})",
                        tuple(getattr(seller, col) for col in sellers_headers)
                    )

                conn.commit()
            except Exception as e:
                print(f"Error adding seller: {e}")
                conn.rollback()
    finally:
        await consumer.stop()
     

async def main():
    phone_task = asyncio.create_task(phone_consumer("phone_listings", "localhost:9092"))
    seller_task = asyncio.create_task(seller_consumer("seller_listings", "localhost:9092"))

    await asyncio.gather(phone_task, seller_task)

    cursor.close()
    conn.close()

asyncio.run(main())

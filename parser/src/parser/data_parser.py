import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
from kafka import KafkaProducer
import psycopg2
import json

from src.parser.models import Product, Seller
from src.parser.parser import parse_avito_page
from src.parser.tools import get_ad_urls

URL_TEMPLATE = "https://www.avito.ru/sankt-peterburg/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?p="
PAUSE_DURATION_SECONDS = 2
NUM_PAGES = 2

# Kafka producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def send_phone(data):
    producer.send("phone_listings", value=data)
    producer.flush()

def send_seller(data):
    producer.send("seller_listings", value=data)
    producer.flush()

def get_parsing_pages(output_folder):

    start_page_number = 1
    end_page_number = start_page_number + NUM_PAGES

    print(f"Начнем парсинг со страницы номер: {start_page_number} (вкл)")
    print(f"Закончим парсинг на странице номер: {end_page_number} (не вкл)")

    return start_page_number, end_page_number

def parse_pages(output_folder, driver, start_page_number, end_page_number):
    conn = psycopg2.connect("dbname=mydatabase user=myuser password=mypassword host=localhost port=5432")
    cursor = conn.cursor()

    cursor.execute("SELECT link FROM product")
    product_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT seller_id FROM seller")
    seller_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    for page_num in range(start_page_number, end_page_number):
        print(f"Начали парсинг страницы # {page_num}")
        try:
            # Загрузка страницы с объявлениями
            url = URL_TEMPLATE + str(page_num)
            driver.get(url)
            time.sleep(PAUSE_DURATION_SECONDS)

            # Получаем HTML-код страницы
            soup = BeautifulSoup(driver.page_source, 'html.parser')
    
            # Извлекаем ссылки на объявления на текущей странице
            links = get_ad_urls(soup)
            for link in tqdm(links):
                # check if link is already in the database
                if link in product_ids:
                    continue
                try:
                    # Переход на страницу объявления
                    driver.get(link)
                    time.sleep(PAUSE_DURATION_SECONDS)  # Задержка для полной загрузки

                    # Парсим данные на странице объявления (название, цена, фото, описание и т.д.)
                    ad_data, seller_data, done_deals_data = parse_avito_page(driver=driver) # <- словарик 
                    ad_data['link'] = link
                    
                    # Validate with Pydantic
                    product = Product.model_validate(ad_data)
                    seller = Seller.model_validate(seller_data)
                    
                    product_ids.append(link)
                    send_phone(product.model_dump())
                    if seller_data['seller_id'] not in seller_ids:
                        seller_ids.append(seller_data['seller_id'])
                        send_seller(seller.model_dump())

                        done_deals_list = [Product.model_validate(deal) for deal in done_deals_data]
                        for deal in done_deals_list:
                            send_phone(deal.model_dump())
                
                except TimeoutException:
                    print(f"Ошибка: объявление {link} не загрузилось, пропускаем...")
                    continue
                except Exception as e:
                    print(f"Произошла ошибка при обработке объявления {link}: {e}")
                    continue
        except TimeoutException:
            print(f"Ошибка: страница {page_num} не загрузилась, пропускаем...")
            continue
        except Exception as e:
            print(f"Произошла ошибка на странице {page_num}: {e}")
            continue

def parse_data():
    options = webdriver.FirefoxOptions()
    # options.add_argument("--headless")
    driver = webdriver.Remote(options=options, command_executor='http://selenium-firefox:4444')

    output_folder = "/home/airflow/parser/data8"
    start_page_number, end_page_number = get_parsing_pages(output_folder)
    parse_pages(output_folder, driver, start_page_number, end_page_number)    

    driver.quit()
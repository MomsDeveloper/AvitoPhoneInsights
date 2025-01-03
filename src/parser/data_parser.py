import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session, session
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm
from webdriver_manager.firefox import GeckoDriverManager

from src.db import ProductTable, SellerTable, SessionLocal, engine
from src.parser.models import Product, Seller
from src.parser.parser import parse_avito_page
from src.parser.tools import get_ad_urls, get_photos

URL_TEMPLATE = "https://www.avito.ru/sankt-peterburg/telefony/mobilnye_telefony/apple-ASgBAgICAkS0wA3OqzmwwQ2I_Dc?p="
PAUSE_DURATION_SECONDS = 2
NUM_PAGES = 100


def get_parsing_pages(output_folder):

    os.makedirs(output_folder, exist_ok=True)

    # Получаем список всех файлов в папке
    files = os.listdir(output_folder)

    # Ищем файлы с расширением .csv и извлекаем числовые части
    numbers = []
    for file in files:
        if file.endswith('.parquet'):
            match = re.search(r'\d+', file)
            if match:
                numbers.append(int(match.group()))

    # Находим максимальное число
    max_number = max(numbers) if numbers else None
    print(f"Максимальный номер: {max_number}")


    if not max_number: 
        start_page_number = 1
    else: 
        start_page_number = max_number + 1

    end_page_number = start_page_number + NUM_PAGES

    print(f"Начнем парсинг со страницы номер: {start_page_number} (вкл)")
    print(f"Закончим парсинг на странице номер: {end_page_number} (не вкл)")

    return start_page_number, end_page_number

def parse_pages(output_folder, driver, start_page_number, end_page_number):
    db_session = SessionLocal()

    product_ids = db_session.query(ProductTable.link).all()
    product_ids = [id[0] for id in product_ids]

    seller_ids = db_session.query(SellerTable.seller_id).all()
    seller_ids = [id[0] for id in seller_ids]

    product_columns = [
    'title', 'price', 'characteristics', 
    'description', 'views', 'date',
    'location', 'link', 'seller_id', 'today_views'
    , 'about', 'is_sold'
    ]

    seller_columns = [
        'seller_id', 'name', 'rating', 'reviews',
        'subscribers', 'subscriptions', 'registered', 
        'done_deals', 'active_deals', 'docs_confirmed',
        'phone_confirmed', 'response_time'
    ]

    for page_num in range(start_page_number, end_page_number):
        
        print(f"Начали парсинг страницы # {page_num}")

        df_page = pd.DataFrame(columns=product_columns)
        df_seller = pd.DataFrame(columns=seller_columns)
        
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
                    db_session.add(ProductTable(**product.model_dump()))
                    df_page = pd.concat([df_page, pd.DataFrame([ad_data])], ignore_index=True)
                    if seller_data['seller_id'] not in seller_ids:
                        seller_ids.append(seller_data['seller_id'])
                        db_session.add(SellerTable(**seller.model_dump()))
                        df_seller = pd.concat([df_seller, pd.DataFrame([seller_data])], ignore_index=True)

                        done_deals_list = [Product.model_validate(deal) for deal in done_deals_data]
                        for deal in done_deals_list:
                            db_session.add(ProductTable(**deal.model_dump()))
                        for deal in done_deals_data:
                            df_page = pd.concat([df_page, pd.DataFrame([deal])], ignore_index=True)

                except TimeoutException:
                    print(f"Ошибка: объявление {link} не загрузилось, пропускаем...")
                    continue
                except Exception as e:
                    print(f"Произошла ошибка при обработке объявления {link}: {e}")
                    continue

            db_session.commit()
            # Сохраняем данные для текущей страницы в DataFrame
            df_page.to_parquet(f'{output_folder}/phones_data_page_{page_num}.parquet')
            df_seller.to_parquet(f'{output_folder}/sellers_data_page_{page_num}.parquet')
        except TimeoutException:
            print(f"Ошибка: страница {page_num} не загрузилась, пропускаем...")
            continue
        except Exception as e:
            print(f"Произошла ошибка на странице {page_num}: {e}")
            continue

    db_session.close()

def parse_data():
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Remote(options=options, command_executor='http://selenium-firefox:4444')

    output_folder = "/home/airflow/src/parser/data8"
    start_page_number, end_page_number = get_parsing_pages(output_folder)
    parse_pages(output_folder, driver, start_page_number, end_page_number)    

    driver.quit()
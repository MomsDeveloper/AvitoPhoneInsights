import pandas as pd
import time
import os
import re

from tqdm import tqdm

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from webdriver_manager.firefox import GeckoDriverManager
from tools import get_ad_urls, get_photos
from parser import parse_avito_page

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
    columns = [
    'title', 'price', 'characteristics', 
    'description', 'views', 'date', 'rating',
    'location', 'link'
    ]
    for page_num in range(start_page_number, end_page_number):
        
        print(f"Начали парсинг страницы # {page_num}")

        df_page = pd.DataFrame(columns=columns)
        
        try:
            # Загрузка страницы с объявлениями
            url = URL_TEMPLATE + str(page_num)
            driver.get(url)
            time.sleep(PAUSE_DURATION_SECONDS)

            # Получаем HTML-код страницы
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
    
            # Извлекаем ссылки на объявления на текущей странице
            links = get_ad_urls(soup)

            for link in tqdm(links):
                
                try:
                    # Переход на страницу объявления
                    driver.get(link)
                    time.sleep(PAUSE_DURATION_SECONDS)  # Задержка для полной загрузки

                    # Парсим данные на странице объявления (название, цена, фото, описание и т.д.)
                    ad_data = parse_avito_page(driver=driver) # <- словарик 
                    ad_data['link'] = link
                    # ad_data['photo'] = get_photos(driver=driver, cnt=5)

                    df_page = pd.concat([df_page, pd.DataFrame([ad_data])], ignore_index=True)

                    
                except TimeoutException:
                    print(f"Ошибка: объявление {link} не загрузилось, пропускаем...")
                    continue
                except Exception as e:
                    print(f"Произошла ошибка при обработке объявления {link}: {e}")
                    continue

            # Сохраняем данные для текущей страницы в DataFrame
            df_page.to_parquet(f'{output_folder}/phones_data_page_{page_num}.parquet')

        except TimeoutException:
            print(f"Ошибка: страница {page_num} не загрузилась, пропускаем...")
            continue
        except Exception as e:
            print(f"Произошла ошибка на странице {page_num}: {e}")
            continue

def parse_data():
    # service = Service(GeckoDriverManager().install())
    options = webdriver.FirefoxOptions()
    # service = Service(ChromeDriverManager().install())
    # options = webdriver.ChromeOptions()

    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Remote(options=options, command_executor='http://selenium-firefox:4444')
    # driver = webdriver.Chrome(service=service, options=options)

    output_folder = "data8"
    start_page_number, end_page_number = get_parsing_pages(output_folder)
    parse_pages(output_folder, driver, start_page_number, end_page_number)    

    driver.quit()
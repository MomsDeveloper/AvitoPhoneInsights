import time
import requests

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_ad_urls(soup): 
    return [
        "https://www.avito.ru" + a['href']
        for a in soup.find_all('a', class_=lambda x: x and 'iva-' in x, href=True)
    ]


def save_photo(photo_url, photo_name):
    response = requests.get(photo_url)
    with open(photo_name, 'wb') as file:
        file.write(response.content)
        
        
def get_photos(driver, cnt=5): 
    photo_urls = []

    for i in range(cnt): 
        # Получаем текущий HTML-код страницы
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Парсим URL изображения
        try:
            photo_tag = soup.find('img', class_=lambda x: x and 'desktop' in x)
            if photo_tag and 'src' in photo_tag.attrs:
                photo_url = photo_tag['src']
                photo_urls.append(photo_url)
            else:
                print("Фото не найдено на этом этапе.")
        
        except Exception as e:
            print(f"Ошибка при парсинге URL фото: {e}")

        # Нажимаем на кнопку для переключения фотографии
        try:
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(@class, 'image-frame-controlButton_right')]"))
            )
            button.click()
            time.sleep(1)  # Задержка между кликами
        except Exception as e:
            print(f"Ошибка при нажатии на кнопку: {e}")
            break  # Прерываем цикл, если не удается нажать на кнопку

    return photo_urls

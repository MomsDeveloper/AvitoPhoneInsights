from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.by import By
import re
import uuid

PAUSE_DURATION_SECONDS = 2  # Define the pause duration in seconds

def parse_avito_page(driver): 
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    res = {}
    seller_data = {}

    try:
        title = soup.find('h1', {'data-marker': 'item-view/title-info'}).text
        res['title'] = title
    except AttributeError:
        pass
    
    # Парсинг цены
    try:
        price_tag = soup.find('span', {'data-marker': 'item-view/item-price'})
        if price_tag and 'content' in price_tag.attrs:
            price = price_tag['content']
            res['price'] = price
        else:
            print("Цена не найдена")
    except AttributeError:
        pass
    
    # Парсинг описания
    try:
        description_div = soup.find('div', {'data-marker': 'item-view/item-description'})
        description = description_div.find('p').get_text(strip=True)
        res['description'] = description
    except AttributeError:
        pass
    
    # Парсинг расположения
    try:
        location = soup.find('span', class_=lambda x: x and 'style-item-address__string' in x).get_text(strip=True)
        res['location'] = location
    except AttributeError:
        pass

    # Парсинг просмотров 
    try:
        views = soup.find('span', {'data-marker': 'item-view/total-views'}).text
        res['views'] = views
    except AttributeError:
        pass

    # Парсинг просмотров за сегодня
    try:
        views = soup.find('span', {'data-marker': 'item-view/today-views'}).text
        res['today_views'] = views
    except AttributeError:
        pass

    # Парсинг даты публикации
    try:
        date = soup.find('span', {'data-marker': 'item-view/item-date'}).text
        res['date'] = date
    except AttributeError:
        pass

    # Парсинг оценки продавца
    try:
        rating = soup.find('div', {'data-marker': 'item-view/seller-info'})
        if rating:
            rating = rating.find('span', class_=lambda x: x and 'styles-module-size_m-n6S6Y' in x).text
            res['rating'] = rating
        else:
            print("Оценка продавца не найдена")

    except AttributeError:
        pass

    # Парсинг о смартфоне
    res['about'] = parse_about(soup) 
    # Парсинг характеристик
    res['characteristics'] = parse_characteristics(soup)

    # Парсинг ссылки на продавца
    try:
        seller_link = soup.find('a', {'data-marker': 'seller-link/link'})
        if seller_link:
            seller_link = seller_link['href']
            if seller_link and not seller_link.startswith('https://www.avito.ru'):
                seller_link = 'https://www.avito.ru' + seller_link

            driver.get(seller_link)
            time.sleep(PAUSE_DURATION_SECONDS)
            seller_data = parse_seller_page(driver)
            seller_id = re.search(r'\/brands\/\w+', seller_link).group()
            seller_data['seller_id'] = seller_id 
                    
        else:
            seller_data = parse_seller_without_page(soup)            
            # Генерация уникального идентификатора продавца
            seller_data['seller_id'] = str(uuid.uuid4())

        res['seller_id'] = seller_data['seller_id']
    except AttributeError:
        pass
        
    return res, seller_data
    
def parse_section(soup, section_title):
    data = {}
    try:
        section = soup.find('h2', string=section_title).find_next('ul')
        items = section.find_all('li')
        for item in items:
            key = item.find("span").text
            value = item.text.replace(key, '').strip()
            key = key.replace(':', '').strip()
            if key and value:
                data[key] = value 
    except AttributeError:
        return None    

    return data

# Парсинг характеристик
def parse_characteristics(soup):
    return parse_section(soup, 'Характеристики')

# Парсинг о смартфоне
def parse_about(soup):
    return parse_section(soup, 'О смартфоне')

def parse_seller_page(driver):
    try:
        show_more_button = driver.find_element(By.CLASS_NAME, "Collapse-module-showMoreButton-EuQUL")
        show_more_button.click()
        time.sleep(PAUSE_DURATION_SECONDS)
    except Exception:
        pass

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    seller_data = {}

    try:
        name = soup.find('h1').text
        seller_data['name'] = name
    except AttributeError:
        pass

    # Парсинг оценки продавца
    try:
        rating = soup.find('span', {'data-marker': 'profile/score'}).text
        seller_data['rating'] = rating
    except AttributeError:
        pass
    
    # Парсинг количества отзывов
    try:
        reviews = soup.find('a', {'data-marker': 'profile/summary'}).text
        seller_data['reviews'] = reviews
    except AttributeError:
        pass
    
    # Парсинг количества подписчиков и подписок
    try:
        subs = soup.find('p', {'data-marker': 'favorite-seller-counters'}).text
        subs = re.findall(r'\d+', subs)
        seller_data['subscribers'] = subs[0]
        seller_data['subscriptions'] = subs[1]
    except AttributeError:
        pass

    # Парсинг даты регистрации
    try:
        registered = soup.find('p', {'data-marker': 'registered'}).text
        seller_data['registered'] = registered
    except AttributeError:
        pass

    # Парсинг времени ответа
    try:
        response_time = soup.find('p', {'data-marker': 'answer-time'}).text
        seller_data['response_time'] = response_time
    except AttributeError:
        pass

    # Парсинг количества сделок
    try:
        active_count = soup.find('span', string="Активные").find_next('span').text
        done_count = soup.find('span', string="Завершённые").find_next('span').text
        seller_data['active_deals'] = active_count
        seller_data['done_deals'] = done_count
    except AttributeError:
        pass
    
    # Парсинг подтверждения документов
    docs_confirmed = soup.find('div', string="Документы проверены")
    if docs_confirmed:
        seller_data['docs_confirmed'] = True
    else:
        seller_data['docs_confirmed'] = False
    
    # Парсинг подтверждения телефона
    phone_confirmed = soup.find('div', string="Телефон подтверждён")
    if phone_confirmed:
        seller_data['phone_confirmed'] = True
    else:
        seller_data['phone_confirmed'] = False
    
    return seller_data

def parse_seller_without_page(soup):
    seller_data = {}

    seller_data['name'] = 'Unknown'
    # Парсинг оценки продавца
    try:
        rating = soup.find('div', {'class': 'seller-info-rating'}).span.text
        seller_data['rating'] = rating
                        
    except AttributeError:
        pass
    
    # Парсинг количества отзывов
    try:
        reviews = soup.find('a', {'data-marker': 'rating-caption/rating'}).span.text
        seller_data['reviews'] = reviews
    except AttributeError:
        pass
    
    # Парсинг подтверждения документов
    docs_confirmed = soup.find('div', string="Документы проверены")
    if docs_confirmed:
        seller_data['docs_confirmed'] = True
    else:
        seller_data['docs_confirmed'] = False
    
    # Парсинг подтверждения телефона
    phone_confirmed = soup.find('div', string="Телефон подтверждён")
    if phone_confirmed:
        seller_data['phone_confirmed'] = True
    else:
        seller_data['phone_confirmed'] = False

    # Парсинг времени ответа
    try:
        response_time = soup.find('div', {'class': 'style-sellerInfoReplyTime-EdRsf'}).p.text
        seller_data['response_time'] = response_time
    except AttributeError:
        pass
    
    return seller_data
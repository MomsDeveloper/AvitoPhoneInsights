import datetime
from bs4 import BeautifulSoup
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import re
import uuid

PAUSE_DURATION_SECONDS = 1  # Define the pause duration in seconds

def parse_avito_page(driver): 
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    res = {
        'link': None,
        'title': None,
        'price': None,
        'description': None,
        'location': None,
        'views': None,
        'today_views': None,
        'date': None,
        'seller_id': None,
        'about': None,
        'characteristics': None,
        'is_sold': False
    }

    seller_data = {}
    done_deals_list = []

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
        # delete all non-digit characters
        views = re.sub(r'\D', '', views)
        res['views'] = views
    except AttributeError:
        pass

    # Парсинг просмотров за сегодня
    try:
        views = soup.find('span', {'data-marker': 'item-view/today-views'}).text
        # delete all non-digit characters
        views = re.sub(r'\D', '', views)
        res['today_views'] = views
    except AttributeError:
        pass

    # Парсинг даты публикации
    try:
        date = soup.find('span', {'data-marker': 'item-view/item-date'}).text
        res['date'] = date
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
            seller_data, done_deals_list = parse_seller_page(driver)
            seller_id = re.search(r'\/brands\/\w+', seller_link).group()
            seller_data['seller_id'] = seller_id 
                    
        else:
            seller_data = parse_seller_without_page(soup)            
            # Генерация уникального идентификатора продавца
            seller_data['seller_id'] = str(uuid.uuid4())

        res['seller_id'] = seller_data['seller_id']
    except AttributeError:
        pass

    for deal in done_deals_list:
        deal['seller_id'] = res['seller_id']

    return res, seller_data, done_deals_list
    
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
    seller_data = {
        'name': None,
        'rating': None,
        'reviews': None,
        'subscribers': None,
        'subscriptions': None,
        'registered': None,
        'done_deals': None,
        'active_deals': None,
        'docs_confirmed': None,
        'phone_confirmed': None,
        'response_time': None
    }
    done_deals_list = []    

    try:
        name = soup.find('h1').text
        seller_data['name'] = name
    except AttributeError:
        pass

    # Парсинг оценки продавца
    try:
        rating = soup.find('span', {'data-marker': 'profile/score'}).text
        seller_data['rating'] = rating.replace(',', '.')
    except AttributeError:
        pass
    
    # Парсинг количества отзывов
    try:
        reviews = soup.find('a', {'data-marker': 'profile/summary'}).text
        # delete all non-digit characters
        reviews = re.sub(r'\D', '', reviews)
        seller_data['reviews'] = reviews
    except AttributeError:
        pass
    
    # Парсинг количества подписчиков и подписок
    try:
        subs = soup.find('p', {'data-marker': 'favorite-seller-counters'}).text
        subs = re.sub(r'\s+', '', subs)
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
        active_span = soup.find('span', string="Активные")
        done_span = soup.find('span', string="Завершённые")
        
        active_count = active_span.find_next('span').text if active_span else None
        done_count = done_span.find_next('span').text if done_span else None

        # delete all non-digit characters
        active_count = re.sub(r'\D', '', active_count)
        done_count = re.sub(r'\D', '', done_count)
        seller_data['active_deals'] = active_count
        seller_data['done_deals'] = done_count

        button = driver.find_element(By.XPATH, "//span[text()='Завершённые']/ancestor::button")
        
        ActionChains(driver).move_to_element(button).perform()
        button.click()

        if done_count and int(done_count) > 0:
            for _ in range(2):
                time.sleep(PAUSE_DURATION_SECONDS)
                done_deals_list.extend(parse_sold_iphones(driver))
                buttons = driver.find_elements(By.CLASS_NAME, "desktop-1iti18a")
                if len(buttons) > 1:
                    button = buttons[1]
                    if button.get_attribute('aria-disabled') == 'false':
                        button.click()
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
    
    return seller_data, done_deals_list

def parse_seller_without_page(soup):
    seller_data = {
        'name': None,
        'rating': None,
        'reviews': None,
        'subscribers': None,
        'subscriptions': None,
        'registered': None,
        'done_deals': None,
        'active_deals': None,
        'docs_confirmed': None,
        'phone_confirmed': None,
        'response_time': None
    }

    seller_data['name'] = 'Unknown'
    # Парсинг оценки продавца
    try:
        rating = soup.find('div', {'class': 'seller-info-rating'}).span.text
        seller_data['rating'] = rating.replace(',', '.')
                        
    except AttributeError:
        pass
    
    # Парсинг количества отзывов
    try:
        reviews = soup.find('a', {'data-marker': 'rating-caption/rating'}).span.text
        # delete all non-digit characters
        reviews = re.sub(r'\D', '', reviews)
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

def parse_sold_iphones(driver):
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    products = []

    # Locate all the product containers
    grid_container = soup.find('div', class_='ProfileItemsGrid-root-UoT_a')  # Adjust this class if needed
    if grid_container:
        products_divs = grid_container.find_all('div', recursive=False)
        for product in products_divs:
            res = {
                'link': None,
                'title': None,
                'price': None,
                'description': None,
                'location': None,
                'views': None,
                'today_views': None,
                'date': None,
                'seller_id': None,
                'about': None,
                'characteristics': None,
                'is_sold': True
            }
            try:
                # Check if the title contains "iPhone"
                title_element = product.find('p', {'itemprop': 'name'})
                if title_element:
                    title = title_element.text
                    res['title'] = title if title else None
                else:
                    continue

                # check using regex if title begins with 'iPhone' or other like iphone
                if not title or not re.match(r'iphone', title, re.IGNORECASE):
                    continue
                
                # Extract the price
                price_element = product.find('meta', itemprop='price')
                res['price'] = price_element['content'] if price_element else None

                date_element = product.find('div', class_='geo-root-zPwRk').find_next_sibling('p')
                res['date'] = date_element.text.strip() if date_element else None
                
                # check if delta between current date and date of publication is more than 1 year then create unique id
                if res['date'] and (res['date'][-4:].isdigit() and len(res['date'][-4:]) == 4) and datetime.datetime.now().year - int(res['date'][-4:]) > 1:
                    res['link'] = str(uuid.uuid4())
                else:
                    # Extract the link
                    link_tag = product.find("a", {'itemprop': 'url'})
                    res['link'] = link_tag['href'] if link_tag else None

                

                # Extract the location
                location_element = product.find('div', class_='geo-root-zPwRk').find('p')
                res['location'] = location_element.text.strip() if location_element else None

                # Append extracted data to products list
                products.append(res)  
                
            except Exception as e:
                print(f"Error parsing product: {e}")
     
    return products
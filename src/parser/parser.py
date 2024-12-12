from bs4 import BeautifulSoup

def parse_avito_page(driver): 

    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    res = {}
    
    try:
        title = soup.find('h1', {'data-marker': 'item-view/title-info'}).text
        res['title'] = title
    except AttributeError:
        print("Название не найдено")
    
    
    # Парсинг цены
    try:
        price_tag = soup.find('span', {'data-marker': 'item-view/item-price'})
        if price_tag and 'content' in price_tag.attrs:
            price = price_tag['content']
            res['price'] = price
        else:
            print("Цена не найдена")
    except AttributeError:
        print("Цена не найдена")

    # Парсинг характеристик
    try:
        # Находим <ul> с классом, который содержит 'params-paramsList'
        params_list = soup.find('ul', class_=lambda x: x and 'params-paramsList' in x)
    
        # Получаем текст всех <li> элементов внутри <ul>
        characteristics = [li.get_text(strip=True) for li in params_list.find_all('li')]
        res['characteristics'] = characteristics
    except AttributeError:
        print("Характеристики не найдены")

    # Парсинг описания
    try:
        description_div = soup.find('div', {'data-marker': 'item-view/item-description'})
        description = description_div.find('p').get_text(strip=True)
        res['description'] = description
    except AttributeError:
        print("Описание не найдено")
    
    # Парсинг расположения
    try:
        location = soup.find('span', class_=lambda x: x and 'style-item-address__string' in x).get_text(strip=True)
        res['location'] = location
    except AttributeError:
        print("Расположение не найдено")

    # Парсинг просмотров 
    try:
        views = soup.find('span', {'data-marker': 'item-view/total-views'}).text
        res['views'] = views
    except AttributeError:
        print("Просмотры не найдены")

    # Парсинг даты публикации
    try:
        date = soup.find('span', {'data-marker': 'item-view/item-date'}).text
        res['date'] = date
    except AttributeError:
        print("Дата не найдена")

    # Парсинг оценки продавца
    try:
        rating = soup.find('div', {'data-marker': 'item-view/seller-info'})
        if rating:
            rating = rating.find('span', class_=lambda x: x and 'styles-module-size_m-n6S6Y' in x).text
            res['rating'] = rating
        else:
            print("Оценка продавца не найдена")

    except AttributeError:
        print("Оценка продавца не найдена")

    return res
    

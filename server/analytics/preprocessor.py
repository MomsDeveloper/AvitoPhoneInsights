import json
import pandas as pd
from datetime import datetime
import re


month_map = {
    'января': 'January',
    'февраля': 'February',
    'марта': 'March',
    'апреля': 'April',
    'мая': 'May',
    'июня': 'June',
    'июля': 'July',
    'августа': 'August',
    'сентября': 'September',
    'октября': 'October',
    'ноября': 'November',
    'декабря': 'December'
}

def parse_timestamp(timestamp):
    cleaned = timestamp.replace(' · ', ' в ').replace('в ', '').strip()
    for ru_month, en_month in month_map.items():
        if ru_month in cleaned:
            cleaned = cleaned.replace(ru_month, en_month)
            break
    if 'сегодня' in cleaned:
        cleaned = cleaned.replace('сегодня', datetime.now().strftime('%d %B'))
    elif 'вчера' in cleaned:
        cleaned = cleaned.replace(
            'вчера', (datetime.now() - pd.Timedelta(days=1)).strftime('%d %B'))

    # check if year is not present (like 20...)
    if not cleaned[-4:].isdigit():
        # if day and month is 01-01 year is now
        current_month = datetime.now().month
        parsed_month = datetime.strptime(cleaned.split()[1], '%B').month
        if parsed_month > current_month:
            cleaned = cleaned + f' {datetime.now().year - 1}'
        else:
            cleaned = cleaned + f' {datetime.now().year}'
    try:
        return datetime.strptime(cleaned, '%d %B %H:%M %Y')
    except ValueError:
        try:
            return datetime.strptime(cleaned, '%d %B %Y')
        except ValueError:
            try:
                return datetime.strptime(cleaned, '%B %Y')
            except ValueError:
                return datetime.strptime(cleaned, '%B %H:%M %Y')




# Getting new features from characteristics of the data
def parse_characteristics(characteristics):
    if not characteristics:
        return None, None, None, None
    version = None
    is_pro = False
    is_max = False
    capacity = None

    version_match = re.search(
        r'\biphone ?(\d+)', characteristics['Модель'], re.IGNORECASE)
    if version_match:
        version = int(version_match.group(1))

    xr_match = re.search(r'\b\w+ ?[Xx][rR]?', characteristics['Модель'])
    if xr_match and not version:
        version = 10
    if version is None:
        print(f'Version in {characteristics["Модель"]} not found')

    is_pro_match = re.search(r'[pP]ro', characteristics['Модель'])
    if is_pro_match:
        is_pro = True

    is_max_match = re.search(r'Max', characteristics['Модель'])
    if is_max_match:
        is_max = True

    if re.search(
        r'1 ?[tTтТ][bBбБ]', characteristics['Встроенная память']):
        capacity = 1024
    else:
        capacity_match = re.search(
            r'(\d+) ?[gGtTгГтТ][bBбБ]', characteristics['Встроенная память'])
        if capacity_match:
            capacity = int(capacity_match.group(1))

    return version, is_pro, is_max, capacity


def parse_title(title):
    if not title:
        return None, None, None, None
    version = None
    is_pro = False
    is_max = False
    capacity = None

    version_match = re.search(r'\biphone ?(\d+)', title, re.IGNORECASE)
    if version_match:
        version = int(version_match.group(1))

    xr_match = re.search(r'\b\w+ ?[Xx][rR]?', title)
    if xr_match and not version:
        version = 10
    if version is None:
        print(f'Version in {title} not found')

    if "pro" in title.lower():
        is_pro = True

    if "max" in title.lower():
        is_max = True

    # capacity_match = re.search(r'(\d+) ?[gGtTгГтТ][bBбБ]', title)

    # if capacity_match:
    #     capacity = int(capacity_match.group(1))

    if re.search(r'1 ?[tTтТ][bBбБ]', title):
        capacity = 1024
    else:
        capacity_match = re.search(r'(\d+) ?[gGtTгГтТ][bBбБ]', title)
        if capacity_match:
            capacity = int(capacity_match.group(1))

    return version, is_pro, is_max, capacity


def parse_registered(timestamp):
    if timestamp is None:
        return None
    cleaned = timestamp.replace('На Авито с ', '').strip()

    for ru_month, en_month in month_map.items():
        if ru_month in cleaned:
            cleaned = cleaned.replace(ru_month, en_month)
            break

    try:
        return datetime.strptime(cleaned, '%d %B %Y')
    except ValueError:
        return datetime.strptime(cleaned, '%B %Y')


def clean_phone(phone_data):
    phone_df = pd.DataFrame(phone_data)

    # deserialize the characteristics and about from json
    phone_df['characteristics'] = phone_df['characteristics'].apply(
        lambda x: json.loads(x) if isinstance(x, str) else x)
    phone_df['about'] = phone_df['about'].apply(
        lambda x: json.loads(x) if isinstance(x, str) else x)
    phone_df.drop(columns=['_sa_instance_state'], inplace=True, errors='ignore')

    # · 13 декабря в 23:09 to datetime
    phone_df['date'] = phone_df['date'].apply(parse_timestamp)
    phone_df['date'].head()


    phone_df['version'], phone_df['is_pro'], phone_df['is_max'], phone_df['capacity'] = zip(
        *phone_df.apply(lambda x: parse_title(x['title']) if x['is_sold'] else parse_characteristics(x['characteristics']), axis=1))
    phone_df['price'] = phone_df.apply(
        lambda x: None if x['is_sold'] and x['price'] < 1000 else x['price'], axis=1)
    phone_df['condition'] = phone_df['about'].apply(
        lambda x: x.get('Состояние') if x else None)


    # phone_df['price_coeff'] = phone_df.groupby(['version', 'is_pro', 'is_max', 'capacity', 'condition'])[
    #     'price'].transform(lambda x: x / x.mean())

    return phone_df

def clean_seller(seller_data):
    seller_df = pd.DataFrame(seller_data)
    seller_df['registered'] = seller_df['registered'].apply(parse_registered)

    return seller_df
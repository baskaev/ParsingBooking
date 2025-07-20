import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import random

def parse_hotel_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    result = {
        'name': '',
        'address': '',
        'score': '',
        'score_text': '',
        'description': '',
        'surroundings': [],
        'restaurants': [],
        'attractions': [],
        'beaches': [],
        'transport': [],
        'airports': [],
        'facilities': [],
        'house_rules': {},
        'important_notes': []
    }

    # Название отеля
    name_tag = soup.find('h2', class_='d2fee87262')
    if name_tag:
        result['name'] = name_tag.get_text(strip=True)

    # Адрес
    address_tag = soup.find('span', class_='hp_address_subtitle')
    if address_tag:
        result['address'] = address_tag.get_text(strip=True)

    # Оценка
    score_tag = soup.find('div', class_='b5cd09854e')
    if score_tag:
        result['score'] = score_tag.get_text(strip=True)

    # Текстовая оценка
    score_text_tag = soup.find('div', class_='d8eab2cf7f')
    if score_text_tag:
        result['score_text'] = score_text_tag.get_text(strip=True)

    # Описание отеля
    desc_div = soup.find('div', {'data-capla-component-boundary': 'b-property-web-property-page/PropertyDescriptionDesktop'})
    if desc_div:
        desc_p = desc_div.find('p', {'data-testid': 'property-description'})
        if desc_p:
            result['description'] = desc_p.get_text(strip=True)

    # Окрестности и инфраструктура
    poi_blocks = soup.find_all('div', {'data-testid': 'poi-block'})
    for block in poi_blocks:
        title_div = block.find('div', class_='e7addce19e')
        if title_div:
            title = title_div.get_text(strip=True)
            items = []
            for li in block.find_all('li', class_='b0bf4dc58f'):
                name_div = li.find('div', class_='aa225776f2')
                distance_div = li.find('div', class_='b99b6ef58f')
                if name_div and distance_div:
                    items.append({
                        'name': name_div.get_text(strip=True),
                        'distance': distance_div.get_text(strip=True)
                    })
            if title == 'В окрестностях':
                result['surroundings'] = items
            elif title == 'Рестораны и кафе':
                result['restaurants'] = items
            elif title == 'Главные достопримечательности':
                result['attractions'] = items
            elif title == 'Пляжи в окрестностях':
                result['beaches'] = items
            elif title == 'Общественный транспорт':
                result['transport'] = items
            elif title == 'Ближайшие аэропорты':
                result['airports'] = items

    # Удобства отеля
    facility_groups = soup.find_all('div', {'data-testid': 'facility-group-container'})
    for group in facility_groups:
        title_div = group.find('div', class_='e7addce19e')
        if title_div:
            title = title_div.get_text(strip=True)
            facilities = []
            for li in group.find_all('li', class_='b0bf4dc58f'):
                facility_span = li.find('span', class_='f6b6d2a959')
                if facility_span:
                    facilities.append(facility_span.get_text(strip=True))
            result['facilities'].append({
                'group': title,
                'items': facilities
            })

    # Условия размещения
    rules_section = soup.find('section', id='policies')
    if rules_section:
        rule_blocks = rules_section.find_all('div', class_='b0400e5749')
        for block in rule_blocks:
            title_div = block.find('div', class_='e7addce19e')
            content_div = block.find('div', class_='b99b6ef58f')
            if title_div and content_div:
                result['house_rules'][title_div.get_text(strip=True)] = content_div.get_text(strip=True)

    # Важная информация
    notes_section = soup.find('section', id='important_info')
    if notes_section:
        notes_div = notes_section.find('div', class_='c85a1d1c49')
        if notes_div:
            for p in notes_div.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    result['important_notes'].append(text)

    return result


def get_hotel_links(search_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        hotel_links = []
        for link in soup.find_all('a', {'data-testid': 'title-link'}):
            href = link.get('href')
            if href and 'hotel' in href:
                hotel_links.append(urljoin('https://www.booking.com', href))
        return list(set(hotel_links))
    except Exception as e:
        print(f"Error getting hotel links: {e}")
        return []

def download_hotel_page(hotel_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(hotel_url, headers=headers)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error downloading hotel page {hotel_url}: {e}")
        return None

def scrape_and_save_hotels(search_url, output_file='hotels_data.xlsx'):
    hotel_links = get_hotel_links(search_url)
    if not hotel_links:
        print("No hotel links found")
        return

    all_hotel_data = []

    for i, link in enumerate(hotel_links, 1):
        print(f"Processing hotel {i}/{len(hotel_links)}: {link}")
        html_content = download_hotel_page(link)
        if not html_content:
            continue
        hotel_data = parse_hotel_page(html_content)
        hotel_data['url'] = link
        all_hotel_data.append(hotel_data)
        time.sleep(random.uniform(1, 3))

    df = pd.json_normalize(all_hotel_data)
    df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}")

# Запуск
if __name__ == "__main__":
    search_url = "https://www.booking.com/searchresults.ru.html?ss=Барселона"
    scrape_and_save_hotels(search_url)

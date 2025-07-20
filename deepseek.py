import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import time
import random

def parse_hotel_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    

    result = {
    'description': '',  # Описание отеля
    'surroundings': [],  # Места поблизости
    'restaurants': [],  # Рестораны и кафе
    'attractions': [],  # Достопримечательности
    'beaches': [],  # Пляжи
    'transport': [],  # Транспорт
    'airports': [],  # Аэропорты
    'facilities': [],  # Удобства отеля
    'house_rules': {},  # Правила отеля
    'important_notes': []  # Важная информация
    }
    
    # 1) Описание отеля
    desc_div = soup.find('div', {'data-capla-component-boundary': 'b-property-web-property-page/PropertyDescriptionDesktop'})
    if desc_div:
        desc_p = desc_div.find('p', {'data-testid': 'property-description'})
        if desc_p:
            result['description'] = desc_p.get_text(strip=True)
    
    # 2) Окрестности, рестораны, достопримечательности, пляжи, транспорт, аэропорты
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
                    item = {
                        'name': name_div.get_text(strip=True),
                        'distance': distance_div.get_text(strip=True)
                    }
                    items.append(item)
            
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
    
    # 3) Удобства
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
    
    # 4) Условия размещения
    rules_section = soup.find('section', id='policies')
    if rules_section:
        rules = {}
        
        # Извлекаем все блоки с правилами
        rule_blocks = rules_section.find_all('div', class_='b0400e5749')
        for block in rule_blocks:
            title_div = block.find('div', class_='e7addce19e')
            if title_div:
                title = title_div.get_text(strip=True)
                content_div = block.find('div', class_='b99b6ef58f')
                if content_div:
                    rules[title] = content_div.get_text(strip=True)
        
        result['house_rules'] = rules
    
    # 5) Важная информация
    notes_section = soup.find('section', id='important_info')
    if notes_section:
        notes_div = notes_section.find('div', class_='c85a1d1c49')
        if notes_div:
            for p in notes_div.find_all('p'):
                result['important_notes'].append(p.get_text(strip=True))
    
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
                hotel_links.append(href)
        
        return list(set(hotel_links))  # Удаляем дубликаты
    
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
    # Получаем ссылки на отели
    hotel_links = get_hotel_links(search_url)
    if not hotel_links:
        print("No hotel links found")
        return
    
    all_hotel_data = []
    
    for i, link in enumerate(hotel_links, 1):
        print(f"Processing hotel {i}/{len(hotel_links)}: {link}")
        
        # Скачиваем страницу отеля
        html_content = download_hotel_page(link)
        if not html_content:
            continue
        
        # Парсим данные
        hotel_data = parse_hotel_page(html_content)
        
        # Добавляем URL отеля в данные
        hotel_data['url'] = link
        
        all_hotel_data.append(hotel_data)
        
        # Пауза между запросами
        time.sleep(random.uniform(1, 3))
    
    # Преобразуем данные в DataFrame и сохраняем в XLSX
    df = pd.json_normalize(all_hotel_data)
    df.to_excel(output_file, index=False, encoding='utf-8')
    print(f"Data saved to {output_file}")

# Пример использования
if __name__ == "__main__":
    search_url = "https://www.booking.com/searchresults.ru.html?ss=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&ssne=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&ssne_untouched=%D0%91%D0%B0%D1%80%D1%81%D0%B5%D0%BB%D0%BE%D0%BD%D0%B0&label=yan104jc-1DCAEoggI46AdIM1gDaMIBiAEBmAEhuAEXyAEM2AED6AEBiAIBqAIDuALfz7TDBsACAdICJDExMDA0MmUxLTNmNWEtNGQwNC05ZDFlLTM3MzFlMmI5ZGYzMNgCBOACAQ&sid=f7c21921d8ed7f4dc3c8f3121ae3219a&aid=397643&lang=ru&sb=1&src_elem=sb&src=index&dest_id=-372490&dest_type=city&group_adults=2&no_rooms=1&group_children=0"
    scrape_and_save_hotels(search_url)
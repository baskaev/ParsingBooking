import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Настройка Selenium
def get_driver():
    options = Options()
    # options.add_argument('--headless')  # <=== УДАЛИ ЭТУ СТРОКУ!
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')  # открывать на весь экран
    return webdriver.Chrome(options=options)


# Загрузка страницы отеля
def download_hotel_page(url):
    driver = get_driver()
    try:
        driver.get(url)
        time.sleep(5)  # Ждём полной загрузки
        html = driver.page_source
        return html
    except Exception as e:
        print(f"Ошибка при загрузке страницы {url}: {e}")
        return None
    finally:
        driver.quit()


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
        'important_notes': [],
        'rooms': []  # <== ДОБАВЛЕНО
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

    # Описание
    desc_div = soup.find('div', {'data-capla-component-boundary': 'b-property-web-property-page/PropertyDescriptionDesktop'})
    if desc_div:
        desc_p = desc_div.find('p', {'data-testid': 'property-description'})
        if desc_p:
            result['description'] = desc_p.get_text(strip=True)

    # Окрестности
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

    # Удобства
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

    # 🛏 Номера (комнаты)
    room_blocks = soup.find_all('div', {'data-testid': 'roomloop-block'})
    for room in room_blocks:
        room_data = {}

        # Название комнаты
        title_tag = room.find('div', class_='c667c82436')
        if title_tag:
            room_data['title'] = title_tag.get_text(strip=True)

        # Цена
        price_tag = room.find('span', class_='f6431b446c fbfd7c1165')
        if price_tag:
            room_data['price'] = price_tag.get_text(strip=True)

        # Условия бронирования
        condition_tag = room.find('span', class_='db63693c62')
        if condition_tag:
            room_data['conditions'] = condition_tag.get_text(strip=True)

        if room_data:
            result['rooms'].append(room_data)

    return result


# Получение ссылок на отели (можно расширить пагинацией)
def get_hotel_links(search_url):
    driver = get_driver()
    try:
        driver.get(search_url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        hotel_links = []
        for link in soup.find_all('a', {'data-testid': 'title-link'}):
            href = link.get('href')
            if href and 'hotel' in href:
                hotel_links.append(urljoin('https://www.booking.com', href))
        return list(set(hotel_links))
    except Exception as e:
        print(f"Ошибка получения ссылок: {e}")
        return []
    finally:
        driver.quit()

# Главная функция
def scrape_and_save_hotels(search_url, output_file='hotels_data.xlsx'):
    hotel_links = get_hotel_links(search_url)
    if not hotel_links:
        print("Ссылки не найдены.")
        return

    all_data = []

    for i, link in enumerate(hotel_links, 1):
        print(f"[{i}/{len(hotel_links)}] Загружаю: {link}")
        html = download_hotel_page(link)
        if not html:
            continue
        data = parse_hotel_page(html)
        data['url'] = link
        all_data.append(data)
        time.sleep(random.uniform(1, 2.5))

    df = pd.json_normalize(all_data)
    df.to_excel(output_file, index=False)
    print(f"\n✅ Сохранено в файл: {output_file}")

# Пример запуска
if __name__ == '__main__':
    search_url = "https://www.booking.com/searchresults.ru.html?ss=Барселона"
    scrape_and_save_hotels(search_url)

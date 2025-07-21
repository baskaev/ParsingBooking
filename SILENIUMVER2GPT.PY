import time
import random
import json
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException



# Настройка драйвера Selenium
def get_driver():
    options = Options()

    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')


    return webdriver.Chrome(options=options)

def download_hotel_page(url):
    driver = get_driver()
    try:
        driver.get(url)
        time.sleep(2)  # даём немного времени на начальную загрузку

        # Плавно скроллим до конца, пока страница продолжает подгружать элементы
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_tries = 0
        while scroll_tries < 10:  # максимум 10 попыток скролла
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # подождать подгрузку

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_tries += 1  # ничего не изменилось, считаем как 1 попытку
            else:
                scroll_tries = 0  # сбрасываем счётчик, если что-то подгрузилось
                last_height = new_height

        return driver.page_source
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")
        return None
    finally:
        driver.quit()

def parse_all_hotel_data(html):
    from bs4 import BeautifulSoup
    import re

    result = {
        'name': None,
        'address': None,
        'description': None,
        'reviews': {},
        'landmarks': {},
        'amenities_text': {},
        'conditions': {},
        'notes': []
    }

    soup = BeautifulSoup(html, 'html.parser')

    # Название
    name_tag = soup.find('h2', class_=re.compile(r'.*pp-header__title.*'))
    if name_tag:
        result['name'] = name_tag.get_text(strip=True)

    # Адрес
    address_button = soup.select_one('div.b99b6ef58f.cb4b7a25d9')
    if address_button:
        result['address'] = address_button.get_text(strip=True)

    # Описание
    desc_tag = soup.select_one('p[data-testid="property-description"]')
    if desc_tag:
        result['description'] = desc_tag.get_text(strip=True)

    # Отзывы
    for review in soup.select('div[data-testid="review-subscore"]'):
        category = review.select_one('span.d96a4619c0')
        score = review.select_one('div.f87e152973')
        if category and score:
            try:
                result['reviews'][category.text.strip()] = float(score.text.replace(',', '.').strip())
            except ValueError:
                continue

    # Ориентиры
    for block in soup.select('div[data-testid="poi-block"]'):
        category_tag = block.select_one('div.e7addce19e')
        if not category_tag:
            continue
        category = category_tag.get_text(strip=True)
        landmarks = []
        for li in block.select('li.b0bf4dc58f'):
            name_div = li.select_one('div.aa225776f2')
            distance_div = li.select_one('div.b99b6ef58f')
            subtype = li.select_one('span.ea6d30da3a')
            if name_div and distance_div:
                name = name_div.get_text(strip=True)
                if subtype:
                    name = f"{subtype.get_text(strip=True)} {name}"
                landmarks.append({
                    'name': name,
                    'distance': distance_div.get_text(strip=True)
                })
        if landmarks:
            result['landmarks'][category] = landmarks


    amenities = []
    # это работаеееет!!!!!!!!!!!!! только надо обрезать Самые популярные удобства и услуги
    for ul in soup.find_all("ul"):
        if ul.has_attr("class") and len(ul["class"]) == 3:
            # Ищем li с 4 классами
            for li in ul.find_all("li"):
                if li.has_attr("class") and len(li["class"]) == 4:
                    # Берём просто весь текст из li (с вложенностями, без тегов)
                    text = li.get_text(separator=" ", strip=True)
                    if text:
                        amenities.append(text)
    result['amenities_text'] = ', '.join(amenities)

    # Условия размещения
    for section in soup.select('div[data-testid="property-section--content"]'):
        for block in section.select('div.b0400e5749'):
            title = block.select_one('div.e7addce19e')
            content_div = block.select_one('div.c92998be48')
            if not title or not content_div:
                continue
            for hidden in content_div.find_all(attrs={"aria-hidden": "true"}):
                hidden.decompose()
            section_title = title.get_text(strip=True)
            if section_title == 'Принимаемые способы оплаты':
                methods = []
                for img in content_div.select('img'):
                    if img.has_attr('alt'):
                        methods.append(img['alt'])
                for span in content_div.select('span.f323fd7e96'):
                    methods.append(span.get_text(strip=True))
                result['conditions'][section_title] = ', '.join(methods)
            else:
                result['conditions'][section_title] = content_div.get_text(" ", strip=True)

    # Примечания
    note_candidates = soup.select('div[data-testid="property-section--content"] p')
    result['notes'] = [p.get_text(strip=True).replace('\xa0', ' ') for p in note_candidates if p.get_text(strip=True)]

    return result

def scroll_to_bottom(driver, pause_time=2, max_failed_attempts=30):
    failed_attempts = 0
    last_height = driver.execute_script("return document.body.scrollHeight")

    while failed_attempts < max_failed_attempts:
        # 1. Пробуем просто проскроллить вниз
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height > last_height:
            last_height = new_height
            failed_attempts = 0  # всё ок — сбрасываем счётчик
            continue

        # 2. Скролл не помог — пробуем нажать кнопку
        try:
            button = driver.find_element(
                'xpath', '//button[.//span[contains(text(), "Загрузить больше результатов")]]'
            )
            if button.is_displayed():
                button.click()
                print("Кнопка 'Загрузить больше результатов' нажата")
                time.sleep(pause_time)
                new_height = driver.execute_script("return document.body.scrollHeight")

                if new_height > last_height:
                    last_height = new_height
                    failed_attempts = 0
                    continue

        except (NoSuchElementException, ElementClickInterceptedException):
            pass  # Кнопки нет или клик не сработал

        # 3. Если ни скролл, ни кнопка не сработали — увеличиваем счётчик неудач
        failed_attempts += 1
        print(f"Неудачная попытка #{failed_attempts}")

    print("Выходим: достигнут лимит попыток.")

# Получение ссылок на отели со страницы поиска
def get_hotel_links(search_url):
    driver = get_driver()
    try:
        driver.get(search_url)
        scroll_to_bottom(driver, pause_time=5)
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
def scrape_and_save_hotels(search_url, output_file='hotels_data.json'):
    hotel_links = get_hotel_links(search_url)
    if not hotel_links:
        print("Не удалось найти отели.")
        return

    all_data = []

    for i, link in enumerate(hotel_links, 1):

        # if i>5:
        #     break
        print(f"[{i}/{len(hotel_links)}] Загружается: {link}")
        html = download_hotel_page(link)
        if not html:
            continue
        data = parse_all_hotel_data(html)
        data['url'] = link
        all_data.append(data)
        time.sleep(random.uniform(1.2, 2.5))

    # Сохраняем в JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Сохранено в файл: {output_file}")

#запуск
if __name__ == '__main__':
    search_url = "https://www.booking.com/searchresults.ru.html?ss=Барселона"
    scrape_and_save_hotels(search_url)

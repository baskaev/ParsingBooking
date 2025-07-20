import time
import random
import json
import pandas as pd
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin


# Настройка драйвера Selenium
def get_driver():
    options = Options()

    # options.add_argument('--headless=new')  # Новый headless режим (важно!)
    # options.add_argument('--disable-gpu')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--enable-unsafe-webgpu')
    # options.add_argument('--enable-unsafe-swiftshader')
    # options.add_argument('--start-maximized')
    # options.add_argument('--disable-dev-shm-usage')


    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')


    return webdriver.Chrome(options=options)


# Загрузка HTML страницы отеля
# def download_hotel_page(url):
#     driver = get_driver()
#     try:

#         driver.get(url)
#         time.sleep(3)
#         driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#         time.sleep(2)

#         # driver.get(url)
#         # time.sleep(5)  # Ждём полной загрузки страницы

#         return driver.page_source
#     except Exception as e:
#         print(f"Ошибка при загрузке {url}: {e}")
#         return None
#     finally:
#         driver.quit()

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



# def parse_all_hotel_data(html):
#     """
#     Безопасно парсит все данные отеля из HTML-кода.

#     Args:
#         html (str): HTML-код страницы отеля

#     Returns:
#         dict: Распарсенные данные:
#             - name
#             - address
#             - description
#             - reviews
#             - landmarks
#             - amenities
#             - conditions
#             - notes
#     """
#     result = {
#         'name': None,
#         'address': None,
#         'description': None,
#         'reviews': {},
#         'landmarks': {},
#         'amenities': {},
#         'conditions': {},
#         'notes': []
#     }

#     soup = BeautifulSoup(html, 'html.parser')

#     # Название отеля (через regex для устойчивости)
#     name_match = re.search(r'<h2[^>]*class=".*?pp-header__title.*?">(.*?)</h2>', html)
#     if name_match:
#         result['name'] = name_match.group(1).strip()

#     # Адрес
#     address_div = soup.find('div', class_=['b99b6ef58f', 'cb4b7a25d9'])
#     if address_div:
#         result['address'] = address_div.get_text(strip=True)

#     # Описание
#     description_div = soup.find('div', class_='hp_desc_main_content')
#     if description_div:
#         desc_p = description_div.find('p', {'data-testid': 'property-description'})
#         if desc_p:
#             result['description'] = desc_p.get_text(strip=True)

#     # Отзывы по категориям
#     review_items = soup.find_all('div', {'data-testid': 'review-subscore'})
#     for item in review_items:
#         category = item.find('span', class_='d96a4619c0')
#         score = item.find('div', class_='f87e152973')
#         if category and score:
#             try:
#                 result['reviews'][category.get_text(strip=True)] = float(score.get_text(strip=True).replace(',', '.'))
#             except ValueError:
#                 continue

#     # Ориентиры
#     poi_blocks = soup.find_all('div', {'data-testid': 'poi-block'})
#     for block in poi_blocks:
#         title_tag = block.find('div', class_='e7addce19e')
#         if not title_tag:
#             continue
#         category = title_tag.get_text(strip=True)
#         items = []
#         for li in block.find_all('li', class_='b0bf4dc58f'):
#             name_div = li.find('div', class_='aa225776f2')
#             distance_div = li.find('div', class_='b99b6ef58f')
#             subtype_span = li.find('span', class_='ea6d30da3a')
#             if name_div and distance_div:
#                 name = name_div.get_text(strip=True)
#                 if subtype_span:
#                     name = f"{subtype_span.get_text(strip=True)} {name}"
#                 items.append({
#                     'name': name,
#                     'distance': distance_div.get_text(strip=True)
#                 })
#         result['landmarks'][category] = items

#     # Удобства
#     facility_groups = soup.find_all('div', {'data-testid': 'facility-group-container'})
#     for group in facility_groups:
#         category_tag = group.find('h3')
#         if not category_tag:
#             continue
#         category_name = category_tag.get_text(strip=True)
#         items = []
#         for li in group.find_all('li'):
#             name_span = li.find('span', class_='f6b6d2a959')
#             if name_span:
#                 name = name_span.get_text(strip=True)
#                 is_paid = bool(li.find('span', class_='f323fd7e96'))
#                 items.append({'name': name, 'is_paid': is_paid})
#         result['amenities'][category_name] = items

#     # Условия размещения
#     policy_container = soup.find('div', {'data-testid': 'property-section--content'})
#     if policy_container:
#         rule_blocks = policy_container.find_all('div', class_='b0400e5749')
#         for section in rule_blocks:
#             title_tag = section.find('div', class_='e7addce19e')
#             content_div = section.find('div', class_='c92998be48')
#             if not title_tag or not content_div:
#                 continue
#             title = title_tag.get_text(strip=True)
#             for hidden in content_div.find_all(attrs={'aria-hidden': 'true'}):
#                 hidden.decompose()
#             content = content_div.get_text(' ', strip=True)

#             # Особые случаи
#             if title == 'Кровати для детей':
#                 paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p')]
#                 content = '\n'.join(paragraphs)
#             elif title == 'Принимаемые способы оплаты':
#                 methods = []
#                 for img in content_div.find_all('img'):
#                     if img.has_attr('alt'):
#                         methods.append(img['alt'])
#                 for span in content_div.find_all('span', class_='f323fd7e96'):
#                     methods.append(span.get_text(strip=True))
#                 content = ', '.join(methods)

#             result['conditions'][title] = content

#     # Примечания (важная информация)
#     notes_section = soup.find('div', {'data-testid': 'property-section--content'})
#     if notes_section:
#         result['notes'] = [p.get_text(strip=True).replace('\xa0', ' ') for p in notes_section.find_all('p') if p.get_text(strip=True)]

#     return result

def parse_all_hotel_data(html):
    from bs4 import BeautifulSoup
    import re

    result = {
        'name': None,
        'address': None,
        'description': None,
        'reviews': {},
        'landmarks': {},
        # 'amenities': {},
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

    # # Удобства
    # for group in soup.select('div[data-testid="facility-group-container"]'):
    #     group_title = group.select_one('h3')
    #     if not group_title:
    #         continue
    #     group_name = group_title.get_text(strip=True)
    #     facilities = []
    #     for li in group.select('li'):
    #         name_tag = li.select_one('span.f6b6d2a959')
    #         if name_tag:
    #             name = name_tag.get_text(strip=True)
    #             is_paid = bool(li.select_one('span.f323fd7e96'))
    #             facilities.append({'name': name, 'is_paid': is_paid})
    #     if facilities:
    #         result['amenities'][group_name] = facilities

    # # Удобства — улучшенный способ (ищем блок с текстом "Удобства и услуги")
    # amenities_root = soup.find(lambda tag: tag.name in ['div', 'section'] and 'Удобства и услуги' in tag.get_text())
    # if amenities_root:
    #     for group in amenities_root.select('div[data-testid="facility-group-container"]'):
    #         title_tag = group.select_one('h3')
    #         if not title_tag:
    #             continue
    #         group_title = title_tag.get_text(strip=True)
    #         facilities = []
    #         for li in group.select('li'):
    #             name_tag = li.select_one('span.f6b6d2a959')
    #             if name_tag:
    #                 facility_name = name_tag.get_text(strip=True)
    #                 is_paid = bool(li.select_one('span.f323fd7e96'))
    #                 facilities.append({'name': facility_name, 'is_paid': is_paid})
    #         if facilities:
    #             result['amenities'][group_title] = facilities

    # result['amenities'] = {}

    # # Найдём все блоки с удобствами ПОЛУРАБОЧАЯ ВЕРСИЯ
    # for group in soup.select('div[data-testid="facility-group-container"]'):
    #     title_tag = group.select_one('h3')
    #     if not title_tag:
    #         continue
    #     group_title = title_tag.get_text(strip=True)
        
    #     facilities = []
    #     for li in group.select('li'):
    #         name_tag = li.select_one('span.f6b6d2a959')
    #         if name_tag:
    #             name = name_tag.get_text(strip=True)
    #             is_paid = bool(li.select_one('span.f323fd7e96'))
    #             facilities.append({'name': name, 'is_paid': is_paid})
        
    #     if facilities:
    #         result['amenities'][group_title] = facilities

    # # Ищем все контейнеры с удобствами
    # for group in soup.select('div[data-testid="facility-group-container"]'):
    #     title_tag = group.select_one('h3')
    #     if not title_tag:
    #         continue
    #     group_title = title_tag.get_text(strip=True)

    #     facilities = []
    #     for li in group.select('li'):
    #         # Основной способ
    #         name_tag = li.select_one('span.f6b6d2a959')
    #         if name_tag:
    #             facility_name = name_tag.get_text(strip=True)
    #         else:
    #             # Fallback: берём текст всего li, если span отсутствует
    #             facility_name = li.get_text(strip=True)

    #         if facility_name:
    #             is_paid = bool(li.select_one('span.f323fd7e96'))
    #             facilities.append({
    #                 'name': facility_name,
    #                 'is_paid': is_paid
    #             })

    #     if facilities:
    #         result['amenities'][group_title] = facilities


    # amenities = []
    # for li in soup.select('div[data-testid="facility-group-container"] li'):
    #     text = li.get_text(" ", strip=True)
    #     if text:
    #         amenities.append(text)

    # # Склеим их через запятую
    # result['amenities_text'] = ', '.join(amenities)


    # amenities = []

    # # Ищем заголовок "Удобства и услуги" и берём всё, что после него
    # amenities_section = soup.find(lambda tag: tag.name == "h2" and "Удобства и услуги" in tag.text)
    # if amenities_section:
    #     parent_section = amenities_section.find_parent("section")
    #     if parent_section:
    #         # Собираем все тексты, кроме кнопок и заголовков
    #         for item in parent_section.find_all(text=True):
    #             text = item.strip()
    #             if text and len(text.split()) > 1:  # отсеиваем короткий мусор
    #                 amenities.append(text)

    # result['amenities_text'] = ', '.join(set(amenities))  # убираем дубли


    # # soup = BeautifulSoup(html, 'html.parser')  # если ещё не сделано

    # # Собираем все li внутри блоков удобств (включая популярные, групповые и т.д.)
    # all_li = soup.select('div[data-testid*="facility"] li')

    # # Берём текст каждого li
    # amenities = []
    # for li in all_li:
    #     text = li.get_text(" ", strip=True)
    #     if text:
    #         amenities.append(text)

    # # Склеиваем удобства через запятую
    # result['amenities_text'] = ', '.join(amenities)


    amenities = []
    # # Находим все ul с тремя классами
    # for ul in soup.find_all("ul"):
    #     if ul.has_attr("class") and len(ul["class"]) == 3:
    #         # Внутри ul ищем li с четырьмя классами
    #         for li in ul.find_all("li"):
    #             if li.has_attr("class") and len(li["class"]) == 4:
    #                 # Вытаскиваем весь текст из li
    #                 text = li.get_text(strip=True)
    #                 if text:
    #                     amenities.append(text)
    # Ищем ul с 3 классами

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



# Получение ссылок на отели со страницы поиска
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
def scrape_and_save_hotels(search_url, output_file='hotels_data.json'):
    hotel_links = get_hotel_links(search_url)
    if not hotel_links:
        print("Не удалось найти отели.")
        return

    all_data = []

    for i, link in enumerate(hotel_links, 1):

        if i>5:
            break
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
    # df = pd.json_normalize(all_data)
    # df.to_excel(output_file, index=False)
    # print(f"\n✅ Сохранено в файл: {output_file}")


# Пример запуска
if __name__ == '__main__':
    search_url = "https://www.booking.com/searchresults.ru.html?ss=Барселона"
    scrape_and_save_hotels(search_url)

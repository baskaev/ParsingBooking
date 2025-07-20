from bs4 import BeautifulSoup
import re

def parse_all_hotel_data(html):
    """
    Парсит все данные отеля из HTML-кода, объединяя функционал всех 8 функций.
    
    Args:
        html (str): HTML-код страницы отеля
        
    Returns:
        dict: Словарь со всеми распарсенными данными:
            - name: название отеля
            - address: адрес
            - description: описание
            - reviews: отзывы по категориям
            - landmarks: ближайшие ориентиры
            - amenities: удобства
            - conditions: условия размещения
            - notes: примечания
    """
    result = {
        'name': None,
        'address': None,
        'description': None,
        'reviews': {},
        'landmarks': {},
        'amenities': {},
        'conditions': {},
        'notes': []
    }
    
    # 1. Парсинг названия отеля (регулярное выражение)
    name_match = re.search(r'<h2 class="ddb12f4f86 pp-header__title">(.*?)</h2>', html)
    if name_match:
        result['name'] = name_match.group(1).strip()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # 2. Парсинг адреса
    address_div = soup.find('div', class_=['b99b6ef58f', 'cb4b7a25d9'])
    if address_div:
        result['address'] = address_div.contents[0].strip()
    
    # 3. Парсинг описания
    description_div = soup.find('div', class_='hp_desc_main_content')
    if description_div:
        description_tag = description_div.find('p', {'data-testid': 'property-description'})
        if description_tag:
            result['description'] = description_tag.get_text(strip=True)
    
    # 4. Парсинг отзывов
    review_items = soup.find_all('div', {'data-testid': 'review-subscore'})
    for item in review_items:
        category_name = item.find('span', class_='d96a4619c0').text.strip()
        rating = item.find('div', class_='f87e152973').text.strip().replace(',', '.')
        result['reviews'][category_name] = float(rating)
    
    # 5. Парсинг ориентиров
    poi_blocks = soup.find_all('div', {'data-testid': 'poi-block'})
    for block in poi_blocks:
        category = block.find('div', class_='e7addce19e').get_text(strip=True)
        items = []
        for li in block.find_all('li', class_='b0bf4dc58f'):
            name = li.find('div', class_='aa225776f2').get_text(strip=True)
            subtype = li.find('span', class_='ea6d30da3a')
            if subtype:
                name = f"{subtype.get_text(strip=True)} {name}"
            distance = li.find('div', class_='b99b6ef58f').get_text(strip=True)
            items.append({'name': name, 'distance': distance})
        result['landmarks'][category] = items
    
    # 6. Парсинг удобств
    facility_groups = soup.find_all('div', {'data-testid': 'facility-group-container'})
    for group in facility_groups:
        category_name = group.find('h3').get_text(strip=True)
        items = []
        for item in group.find_all('li'):
            item_text = item.find('span', class_='f6b6d2a959').get_text(strip=True)
            paid_tag = item.find('span', class_='f323fd7e96')
            is_paid = paid_tag.get_text(strip=True) if paid_tag else None
            items.append({'name': item_text, 'is_paid': bool(is_paid)})
        result['amenities'][category_name] = items
    
    # 7. Парсинг условий размещения
    container = soup.find('div', {'data-testid': 'property-section--content'})
    if container:
        sections = container.find_all('div', class_='b0400e5749')
        for section in sections:
            title_div = section.find('div', class_='e7addce19e')
            if not title_div:
                continue
            title = title_div.get_text(strip=True)
            content_div = section.find('div', class_='c92998be48')
            if content_div:
                for hidden in content_div.find_all(attrs={'aria-hidden': 'true'}):
                    hidden.decompose()
                content = content_div.get_text(' ', strip=True)
                
                if title == 'Кровати для детей':
                    child_policies = []
                    for p in content_div.find_all('p'):
                        child_policies.append(p.get_text(strip=True))
                    content = '\n'.join(child_policies)
                elif title == 'Принимаемые способы оплаты':
                    payment_methods = []
                    for img in content_div.find_all('img'):
                        if img.has_attr('alt'):
                            payment_methods.append(img['alt'])
                    for span in content_div.find_all('span', class_='f323fd7e96'):
                        payment_methods.append(span.get_text(strip=True))
                    content = ', '.join(payment_methods)
                
                result['conditions'][title] = content
    
    # 8. Парсинг примечаний
    notes_section = soup.find('div', {'data-testid': 'property-section--content'})
    if notes_section:
        notes_paragraphs = notes_section.find_all('p')
        result['notes'] = [p.get_text(strip=True).replace('\xa0', ' ') for p in notes_paragraphs]
    
    return result
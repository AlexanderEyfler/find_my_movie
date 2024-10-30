import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import os

# url = 'https://kino.mail.ru/cinema/all/'

headers = {
    'Accept': '*/*',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0'
}

# req = requests.get(url)
# src = req.text
# print(src)

# with open('index.html', 'w') as file:
#     file.write(src)

# with open('index.html') as file:
#     src = file.read()


# base_url = 'https://kino.mail.ru/cinema/all/'
# total_pages = 200  # Укажите количество страниц для обработки

# all_films_dict = {}
# for page in range(1, total_pages + 1):
#     # Формируем URL для каждой страницы
#     if page == 1:
#         url = base_url  # Первая страница
#     else:
#         url = f'{base_url}?page={page}'  # Остальные страницы

#     print(f'Обрабатываем {url}')

#     # Получаем HTML контент страницы
#     response = requests.get(url)
#     if response.status_code != 200:
#         print(f'Ошибка при получении страницы: {response.status_code}')
#         continue  # Переходим к следующей итерации, если произошла ошибка

#     src = response.content
#     soup = BeautifulSoup(src, 'lxml')

#     # Находим все нужные элементы на странице
#     all_films_hrefs = soup.find_all(class_='link link_inline color_black link-holder link-holder_itemevent link-holder_itemevent_small')

#     # Извлекаем текст и ссылки
#     for item in all_films_hrefs:
#         item_text = item.text.strip()  # Удаляем лишние пробелы
#         item_href = 'https://kino.mail.ru' + item.get('href') if item.get('href') else 'Ссылка отсутствует'
        
#         # Добавляем текст и ссылку в словарь.
#         all_films_dict[item_text] = item_href

# # Записываем все собранные данные в JSON файл
# with open('all_films_dict.json', 'w', encoding='utf-8') as file:
#     json.dump(all_films_dict, file, indent=4, ensure_ascii=False)





with open('all_films_dict.json') as file:
    all_films = json.load(file)


csv_filename = 'all_data.csv'

# Проверка, сколько записей уже в CSV
existing_films = 0

if os.path.exists(csv_filename):
    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        existing_films = sum(1 for row in reader)  # Подсчитываем количество записей

# Открытие CSV для записи данных в режиме добавления
with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['film_name', 'IMDb', 'director', 'actors', 'image', 'description']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Записываем заголовок, только если файл пуст (если нет записей)
    if existing_films == 0:
        writer.writeheader()

    count = existing_films  # Начинаем с уже существующих записей

    for index, (film_name, film_href) in enumerate(all_films.items()):
        # Пропускаем уже обработанные фильмы
        if index < count:
            continue

        # Подготовка названия фильма
        rep = ['/']
        for item in rep:
            if item in film_name:
                film_name = film_name.replace(item, ' ')
        
        # Выполнение запроса
        req = requests.get(url=film_href, headers=headers)
        src = req.text

        # Сохранение HTML в файл
        with open(f'data/{count}_{film_name}.html', 'w', encoding='utf-8') as file:
            file.write(src)

        # Парсинг HTML
        soup = BeautifulSoup(src, 'lxml')

        # Получение описания фильма
        description = soup.select_one('.text.text_inline.text_light_medium.text_fixed.valign_baseline.p-movie-info__description-text')
        description_text = description.get_text(strip=True) if description else "Описание не найдено"

        # Получение имени режиссера
        director = soup.select_one('.p-movie-info__content .p-truncate__inner a')
        director_name = director.get_text(strip=True) if director else "Режиссер не найден"

        # Получение имен актеров
        actor_links = soup.select('.p-truncate__inner.js-toggle__truncate-inner a')
        actor_names = [actor.get_text(strip=True) for actor in actor_links]
        actor_names = ', '.join(actor_names) if actor_names else "Актеры не найдены"

        # Получение рейтинга
        rating_span = soup.find('div', class_='p-movie-rates__item p-movie-rates__item_border_left nowrap')
        rating = rating_span.find('span', class_='margin_left_10').get_text(strip=True) if rating_span else "Рейтинг не найден"

        # Получение URL изображения
        img_tag = soup.find('img', class_='picture__image picture__image_cover')
        img_url = img_tag['src'] if img_tag else "Изображение не найдено"

        # Запись в CSV
        writer.writerow({
            'film_name': film_name,
            'description': description_text,
            'director': director_name,
            'actors': actor_names,
            'IMDb': rating,
            'image': img_url
        })

        count += 1
        time.sleep(1)  # Задержка между запросами



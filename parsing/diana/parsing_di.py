# Импорты
from bs4 import BeautifulSoup
import csv
import requests
import json
import time
import random

# Чтение сайта
base_url = 'https://kino-lol.ws/'
headers = {
    'Accept' : '*/*',
    'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36'
}

req = requests.get(base_url, headers=headers)
src = req.text
# Сохраняем 1 страницу в файл
with open('index.html', 'w') as file:
    file.write(src)


# Общее количество страниц
total_pages = 450

# Список для хранения данных
all_shows = {}
all_categories = {}

# Цикл по страницам
for page in range(1, total_pages + 1):
    if page == 1:
        url = base_url
    else:
        url = f'{base_url}?page{page}'
    print(f'Обрабатываем {url}')

    response = requests.get(url, headers=headers)
#1-https://kino-lol.ws/
#2-https://kino-lol.ws/?page2
#3-https://kino-lol.ws/?page3

    # Проверяем статус ответа
    if response.status_code != 200:
        print(f'Ошибка при получении страницы {page}: {response.status_code}')
        continue  # Переходим к следующей странице

    # Создаём объект BeautifulSoup для парсинга HTML
    src = response.content
    soup = BeautifulSoup(response.content, 'lxml')

    # Находим все сериалы на странице
    shows = soup.find_all('div', class_='sh0titl')
    #print(shows)

    if not shows:
        #print(f'Сериалы не найдены на странице {page}')
        continue  # Переходим к следующей странице
    all_titles = []    
    # Цикл по сериалам на странице
    for idx, first_show in enumerate(shows, start=1):
        #print(f'  Обработка сериала {idx} на странице {page}')
        #print(first_show)

        # Извлечение ссылки на страницу сериала
        show_link =  first_show.find('a')
        #print(show_link)
        show_href = first_show.get('href') if show_link else None
        if show_link:
            show_href = show_link.get('href')  # Извлекаем 'href' из элемента 'a'
            if show_href:
                show_url = 'https://kino-lol.ws' + show_href
                # Извлечение названия сериала
                title = show_link.text.strip()  # Получаем текст из элемента 'a'
                #print(f"Название сериала: {title}") 

                #all_shows[title] = show_url

                # Добавляем название в список и убираем лишнее
                all_titles.append(title)
                for i in range(len(all_titles)):
                    title = all_titles[i]
                    title = title.replace(" (", "(").replace(")", "").split("(")[0].strip()
                    title = title.replace("\\", "_").replace("/", "_").replace("|", "_")
                    title = title.replace(":", "_").replace(" ", "_")
                    all_titles[i] = title

                all_shows[title] = show_url

            else:
                print('    Не удалось найти ссылку на сериал')
                continue  # Переходим к следующему сериалу
        else:
            print('    Не удалось найти ссылку на сериал')
            continue  # Переходим к следующему сериалу


# Сохраним результат в файл json:
with open('all_shows_3.json', 'w') as file:
    json.dump(all_shows, file, indent=4, ensure_ascii=False)

# Сохраним файл json в переменную:
with open('all_shows_3.json') as file:
    all_categories = json.load(file)
#print(all_categories)

with open('all_data_3.csv', 'w', newline='', encoding='utf-8') as f:
    filednames = ['film_name', 'gener', 'description', 'image_url', 'producor']
    writer = csv.DictWriter(f, fieldnames=filednames)
    writer.writeheader()
    
    count = 0
    for cat_name, cat_href in all_categories.items():
        req = requests.get(url=cat_href, headers=headers)
        src = req.text

        with open(f'/home/xuri/parsing/data_2/{count}_{cat_name}.html', "w") as file:
            file.write(src)
        
        with open(f"/home/xuri/parsing/data_2/{count}_{cat_name}.html") as file:
            src = file.read()

            soup = BeautifulSoup(src, 'lxml')
            
            # ЖАНР ФИЛЬМА
            gener = soup.find('div', class_='blockinfo').find('b', string='Жанр:')
            if gener:
                gener_text = gener.next_sibling.strip()
                #print(gener_text)

            # ОПИСАНИЕ ФИЛЬМА
            description = soup.find('div', class_='blockinfo').find_all('br')[-3].next_sibling
            if description:
                description_text = description.strip()
                #print(description_text)

            # URL ПОСТЕРА
            image_tag = soup.find('div', class_='poster').find('img')
            if image_tag:
                img_url = base_url + image_tag['src']  # Добавляем base_url к src
                #print(img_url)
            else:
                img_url = 'Изображение не найдено'

            # РЕЖИССЕР
            producor = soup.find('div', class_='blockinfo').find('b', string='Режиссер:')
            if producor:
                producors = producor.next_sibling.strip()

            # Переход на страницу сериала и получение описания
        count += 1
        
        writer.writerow({
                    'film_name' : cat_name,
                    'gener' : gener_text,
                    'description' : description_text,
                    'image_url' : img_url,
                    'producor' : producors
                })
        time.sleep(1)  # Задержка между запросами к страницам поиска
        
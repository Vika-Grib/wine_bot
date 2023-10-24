import requests
import telebot
from config import token
from bs4 import BeautifulSoup
from telebot import types
import logging
import openpyxl


def get_wine_class_name(url, wine_example):
    response = requests.get(url)
    soup1 = BeautifulSoup(response.content, 'html.parser') #cодержимое разбираем с помощью BeautifulSoup с парсером 'html.parser' для создания объекта soup1
    # print('soup1: ', soup1)
    if wine_example:
        tag = soup1.find(string=wine_example)
        print('TAG', tag)
        if tag:
            parent_tag = tag.parent
            print("*****", parent_tag, "*****")
            while parent_tag and not parent_tag.has_attr('class'):
                parent_tag = parent_tag.parent

            if parent_tag and parent_tag.has_attr('class'):
                print('PARENT_TAG!!! ', parent_tag)
                return parent_tag #элемент BeautifulSoup, представляющий родительский тег, содержащий имя вина и требуемый атрибут класса

            # Поиск внутри потомков
            if tag:
                parent_tag = tag.find_parent(class_=True)
                if parent_tag:
                    print('PARENT_TAG!!! (Descendant): ', parent_tag)
                    return parent_tag

    return None

def get_vivino_wines(url): # запрос быстрее работает быстрее парсера
    response = requests.get(url)
    current_page_wines = response.json()['explore_vintage']['matches']
    for wine in current_page_wines:
        print(wine)
    #print(response.json()['explore_vintage']['matches'][1])
get_vivino_wines('https://www.vivino.com/webapi/explore/explore?country_code=BY&currency_code=BYN&grape_filter=varietal&min_rating=1&order_by=ratings_average&order=desc&price_range_max=1000&price_range_min=0&wine_type_ids%5B%5D=1&wine_type_ids%5B%5D=2&wine_type_ids%5B%5D=3&wine_type_ids%5B%5D=4&wine_type_ids%5B%5D=24&wine_type_ids%5B%5D=7&page=1&language=en')



def collect_wine_names(url, parent_tag):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    wine_names_on_url_page = []
    parent_div = soup.find_all(parent_tag.name, class_=parent_tag.get('class'))
    i = 0
    while i in range(len(parent_div)): # меняем for на while
        parent = parent_div[i]
        print("PARENT: ", parent)
        wine_name = parent.find(string=True, recursive=False)
        if not wine_name:
            wine_name = parent.find('a')
            if wine_name:
                wine_name = wine_name.text.strip()
        else:
            wine_name = wine_name.strip()

        if wine_name:
            wine_names_on_url_page.append(wine_name)
            # print("wine_names_on_url_page\n", wine_names_on_url_page)
        i += 3

    return wine_names_on_url_page



# Функция для получения рейтинга вин от Vivino
def get_vivino_rating(wine_name):
    # URL страницы поиска Vivino с названием вина в качестве параметра запроса
    search_url = f"https://www.vivino.com/search/wines?q={wine_name}"
    # print(search_url)
    response = requests.get(search_url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'})

    if response.status_code == 200:
        wine_search_soup = BeautifulSoup(response.content, 'html.parser')
        # первый элемент вина в результатах поиска
        wine_element = wine_search_soup.find('div', class_='wine-card__content')
        # print("#" * 50)
        # print(wine_element)
        # print("#" * 50)
        #

        if wine_element:
            # нахождение рейтинга вина
            rating_element = wine_search_soup.find('div', class_='text-inline-block light average__number')
            if rating_element:
                rating_element_text = rating_element.get_text()
                # print('*' * 50)
                print('RATING' + rating_element_text)
                # print('*' * 50)
                return rating_element.text.strip()

    return None # Если получить рейтинг не удалось


# parent_tag = get_wine_class_name(url, wine_example)
# print("PARENT_TAG: \n", parent_tag)
#
# if parent_tag:
#     # собираем названия вин со страницы url
#     wine_names = collect_wine_names(url, parent_tag)
#     print('\n'.join(wine_names))
#
#     ratings = {}
#     for wine_name in wine_names:
#         rating = get_vivino_rating(wine_name)
#         ratings[wine_name] = rating
#     print(ratings)
# else:
#     print('Wine example not found on the page.')

# настройка журнала
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# создание бота
bot = telebot.TeleBot(token)

# команда старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! Please send me the URL of a wine page.")

@bot.message_handler(func=lambda message: True)
def process_message(message):
    if message.text.startswith('http'):
        url = message.text
        bot.send_message(message.chat.id, "Great! Now, please send me the name of the wine.")
        bot.register_next_step_handler(message, process_wine_name, url)
    else:
        bot.send_message(message.chat.id, "Please send valid URL.")

#функция для обработки URL-адреса винной страницы
# def process_wine_name(message, url):
#     wine_example = message.text
#     parent_tag = get_wine_class_name(url, wine_example)
#     print("PARENT_TAG: \n", parent_tag)
#     if parent_tag:
#         wine_names = collect_wine_names(url, parent_tag)
#         print('\n'.join(wine_names))
#
#         ratings = {}
#         for wine_name in wine_names:
#             rating = get_vivino_rating(wine_name)
#             ratings[wine_name] = rating if rating is not None else "Rating not found on Vivino"
#
#         response = generate_response(ratings)
#         bot.send_message(message.chat.id, response)
#     else:
#         bot.send_message(message.chat.id, "Wine example not found on the page! ")

def process_wine_name(message, url):
    wine_example = message.text
    parent_tag = get_wine_class_name(url, wine_example)
    print("PARENT_TAG: \n", parent_tag)
    if parent_tag:
        wine_names = collect_wine_names(url, parent_tag)
        print('\n'.join(wine_names))

        # Excel и активный лист
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        # Заголовки
        sheet['A1'] = 'Wine Name'
        sheet['B1'] = 'Rating'
        row_index = 2  # Начнем с 2 строки (после заголовков)
        print('Вина принт!', wine_names)

        for wine_name in wine_names:
            rating = get_vivino_rating(wine_name)
            if rating is not None:
                # Сохраните информацию о вине и рейтинге в Excel
                sheet.cell(row=row_index, column=1, value=wine_name)
                sheet.cell(row=row_index, column=2, value=rating)
                row_index += 1

        # Сохраняем файл Excel с данными о винах
        file_name = 'wine_data.xlsx'
        workbook.save(file_name)

        # Отправляем файл с данными о винах пользователю
        with open(file_name, 'rb') as file:
            bot.send_document(message.chat.id, file)

        ratings = {}
        for wine_name in wine_names:
            ratings[wine_name] = get_vivino_rating(wine_name) if get_vivino_rating(wine_name) is not None else "Rating not found on Vivino"

        response = generate_response(ratings)
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Wine example not found on the page! ")



# примеры!!!!
# url = 'https://8wines.com/wines'
# wine_example = 'El Enemigo Chardonnay 2020'

# url = 'https://www.thewinehouse.pl/oferta-win/'
# wine_example = 'Chablis 1er Cru Fourchaume AOC'



# Функция для генерации ответного сообщения с рейтингом вин
def generate_response(ratings):
    response = "Wine Ratings:\n"
    for wine_name, rating in ratings.items():
        if rating is not None:
            response += f"{wine_name} - {rating}\n"
        else:
            response += f"{wine_name} - Rating not found on Vivino\n"
    return response





# запускаем бота
bot.polling()



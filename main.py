import requests
import telebot
from config import token
from telebot import types
import logging
import openpyxl
import parser_BeautifulSoup as pB


def get_wine_names_from_api_vivino(url): # запрос работает быстрее парсера
    response = requests.get(url)
    current_page_wines = response.json()['explore_vintage']['matches']
    wine_list = []

    for wine in current_page_wines:
        print(wine)
        name = wine['vintage']['seo_name'].replace('-', ' ')
        rating = wine['vintage']['statistics']['ratings_average']
        wine_info = f"{name} - Rating: {rating}"
        wine_list.append(wine_info)

    for wine_info in wine_list:
        print(wine_info)

    return wine_list

    #print(response.json()['explore_vintage']['matches'][1])
#get_wine_names_from_api_vivino('https://www.vivino.com/webapi/explore/explore?country_code=BY&currency_code=BYN&grape_filter=varietal&min_rating=1&order_by=ratings_average&order=desc&price_range_max=1000&price_range_min=0&wine_type_ids%5B%5D=1&wine_type_ids%5B%5D=2&wine_type_ids%5B%5D=3&wine_type_ids%5B%5D=4&wine_type_ids%5B%5D=24&wine_type_ids%5B%5D=7&page=1&language=en')


row_index = 2  # Начнем с 2 строки (после заголовков) (чтобы какждый раз не обнулялась - выносим вне функции и делаем в функции глобальной, чтобы она каждый раз не сбрасывалась, а олин раз начала с 2 и дальше ув +1)

# Функция для обработки URL-адреса винной страницы
def excel_paste(page_num, sheet):
    global row_index, list_of_wines
   # url = f'https://www.vivino.com/webapi/explore/explore?country_code=PL&currency_code=PLN&grape_filter=varietal&min_rating=1&order_by=ratings_average&order=desc&price_range_max=120&price_range_min=30&wine_type_ids%5B%5D=1&wine_type_ids%5B%5D=2&page={page_num}&language=en'
    url = f'https://www.vivino.com/webapi/explore/explore?country_code=PL&currency_code=PLN&grape_filter=varietal&order_by=price&order=asc&wine_type_ids%5B%5D=1&wine_type_ids%5B%5D=2&wine_type_ids%5B%5D=3&wine_type_ids%5B%5D=4&wine_type_ids%5B%5D=5&wine_type_ids%5B%5D=6&wine_type_ids%5B%5D=7&wine_type_ids%5B%5D=&wine_type_ids%5B%5D=24&page={page_num}&language=en'
    wine_names_and_ratings = get_wine_names_from_api_vivino(url)  # Получаем имена и рейтинги вин с использованием API

    if wine_names_and_ratings:
        for wine_info in wine_names_and_ratings:
            wine_name, rating = wine_info.split(' - Rating: ') # разделяем информацию о вине на имя и рейтинг с помощью .split(' - Rating: '), а затем сохраняем их в файл Excel
            if wine_name in list_of_wines:
                continue

            sheet.cell(row=row_index, column=1, value=wine_name)
            sheet.cell(row=row_index, column=2, value=rating)
            row_index += 1
            print('new wine: ', wine_name)


list_of_wines = []

def parser():
    global list_of_wines, row_index

    file_name = 'wine_data.xlsx'
    start_page = 1
    last_page = 81
    # Excel и активный лист
    workbook = openpyxl.load_workbook(file_name)  # нужно чтобы открылась таблица ДО парсера, а закрывалась уже только после парсера всех страниц
    sheet = workbook.active

    # Заголовки
    sheet['A1'] = 'Wine Name'
    sheet['B1'] = 'Rating'

    column_A = sheet['A']
    for elem in range(len(column_A)):
        list_of_wines.append(column_A[elem].value) # value - значение ячейки, а не сама ячейка

    row_index = len(list_of_wines) + 1  # определяет последнее значение - то есть записываются вина и после 2026
                                        # - следуующие будут дозаписываться уже начиная с 2027

    for page in range(start_page, last_page+1):
        excel_paste(page, sheet)

    # Сохраняем файл Excel с данными о винах
    workbook.save(file_name)
#parser()

# настройка журнала
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# создание бота
bot = telebot.TeleBot(token)

# команда старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! Please send me the URL of a wine page.")


send_url = False
url = ''


@bot.message_handler(func=lambda message: True)
def process_message(message):
    global url, send_url
    if send_url:
        wine_class_name = pB.get_wine_class_name(message, url)
        print("wcm: ", wine_class_name)
        wine_page_list = pB.collect_wine_names(url, wine_class_name)
        rating_page_list = []
        for wine in wine_page_list:
            rating_page_list.append(pB.get_vivino_rating(wine))
        response = pB.generate_response(wine_page_list, rating_page_list)
        bot.send_message(message.chat.id, response)
        send_url = False
    elif message.text.startswith('http'):
        url = message.text
        bot.send_message(message.chat.id, "Great! Now, please send me the name of the wine.")
        send_url = True
    else:
        bot.send_message(message.chat.id, "Please send valid URL.")




# запускаем бота
bot.polling()





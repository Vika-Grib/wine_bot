import requests
import telebot
from config import token
from bs4 import BeautifulSoup
from telebot import types
import logging


def get_wine_class_name(url, wine_example):
    response = requests.get(url)
    soup1 = BeautifulSoup(response.content, 'html.parser') #cодержимое разбираем с помощью BeautifulSoup с парсером 'html.parser' для создания объекта soup1

    if wine_example:
        tag = soup1.find(string=wine_example)
        if tag:
            parent_tag = tag.parent
            print("*****", parent_tag, "*****")
            while parent_tag and not parent_tag.has_attr('class'):
                parent_tag = parent_tag.parent

            if parent_tag and parent_tag.has_attr('class'):
                print('PARENT_TAG!!! ', parent_tag)
                return parent_tag #элемент BeautifulSoup, представляющий родительский тег, содержащий имя вина и требуемый атрибут класса
    return None


def collect_wine_names(url, parent_tag):
    responce = requests.get(url)
    soup = BeautifulSoup(responce.content, 'html.parser')

    wine_names_on_url_page = []
    for parent in soup.find_all(parent_tag.name, class_=parent_tag.get('class')):
        print("PARENT: ", parent)
        wine_name = parent.find(string=True, recursive=False)
        if wine_name:
            wine_names_on_url_page.append(wine_name.strip())
            print("wine_names_on_url_page\n", wine_names_on_url_page)

    return wine_names_on_url_page



# Функция для получения рейтинга вин от Vivino
def get_vivino_rating(wine_name):
    # URL страницы поиска Vivino с названием вина в качестве параметра запроса
    search_url = f"https://www.vivino.com/search/wines?q={wine_name}"
    print(search_url)
    response = requests.get(search_url, headers={'User-agent': 'Super Bot Power Level Over 9000'})
    print(response.status_code)
    print(response.url)
    # print(response.content)
    if response.status_code == 200:
        wine_search_soup = BeautifulSoup(response.content, 'html.parser')
        # первый элемент вина в результатах поиска
        wine_element = wine_search_soup.find('div', class_='wine-card__content')
        # print("#" * 50)
        # print(wine_element)
        # print("#" * 50)

        if wine_element:
            # нахождение рейтинга вина
            rating_element = wine_search_soup.find('div', class_='text-inline-block light average__number')
            if rating_element:
                rating_element_text = rating_element.get_text()
                print('*' * 50)
                print('RATING' + rating_element_text)
                print('*' * 50)
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
def process_wine_name(message, url):
    wine_example = message.text
    parent_tag = get_wine_class_name(url, wine_example)
    print("PARENT_TAG: \n", parent_tag)
    if parent_tag:
        wine_names = collect_wine_names(url, parent_tag)
        print('\n'.join(wine_names))

        ratings = {}
        for wine_name in wine_names:
            rating = get_vivino_rating(wine_name)
            ratings[wine_name] = rating if rating is not None else "Rating not found on Vivino"

        response = generate_response(ratings)
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "Wine example not found on the page! ")

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





# # запускаем бота
bot.polling()


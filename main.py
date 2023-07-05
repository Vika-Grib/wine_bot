import requests
import telebot
from config import token
from bs4 import BeautifulSoup
from telebot import types
import logging

# # настройка журнала
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.INFO)
#
# # создание бота
# bot = telebot.TeleBot(token)
#
# # команда старт
# @bot.message_handler(commands=['start'])
# def start(message):
#     bot.send_message(message.chat.id, "Hello! Please send me the URL of a wine page.")
#
# @bot.message_handler(func=lambda message: True)
# def process_message(message):
#     if message.text.startswith('http'):
#         url = message.text
#         bot.send_message(message.chat.id, "Great! Now, please send me the name of the wine.")
#         bot.register_next_step_handler(message, process_wine_name, url)
#     else:
#         bot.send_message(message.chat.id, "Please send valid URL.")
#
# #функция для обработки URL-адреса винной страницы
# def process_wine_name(message, url):
#     wine_example = message.text
#     ratings = get_wine_list(url, wine_example)
#     response = generate_response(ratings)
#     bot.send_message(message.chat.id, response)

url = 'https://8wines.com/wines'
wine_example = 'El Enemigo Chardonnay 2020'

def get_wine_class_name(url, wine_example=None):
    response = requests.get(url)
    soup1 = BeautifulSoup(response.content, 'html.parser')
    #print(soup1)
    if wine_example:
        tag = soup1.find(string=wine_example)
        wine_tags = soup1.find_all(string=wine_example)
        parent_tags = [tag.parent for tag in wine_tags]
        return parent_tags

    else:
        print("No wine example provided.")


def get_wine_list(url, wine_example):
    ratings = {}
    # print(ratings)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Вызвать исключение, если запрос не был успешным
        soup = BeautifulSoup(response.content, 'html.parser')
        print(soup)
        wine_examples = []

    #     for text in soup.find_all(string=True):
    #         if wine_example.lower() in text.lower():
    #             wine_examples_element = text.find_parent()
    #             if wine_examples_element:
    #                 wine_example = wine_examples_element.text.strip()
    #                 wine_examples.append(wine_example)
    #
    #     for wine_example in wine_examples:
    #         rating = get_vivino_rating(wine_example)
    #         ratings[wine_example] = rating
    #
    # except requests.exceptions.RequestException as e:
    #     print("Error occurred:", e)
    # return ratings

        product_elements = soup.find_all(string=wine_example)
        print(product_elements)
        for product in product_elements:
            wine_examples_element = product.find_parent()
            print(wine_examples_element)

            if wine_examples_element:
                wine_name = wine_examples_element.text.strip()
                wine_examples.append(wine_name)
        for wine_name in wine_examples:
            rating = get_vivino_rating(wine_name)
            ratings[wine_name] = rating
            #print(ratings)
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
    return ratings


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
        print("#" * 50)
        print(wine_element)
        print("#" * 50)

        if wine_element:
            # нахождение рейтинга вина
            rating_element = wine_search_soup.find('div', class_='text-inline-block light average__number')
            rating_element_text = rating_element.get_text()
            print('*' * 50)
            print('RATING' + rating_element_text)
            print('*' * 50)

            if rating_element:
                rating = rating_element.text.strip()
                print(rating)
                return rating
    # Если получить рейтинг не удалось, вернуть None
    return None


# Функция для генерации ответного сообщения с рейтингом вин
def generate_response(ratings):
    response = "Wine Ratings:\n"
    for wine_name, rating in ratings.items():
        response += f"{wine_name} - {rating}\n"
    return response
#
# # запускаем бота
# bot.polling()

parent_tags = get_wine_class_name(url, wine_example)
print(parent_tags)
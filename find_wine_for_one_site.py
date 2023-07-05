
import requests
import telebot
from config import token
from bs4 import BeautifulSoup
from telebot import types
import logging

# настройка журнала
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# создание бота
bot = telebot.TeleBot(token)

# команда старт
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Hello! Please send me the URL of a wine page.")

# функция для обработки URL-адреса винной страницы
@bot.message_handler(func=lambda message: True)
def process_url(message):
    url = message.text
    ratings = get_wine_ratings(url)
    response = generate_response(ratings)
    bot.send_message(message.chat.id, response)


def get_wine_ratings(url):
    ratings = {}
    try:
        response = requests.get(url)
        response.raise_for_status()  # Вызвать исключение, если запрос не был успешным
        soup = BeautifulSoup(response.content, 'html.parser')
        wine_names = []
        product_elements = soup.find_all('div', class_='product')
        for product in product_elements:
            wine_name_element = product.find('div', class_='box__title')
            if wine_name_element:
                wine_name = wine_name_element.text.strip()
                wine_names.append(wine_name)
        for wine_name in wine_names:
            rating = get_vivino_rating(wine_name)
            ratings[wine_name] = rating
    except requests.exceptions.RequestException as e:
        print("Error occurred:", e)
    return ratings


# Функция для получения рейтинга вин от Vivino
def get_vivino_rating(wine_name):
    # URL страницы поиска Vivino с названием вина в качестве параметра запроса
    search_url = f"https://www.vivino.com/search/wines?q={wine_name}"
    print(search_url)
    response = requests.get(search_url, headers = {'User-agent': 'Super Bot Power Level Over 9000'})
    print(response.status_code)
    print(response.url)
    #print(response.content)
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

# запускаем бота
bot.polling()

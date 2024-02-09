import sqlite3

import requests
from config import token, api_chat_gpt
import logging
import openpyxl
import parser_BeautifulSoup as pB
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Initialize bot and dispatcher
bot = Bot(token=token)
memory_storage = MemoryStorage()
dp = Dispatcher(bot, storage=memory_storage)


# Установка API-ключа OpenAI
openai.api_key = api_chat_gpt

# Функция для обработки запросов пользователя с использованием GPT
def get_gpt_response(user_input):
    response = openai.Completion.create(
        # engine="gpt-3.5-turbo-instruct",  # Выбрать нужный движок GPT
        engine="gpt-3.5-turbo-0125",  # Выбрать нужный движок GPT
        prompt=user_input,
        max_tokens=1000,
        temperature=0.9
    )
    return response.choices[0].text.strip()



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



# Функция для обработки URL-адреса винной страницы
def excel_paste(page_num, sheet):
    row_index = 2  # Начнем с 2 строки (после заголовков) (чтобы какждый раз не обнулялась - выносим вне функции и делаем в функции глобальной, чтобы она каждый раз не сбрасывалась, а олин раз начала с 2 и дальше ув +1)
    list_of_wines = []
    # global row_index, list_of_wines
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
            # print('new wine: ', wine_name)


def parser():
    list_of_wines = []

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



# команда старт
@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Get Wine Rating")
    btn2 = types.KeyboardButton("All wine`s ratings from page")
    btn3 = types.KeyboardButton("Ask AI about wine")
    markup.row(btn1, btn2)
    markup.add(btn3)
    await bot.send_message(chat_id=message.from_user.id, text=f"Hello, {message.from_user.first_name}!\nI`m bot. I`m here to help you to find out wine rating and answer questions about wine.", reply_markup=markup)
    # Please send me the URL of a wine page.


@dp.message_handler(text_contains='Ask AI about wine')  # это для кнопки
async def process_message(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Please ask AI what you want to know about wine.')
    await state.set_state('prepared_request')  # ожидает ссылку и наше состояние устанавливается

@dp.message_handler(content_types=['text'], state='prepared_request')  # а это чтобы кнопка по стейту срабатывала
async def process_message(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('wine_database.db')
    # Создаем объект cursor, который позволяет нам взаимодействовать с базой данных и добавлять записи
    cursor = conn.cursor()
    cursor.execute(f'''Select * from wine_ratings''')
    wine_ratings = list(cursor.fetchall())
    user_wine = message.text # то что вводит юзер - название вина
    for wine_rating in wine_ratings:
        if user_wine.lower() in wine_rating[0].lower(): # тут мы сравниваем именно имя [0] чтобы в нижнем регистре
            await bot.send_message(chat_id=message.from_user.id, text=wine_rating[1])
            break
        print('СРАВНИТЬ!', wine_rating[0], user_wine)
    await state.finish()


@dp.message_handler(text_contains='Get Wine Rating')
async def process_message(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Please send me the name of a wine for rating.')
    await state.set_state('prepared_rating')  # ожидает ссылку и наше состояние устанавливается


@dp.message_handler(content_types=['text'], state='prepared_rating')
async def process_message(message: types.Message, state: FSMContext):
    conn = sqlite3.connect('wine_database.db')
    # Создаем объект cursor, который позволяет нам взаимодействовать с базой данных и добавлять записи
    cursor = conn.cursor()
    cursor.execute(f'''Select * from wine_ratings''')
    wine_ratings = list(cursor.fetchall())
    user_wine = message.text # то что вводит юзер - название вина
    for wine_rating in wine_ratings:
        if user_wine.lower() in wine_rating[0].lower(): # тут мы сравниваем именно имя [0] чтобы в нижнем регистре
            await bot.send_message(chat_id=message.from_user.id, text=wine_rating[1])
            break
        print('СРАВНИТЬ!', wine_rating[0], user_wine)
    await state.finish()


@dp.message_handler(text_contains='All wine`s ratings from page')
async def process_message(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Please send me the URL of a wine page.')
    await state.set_state('prepared_rating_list')  # ожидает ссылку и наше состояние устанавливается


@dp.message_handler(content_types=['text'], state='prepared_rating_list')
async def process_message(message: types.Message, state: FSMContext):
    user_url = message.text
    if user_url.startswith('http'):
        # чтобы запомнить предыдущий ответ
        await state.update_data(user_url=user_url)
        await bot.send_message(chat_id=message.from_user.id, text='Great! Now, please copy as it`s named on page and send it to me.')
        await state.set_state('completed_request')  # ожидает ссылку и наше состояние устанавливается
    else:
        await bot.send_message(chat_id=message.from_user.id, text="Please send valid URL.")


@dp.message_handler(content_types=['text'], state='completed_request')
async def process_message(message: types.Message, state: FSMContext):
    async with state.proxy() as data:  # при помощи state.proxy() as data достали все аргументы из текущего состояния и записали в data
        user_url = data["user_url"]  # достаем из data нашу информацию
    if user_url.startswith('http'):
        wine_class_name = pB.get_wine_class_name(message, user_url)
        # print("wcm: ", wine_class_name)
        wine_page_list = pB.collect_wine_names(user_url, wine_class_name)
        rating_page_list = []
        for wine in wine_page_list:
            rating_page_list.append(pB.get_vivino_rating(wine))
        response = pB.generate_response(wine_page_list, rating_page_list)
        await bot.send_message(chat_id=message.from_user.id, text=response)
        await state.finish()  # заканчиваем стейт, чтобы он сбросился
    else:
        await bot.send_message(chat_id=message.from_user.id, text="Please send valid URL.")
        await state.set_state('prepared_request')


# Run the bot
if __name__ == '__main__':
    from aiogram import executor
    # print(get_gpt_response(input()))
    # настройка журнала
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)


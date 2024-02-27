import sqlite3
import requests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

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
        engine="gpt-3.5-turbo-instruct",  # Выбрать нужный движок GPT
        # engine="gpt-3.5-turbo-0125",  # Выбрать нужный движок GPT
        prompt=user_input,
        max_tokens=500,
        temperature=0.7
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


# Кнопка "Exit"
exit_button = KeyboardButton("Back to menu")
exit_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(exit_button)

class ConversationState(StatesGroup):
    conversation = State()


conn = sqlite3.connect('wine_database.db')
# Создаем объект cursor, который позволяет нам взаимодействовать с базой данных и добавлять записи
cursor = conn.cursor()


# команда старт
@dp.message_handler(commands=['start'])
@dp.message_handler(text_contains='Back to menu', state='prepared_rating')
@dp.message_handler(text_contains='Back to menu', state='prepared_rating_list')
async def start(message: types.Message, state: FSMContext):
    try:
        cursor.execute(f'SELECT * FROM users WHERE user_id={message.from_user.id}') # чтобы не пзаписывало много раз одного чела
        user = list(cursor.fetchall())[0]
    except Exception as e:
        print(e)
        cursor.execute(f'''INSERT INTO users VALUES ({str(message.from_user.id)},'{str(message.from_user.username)}','','')''')
        conn.commit()
    user = message.from_user
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Get Wine Rating")
    btn2 = types.KeyboardButton("All wine`s ratings from page")
    btn3 = types.KeyboardButton("Ask AI about wine")
    markup.row(btn1, btn2)
    markup.add(btn3)
    await bot.send_message(chat_id=message.from_user.id, text=f"Hello, {message.from_user.first_name}!\nI`m bot. I`m here to help you to find out wine rating and answer questions about wine.", reply_markup=markup)
    # Please send me the URL of a wine page.


# Обработчик нажатия кнопки "Ask AI about wine"
@dp.message_handler(text_contains='Ask AI about wine')
async def process_message(message: types.Message, state: FSMContext):
    await message.answer('Welcome! Feel free to ask me anything about wine.')
    await ConversationState.conversation.set()


# Обработчик состояния "conversation"
@dp.message_handler(content_types=['text'], state=ConversationState.conversation)
async def process_message(message: types.Message, state: FSMContext):
    # Проверяем наличие кнопки "Exit"
    if message.text == "Back to menu":
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton("Get Wine Rating")
        btn2 = types.KeyboardButton("All wine`s ratings from page")
        btn3 = types.KeyboardButton("Ask AI about wine")
        markup.row(btn1, btn2)
        markup.add(btn3)
        cursor.execute(f'''UPDATE users SET theme='' WHERE user_id = {message.from_user.id}''')
        conn.commit()
        cursor.execute(f'''UPDATE users SET main_idea='' WHERE user_id = {message.from_user.id}''')
        conn.commit()
        await message.answer('Exiting conversation. Feel free to start a new one anytime!',
                             reply_markup=markup)
        await message.answer('Пишем какое-то стартовое сообщение чтобы заново тыкать по кнопочкам!')
        await state.finish()
        return


    else:
        cursor.execute(f'''Select * from users WHERE user_id={message.from_user.id}''')
        user = list(cursor.fetchall())[0]
        theme = user[2]
        main_idea = user[3]
        if theme == '' and main_idea == '':
            first_gpt_response = get_gpt_response(message.text)
            print(first_gpt_response, '1_GPT_RESPONSE!!!!')
            await message.answer(first_gpt_response.strip(), reply_markup=exit_markup)
            # Сохраняем ответ gpt для будущих запросов
            gpt_response = get_gpt_response(f'''
Выдели тему сообщения в квадратных скобках, затем кратко запиши основную мысль.
Пример:
Начать пробовать красные супервина можно с французских вин, таких как Шато Латур или Шато Марго, итальянских вин, например, Бароло или Брунелло ди Монтальчино, аргентинских вин, например, Малбек или Каберне Совиньон, и других регионов, известных своими высококачественными красными винами, например, Напа Вэлли в Калифорнии или Бордо во Франции.

Твой идеальный ответ:
Тема: красные супервина.
Основная мысль: Шато Латур, Шато Марго, Бароло, Брунелло ди Монтальчино, Малбек, Каберне Совиньон, Напа Вэлли - Калифорния, Бордо - Франция.

[{first_gpt_response}]
''')
            gpt_theme = gpt_response.split('Основная мысль:')[0].replace('Тема:', '').strip()
            gpt_main_idea = gpt_response.split('Основная мысль:')[1].strip()
            theme = gpt_theme
            main_idea = gpt_main_idea
            cursor.execute(f'''UPDATE users SET theme='{theme}' WHERE user_id = {message.from_user.id}''')
            conn.commit()
            cursor.execute(f'''UPDATE users SET main_idea='{main_idea}' WHERE user_id = {message.from_user.id}''')
            conn.commit()

        else:
            context = f'''
Дай ответ на "Вопрос пользователя". Основная мысль вашего диалога находится в "Контекст".
Контекст: 
Тема: {theme}
Основная мысль: {main_idea}
Вопрос пользователя: 
{message.text}
'''
            # Передаем контекст в GPT
            next_gpt_response = get_gpt_response(context)
            await message.answer(next_gpt_response.strip(), reply_markup=exit_markup)
            gpt_response = get_gpt_response(f'''
Выдели тему сообщения в квадратных скобках, затем кратко запиши основную мысль.
Пример:
Начать пробовать красные супервина можно с французских вин, таких как Шато Латур или Шато Марго, итальянских вин, например, Бароло или Брунелло ди Монтальчино, аргентинских вин, например, Малбек или Каберне Совиньон, и других регионов, известных своими высококачественными красными винами, например, Напа Вэлли в Калифорнии или Бордо во Франции.

Твой идеальный ответ:
Тема: красные супервина.
Основная мысль: Шато Латур, Шато Марго, Бароло, Брунелло ди Монтальчино, Малбек, Каберне Совиньон, Напа Вэлли - Калифорния, Бордо - Франция.

[{next_gpt_response}]
''')
            print(next_gpt_response)
            gpt_theme = gpt_response.split('Основная мысль:')[0].replace('Тема:', '').strip()
            gpt_main_idea = gpt_response.split('Основная мысль:')[1].strip()
            theme += ' + ' + gpt_theme
            main_idea += ' + ' + gpt_main_idea
            cursor.execute(f'''UPDATE users SET theme='{theme}' WHERE user_id = {message.from_user.id}''')
            conn.commit()
            cursor.execute(f'''UPDATE users SET main_idea='{main_idea}' WHERE user_id = {message.from_user.id}''')
            conn.commit()
            print(gpt_response, "!!!!!")

            # Сбрасываем текущее состояние, но продолжаем слушать ввод пользователя
            await state.reset_state()

        # После ответа бота, переводим его снова в состояние "conversation"
    await ConversationState.conversation.set()


# @dp.message_handler(text_contains='Ask AI about wine')  # это для кнопки
# async def process_message(message: types.Message, state: FSMContext):
#     await bot.send_message(chat_id=message.from_user.id, text='Welcome! Feel free to ask me anything about wine.')
#     await state.set_state('conversation')  # ожидает ссылку и наше состояние устанавливается

# @dp.message_handler(content_types=['text'], state='conversation')  # а это чтобы кнопка по стейту срабатывала
# async def process_message(message: types.Message, state: FSMContext): # создает временное хранилище данных, называемое "proxy" (посредник), связанное с текущим состоянием
#     async with state.proxy() as data:
#         user_input = data.get("user_input", "")
#         user_input += f" {message.text}"  # Добавляем новый вопрос в контекст
#
#         # Передаем контекст в GPT
#         gpt_response = get_gpt_response(user_input)
#
#         await bot.send_message(chat_id=message.from_user.id, text=gpt_response.strip())
#         # # Сбрасываем текущее состояние, но продолжаем слушать ввод пользователя
#         # await state.reset_state()
#
#         # Сохраняем текущий ввод пользователя для будущих запросов
#         data["user_input"] = user_input
#     # Продолжаем беседу
#     await state.finish()

    # prompt = message.text
    # gpt_response = get_gpt_response(prompt)  # вызываем функцию для обработки запросов
    # await bot.send_message(chat_id=message.from_user.id, text=gpt_response)
    # await state.finish()


@dp.message_handler(text_contains='Get Wine Rating')
async def process_message(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Please send me the name of a wine for rating.', reply_markup=exit_markup)
    await state.set_state('prepared_rating')  # ожидает ссылку и наше состояние устанавливается


@dp.message_handler(content_types=['text'], state='prepared_rating')
async def process_message(message: types.Message, state: FSMContext):
    cursor.execute(f'''Select * from wine_ratings''')
    wine_ratings = list(cursor.fetchall())
    user_wine = message.text # то что вводит юзер - название вина
    for wine_rating in wine_ratings:
        if user_wine.lower() in wine_rating[0].lower(): # тут мы сравниваем именно имя [0] чтобы в нижнем регистре
            await bot.send_message(chat_id=message.from_user.id, text=wine_rating[1])
            break
        # print('СРАВНИТЬ!', wine_rating[0], user_wine)
    await state.finish()


@dp.message_handler(text_contains='All wine`s ratings from page')
async def process_message(message: types.Message, state: FSMContext):
    await bot.send_message(chat_id=message.from_user.id, text='Please send me the URL of a wine page.', reply_markup=exit_markup)
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
        await state.set_state('prepared_rating_list')


# Run the bot
if __name__ == '__main__':
    from aiogram import executor
    # print(get_gpt_response(input()))
    # настройка журнала
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    # logging.info('Starting the bot...')
    executor.start_polling(dp, skip_updates=True)




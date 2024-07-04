import requests
import psycopg2
import telebot
from telebot import types

token = '7442990666:AAHjb16py4B2rsdi4Rs4fdVGHOCAlT5QLBU'

bot = telebot.TeleBot(token)

conn = psycopg2.connect(
        dbname="vacancies",
        user="postgres",
        password="los",
        host="localhost",
        port="5432"
    )
cur = conn.cursor()

def get_vacancies_from_hh(city, vacancy):
    # Параметры для поиска
    headers = {'Authorization': 'Bearer APPLJUL05UFUADFTH956A0VCG16QATBP64CKMB75O5OIH4MEN19SKP15JT3U6N91'}
    params = {'text': vacancy, 'area': get_area_id(city), 'per_page': '100'}
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Vacancies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255),
            employer VARCHAR(255),
            salary_from INTEGER,
            salary_to INTEGER,
            currency VARCHAR(10),
            area_name VARCHAR(255),
            street_name VARCHAR(255),
            employment VARCHAR(255),
            experience VARCHAR(255),
            schedule VARCHAR(255)
        )
    """)
    conn.commit()

    url = 'https://api.hh.ru/vacancies'
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    for vacancy in data['items']:
        save_vacancy_to_db(vacancy)

def get_area_id(city):
    if city == "Москва":
        return 1
    elif city == "Санкт-Петербург":
        return 2
    elif city == "Мытищи":
        return 2041
    elif city == "Химки":
        return 2077
    elif city == "Долгопрудный":
        return 2085
    elif city == "Реутов":
        return 2094
    elif city == "Люберцы":
        return 2039
    else:
        return None

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Я помогу найти тебе различные вакансии в нескольких городах:')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Москва")
    item2 = types.KeyboardButton("Санкт-Петербург")
    item3 = types.KeyboardButton("Мытищи")
    item4 = types.KeyboardButton("Химки")
    item5 = types.KeyboardButton("Долгопрудный")
    item6 = types.KeyboardButton("Реутов")
    item7 = types.KeyboardButton("Люберцы")
    markup.add(item1, item2, item3, item4, item5, item6, item7)
    bot.send_message(message.chat.id, 'Выберите город:', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["Москва", "Санкт-Петербург", "Мытищи", "Химки", "Долгопрудный", "Реутов", "Люберцы"])
def city_selected(message):
    global selected_city
    selected_city = message.text  # Запомни выбранный город
    bot.send_message(message.chat.id, 'Отлично! Введите название вакансии:')
    bot.register_next_step_handler(message, vacancy_selected)

def vacancy_selected(message):
    global selected_vacancy
    selected_vacancy = message.text  # Запомни выбранную вакансию
    bot.send_message(message.chat.id, f'Вы выбрали город {selected_city} и вакансию {selected_vacancy}.')


def save_vacancy_to_db(vacancy):
    # Получение необходимых данных
    name = vacancy['name']
    salary = vacancy['salary']
    salary_from = salary['from'] if salary else None
    salary_to = salary['to'] if salary else None
    currency = salary['currency'] if salary else None
    area_name = vacancy['area']['name']
    address = vacancy['address']
    street_name = address['raw'] if address else None
    employer = vacancy['employer']
    employer_name = employer['name'] if employer else None
    employment = vacancy['employment']
    employment_name = employment['name'] if employment else None
    experience = vacancy['experience']
    experience_name = experience['name']
    schedule = vacancy['schedule']
    schedule_name = schedule['name']
    #description = vacancy['snippet']
    #requirement = description['requirement'] if description else None
    #responsibility = description['responsibility'] if description else None

    # Сохранение данных в базу
    cur.execute("""
                INSERT INTO Vacancies (name, area_name, salary_from, salary_to, currency, street_name, employer, employment,
                 experience, schedule)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, area_name, salary_from, salary_to, currency, street_name, employer_name, employment_name,
                  experience_name, schedule_name))

    conn.commit()

@bot.message_handler(func=lambda message: message.text in ["Веб-дизайнер", "Разработчик Python", "СЕО-аналитик",
                                                           "Грузчик", "Кассир"])

def vacancy_selected(message):
    selected_vacancy = message.text
    array = []
    print(selected_city)
    print(selected_vacancy)
    get_vacancies_from_hh(city_selected, selected_vacancy)
    cur.execute(f"SELECT * FROM Vacancies WHERE name = '{selected_vacancy}' AND area_name = '{selected_city}'")
    print((f"SELECT * FROM Vacancies WHERE name = '{selected_vacancy}' AND area_name = '{selected_city}'"))
    vacancies = cur.fetchall()
    if vacancies:
        for vacancy in vacancies:
            name = vacancy[1]
            employer = vacancy[2]
            salary_from = vacancy[3]
            salary_to = vacancy[4]
            currency = vacancy[5]
            area = vacancy[6]
            address = vacancy[7]
            employment = vacancy[8]
            experience = vacancy[9]
            schedule = vacancy[10]

            salary_from = salary_from if salary_from else "не указано"
            salary_to = salary_to if salary_to else "не указано"
            currency = currency if currency else "не указано"
            address = address if address else "не указано"
            employment = employment if employment else "не указано"
            experience = experience if experience else "не указано"
            schedule = schedule if schedule else "не указано"

            bot.send_message(message.chat.id, f"{name}\nЗарплата: {salary_from} - {salary_to} {currency}\n"
                                              f"Адрес: {address}\nГород: {area}\nЗанятость: {employment}\nОпыт: {experience}\n"
                                              f"График: {schedule}")
    else:
        bot.send_message(message.chat.id, "К сожалению, вакансий по данному запросу не найдено.")

bot.infinity_polling()
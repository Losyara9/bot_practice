import requests
import psycopg2
import telebot
from telebot import types

token = '7442990666:AAHjb16py4B2rsdi4Rs4fdVGHOCAlT5QLBU'

bot = telebot.TeleBot(token)

# Подключение к базе данных
conn = psycopg2.connect(
    dbname="vacancies",
    user="postgres",
    password="los",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# Создание таблицы в бд и парсинг вакансий


def get_vacancies_from_hh(city, vacancy):
    headers = {
        'Authorization': 'Bearer APPLJUL05UFUADFTH956A0VCG16QATBP64CKMB75O5OIH4MEN19SKP15JT3U6N91'}
    params = {'text': vacancy, 'area': get_area_id(city), 'per_page': '100'}
    print(get_area_id(city))
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER,
            name VARCHAR(255),
            employer VARCHAR(255),
            salary_from INTEGER,
            salary_to INTEGER,
            currency VARCHAR(10),
            area_name VARCHAR(255),
            street_name VARCHAR(255),
            employment VARCHAR(255),
            experience VARCHAR(255),
            schedule VARCHAR(255),
            link VARCHAR(255)
        )
    """)
    conn.commit()

    url = 'https://api.hh.ru/vacancies'
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    for vacancy in data['items']:
        save_vacancy_to_db(vacancy)

# Получение id города для фильтрации


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

# Обработка команды start


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        'Привет! Я помогу найти тебе различные вакансии в нескольких городах:\nЕсли хочешь начать заново'
        ' введи /start')
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


# Переменные для фильтров
selected_vacancy = None
selected_salary_from = None
selected_salary_to = None
selected_employment = None
selected_schedule = None

global selected_city


@bot.message_handler(
    func=lambda message: message.text in [
        "Москва",
        "Санкт-Петербург",
        "Мытищи",
        "Химки",
        "Долгопрудный",
        "Реутов",
        "Люберцы"])
def city_selected(message):
    global selected_city
    selected_city = message.text  # Запомни выбранный город
    bot.send_message(message.chat.id, 'Отлично! Введите название вакансии:')
    bot.register_next_step_handler(message, vacancy_selected)

# Обработка выбора вакансии


@bot.message_handler(func=lambda message: message.text)
def vacancy_selected(message):
    global selected_vacancy
    selected_vacancy = message.text
    bot.send_message(message.chat.id, 'Теперь выбери дополнительные фильтры:\n'
                     '1. Зарплата\n'
                     '2. Тип занятости\n'
                     '3. График работы\n'
                     '4. Ничего не добавлять')
    bot.register_next_step_handler(message, filter_selected)


# Обработка выбора фильтра
def filter_selected(message):
    if message.text == '1':
        bot.send_message(
            message.chat.id,
            'Введите минимальную желаемую зарплату:')
        bot.register_next_step_handler(message, salary_from_selected)
    elif message.text == '2':
        bot.send_message(message.chat.id, 'Выберите тип занятости:\n'
                         '/fulltime - Полная занятость\n'
                         '/parttime - Частичная занятость\n'
                         '/project - Проектная работа\n'
                         '/remote - Удаленная работа')
        bot.register_next_step_handler(message, employment_selected)
    elif message.text == '3':
        bot.send_message(message.chat.id, 'Выберите график работы:\n'
                         '/fullday - Полный день\n'
                         '/shift - Сменный график\n'
                         '/flexible - Гибкий график\n'
                         '/remote - Удаленная работа')
        bot.register_next_step_handler(message, schedule_selected)
    elif message.text == '4':
        show_vacancies(message)
    else:
        bot.send_message(
            message.chat.id,
            'Некорректный выбор. Попробуйте снова.')
        bot.register_next_step_handler(message, filter_selected)

# Обработка выбора минимальной зарплаты


def salary_from_selected(message):
    global selected_salary_from
    selected_salary_from = message.text
    bot.send_message(
        message.chat.id,
        'Введите максимальную желаемую зарплату:')
    bot.register_next_step_handler(message, salary_to_selected)

# Обработка выбора максимальной зарплаты


def salary_to_selected(message):
    global selected_salary_to
    selected_salary_to = message.text
    bot.send_message(
        message.chat.id,
        'Хотите добавить еще один фильтр? (да/нет)')
    bot.register_next_step_handler(message, add_filter)

# Обработка выбора типа занятости


def employment_selected(message):
    global selected_employment
    if message.text == '/fulltime':
        selected_employment = 'Полная занятость'
    elif message.text == '/parttime':
        selected_employment = 'Частичная занятость'
    elif message.text == '/project':
        selected_employment = 'Проектная работа'
    elif message.text == '/internship':
        selected_employment = 'Стажировка'
    else:
        bot.send_message(
            message.chat.id,
            'Некорректный выбор. Попробуйте снова.')
        bot.register_next_step_handler(message, employment_selected)
    bot.send_message(
        message.chat.id,
        'Хотите добавить еще один фильтр? (да/нет)')
    bot.register_next_step_handler(message, add_filter)

# Обработка выбора графика работы


def schedule_selected(message):
    global selected_schedule
    if message.text == '/fullday':
        selected_schedule = 'Полный день'
    elif message.text == '/shift':
        selected_schedule = 'Сменный график'
    elif message.text == '/flexible':
        selected_schedule = 'Гибкий график'
    elif message.text == '/remote':
        selected_schedule = 'Удаленная работа'
    else:
        bot.send_message(
            message.chat.id,
            'Некорректный выбор. Попробуйте снова.')
        bot.register_next_step_handler(message, schedule_selected)
    bot.send_message(
        message.chat.id,
        'Хотите добавить еще один фильтр? (да/нет)')
    bot.register_next_step_handler(message, add_filter)

# Обработка добавления дополнительных фильтров


def add_filter(message):
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, 'Выбери дополнительный фильтр:\n'
                         '1. Зарплата\n'
                         '2. Тип занятости\n'
                         '3. График работы')
        bot.register_next_step_handler(message, filter_selected)
    else:
        show_vacancies(message)


def save_vacancy_to_db(vacancy):
    # Получение необходимых данных
    idv = vacancy['id']
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
    link = vacancy['alternate_url']

    # Проверка на дубликат
    cur.execute("""
                    SELECT 1 FROM Vacancies
                    WHERE id = %s
                    LIMIT 1
                """, (idv,))

    if cur.fetchone() is None:
        # Если дубликата нет, сохраняем вакансию
        cur.execute(
            """
                        INSERT INTO Vacancies (id, name, area_name, salary_from, salary_to, currency, street_name, 
                        employer, employment, experience, schedule, link)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
            (idv,
             name,
             area_name,
             salary_from,
             salary_to,
             currency,
             street_name,
             employer_name,
             employment_name,
             experience_name,
             schedule_name,
             link))
        conn.commit()


def show_vacancies(message, page=1):
    """Функция для показа вакансий с пагинацией."""
    global selected_city, selected_vacancy
    get_vacancies_from_hh(
        selected_city,
        selected_vacancy)  # Получение данных с HH

    sql_query = f"SELECT * FROM Vacancies WHERE name = '{selected_vacancy}' AND area_name = '{selected_city}'"

    # Добавление доп. фильтров которые были указаны пользователем
    if selected_salary_from is not None:
        sql_query += f" AND salary_from >= {selected_salary_from}"
    if selected_salary_to is not None:
        sql_query += f" AND salary_to <= {selected_salary_to}"
    if selected_employment is not None:
        sql_query += f" AND employment = '{selected_employment}'"
    if selected_schedule is not None:
        sql_query += f" AND schedule = '{selected_schedule}'"

    cur.execute(sql_query)
    vacancies = cur.fetchall()

    if vacancies:
        # Определение индекса текущей вакансии
        vacancy_index = (page - 1) % len(vacancies)
        vacancy = vacancies[vacancy_index]

        # Вывод информации о текущей вакансии
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
        link = vacancy[11]

        salary_from = salary_from if salary_from else "не указано"
        salary_to = salary_to if salary_to else "не указано"
        currency = currency if currency else "не указано"
        address = address if address else "не указано"
        employment = employment if employment else "не указано"
        experience = experience if experience else "не указано"
        schedule = schedule if schedule else "не указано"

        bot.send_message(
            message.chat.id, f"{name}\nЗарплата: {salary_from} - {salary_to} {currency}\n"
            f"Адрес: {address}\nГород: {area}\nЗанятость: {employment}\nОпыт: {experience}\n"
            f"График: {schedule}\nРаботодатель: {employer}\nСсылка на вакансию: {link}")

        # Предложить пользователю продолжить просмотр
        bot.send_message(
            message.chat.id,
            "Хотите посмотреть следующую вакансию? (да/нет)")
        bot.register_next_step_handler(
            message, lambda m: handle_next_vacancy(
                m, page + 1))
    else:
        bot.send_message(
            message.chat.id,
            "К сожалению, вакансий по данному запросу не найдено.")
        bot.send_message(
            message.chat.id,
            "Хотите начать новый поиск? (да/нет)")
        bot.register_next_step_handler(message, start_over)


def handle_next_vacancy(message, page):
    # Обработчик ответа пользователя о продолжении просмотра

    if message.text.lower() == 'да':
        show_vacancies(message, page)  # Вывод следующей вакансии
    else:
        bot.send_message(
            message.chat.id,
            "Хорошо. Завершаем просмотр.")
        start_over(message)  # Возврат в главное меню


def start_over(message):
    if message.text.lower() == 'да':
        start_message(message)
    else:
        bot.send_message(
            message.chat.id,
            "До свидания!\nЕсли захотите продолжить просмотр введите /start")


bot.infinity_polling()

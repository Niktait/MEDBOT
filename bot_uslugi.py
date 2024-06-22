import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from config import BOT_TOKEN
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

состояния_пользователей = {}




def create_table():
    with sqlite3.connect('appointments.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                fullname TEXT,
                birthdate TEXT,
                time TEXT,
                doctor TEXT,
                date TEXT
            )
        ''')
        conn.commit()

create_table()



def save_to_db(user_id, fullname, birthdate, time, doctor, date):
    with sqlite3.connect('appointments.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, fullname, birthdate, time, doctor, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, fullname, birthdate, time, doctor, date))
        conn.commit()


def fetch_appointments_from_db():
    with sqlite3.connect('appointments.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments")
        appointments = cursor.fetchall()
    return appointments

@dp.message_handler(commands=['showbase'])
async def cmd_showbase(message: types.Message):
    appointments = fetch_appointments_from_db()
    
    base_message = "Текущая база данных:\n"
    for appointment in appointments:
        base_message += f"ID: {appointment[0]}, ФИО: {appointment[2]}, Дата рождения: {appointment[3]}, Время: {appointment[4]}, Врач: {appointment[5]}, Дата приема: {appointment[6]}\n"
    
    group_chat_id = '-1002129410883'  
    await bot.send_message(group_chat_id, base_message)





@dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    help_message = (
        "/start - Начать процесс записи к врачу\n"
        "/help - Получить справку по командам бота\n"
        "/info - Узнать информацию о медицинском центре\n"
        "/contact - Получить контактные данные медицинского центра"
    )
    await message.answer(help_message)

@dp.message_handler(commands=['info'])
async def cmd_info(message: types.Message):
    info_message = (
        "Добро пожаловать в наш медицинский центр!\n"
        "Мы предлагаем широкий спектр медицинских услуг, включая терапию, массаж, ЛФК и косметологические процедуры.\n"
        "Наши квалифицированные специалисты всегда готовы помочь вам."
    )
    await message.answer(info_message)

@dp.message_handler(commands=['contact'])
async def cmd_contact(message: types.Message):
    contact_message = (
        "Контактные данные медицинского центра:\n"
        "Адрес: ул. Примерная, д. 1\n"
        "Телефон: +7 (123) 456-78-90\n"
        "Электронная почта: info@medicalcenter.com"
    )
    await message.answer(contact_message)

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name
    welcome_message = f"Привет, {user_name}! Меня зовут Ляйсан, я запишу вас к интересующему специалисту 😊\n\nПозвольте задать вам пару вопросов:\nК какому врачу вас записать?"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Врач терапевт", callback_data="doctor_therapist"),
    )
    keyboard.add(
        InlineKeyboardButton("Массажист", callback_data="masseur"),
    )
    keyboard.add(
        InlineKeyboardButton("Врач ЛФК", callback_data="doctor_physiotherapist"),
    )
    keyboard.add(
        InlineKeyboardButton("Косметолог", callback_data="cosmetologist"),
    )
    await message.answer(welcome_message, reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data in ['doctor_therapist', 'masseur', 'doctor_physiotherapist', 'cosmetologist'])
async def process_doctor(callback_query: types.CallbackQuery):
    doctor_map = {
        'doctor_therapist': 'Врач терапевт',
        'masseur': 'Массажист',
        'doctor_physiotherapist': 'Врач ЛФК',
        'cosmetologist': 'Косметолог'
    }
    user_id = callback_query.from_user.id
    состояния_пользователей[user_id] = {'doctor': doctor_map[callback_query.data]}
    keyboard = InlineKeyboardMarkup()
    today = datetime.date.today()
    weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
    
    added_days = 0
    day_offset = 0
    while added_days < 5:
        date = today + datetime.timedelta(days=day_offset)
        if date.weekday() < 5:  # Only add weekdays (Monday to Friday)
            weekday_name = weekdays[date.weekday()]
            keyboard.add(
                InlineKeyboardButton(f"{weekday_name}, {date.strftime('%d.%m.%Y')}", callback_data=f"weekday_{date.strftime('%Y-%m-%d')}")
            )
            added_days += 1
        day_offset += 1
    
    await bot.send_message(callback_query.from_user.id, "Выберите день недели и дату:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('weekday_'))
async def process_weekday(callback_query: types.CallbackQuery):
    selected_date = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    состояния_пользователей[user_id]['date'] = selected_date
    await bot.send_message(callback_query.from_user.id, f"Выбран {selected_date}. Теперь выберите время:", reply_markup=generate_time_keyboard())

def generate_time_keyboard():
    keyboard = InlineKeyboardMarkup()
    for hour in range(9, 21):
        keyboard.add(
            InlineKeyboardButton(f"{hour}:00", callback_data=f"time_{hour}"),
        )
    return keyboard

@dp.callback_query_handler(lambda c: c.data.startswith('time_'))
async def process_time(callback_query: types.CallbackQuery):
    chosen_time = callback_query.data.split('_')[1]
    user_id = callback_query.from_user.id
    состояния_пользователей[user_id]['time'] = chosen_time
    await bot.send_message(callback_query.from_user.id, f"Выбранное время: {chosen_time}. Теперь введите вашу ФИО и номер телефона :")

@dp.message_handler(regexp=r'^[А-Яа-яЁё]+\s[А-Яа-яЁё]\.\s?[А-Яа-яЁё]?\.?$')
async def ask_birthdate(message: types.Message):
    user_id = message.from_user.id
    состояния_пользователей[user_id]['fullname'] = message.text
    await message.answer("Пожалуйста, введите вашу дату рождения в формате ДД.ММ.ГГГГ (например, 01.01.1990):")

@dp.message_handler(regexp=r'^\d{2}\.\d{2}.\d{4}$')
async def save_birthdate(message: types.Message):
    user_id = message.from_user.id
    состояния_пользователей[user_id]['birthdate'] = message.text
    user_data = состояния_пользователей.get(user_id, {})
    fullname = user_data.get('fullname')
    birthdate = user_data.get('birthdate')
    chosen_time = user_data.get('time')
    selected_date = user_data.get('date')
    doctor = user_data.get('doctor')
    if fullname and birthdate and chosen_time and selected_date and doctor:
        group_chat_id = '-1002129410883'
        await bot.send_message(group_chat_id, f"Новая заявка на прием:\nФИО и номер телефона: {fullname}\nДата рождения: {birthdate}\nВыбранная дата: {selected_date}\nВыбранное время: {chosen_time}\nВрач: {doctor}")
        save_to_db(user_id, fullname, birthdate, chosen_time, doctor, selected_date)
        await message.answer("Спасибо! Ваша запись завершена, для уточнения с вами свяжется наш специалист.")
        состояния_пользователей.pop(user_id)
    else:
        await message.answer("Произошла ошибка, пожалуйста, начните процесс заново.")



dp.register_message_handler(ask_birthdate)
dp.register_message_handler(save_birthdate)
-1002129410883





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
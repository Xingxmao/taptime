import telebot
from telebot import types
import threading
import time
from flask import Flask, render_template_string

API_TOKEN = '7470985226:AAGviFk4WbEE0JNpkwVxxMSHoVatpPM_z0M'
bot = telebot.TeleBot(API_TOKEN)

tasks = {
    'task1': {'name': 'Iceberg', 'duration': 6 * 3600, 'end_time': None},
    'task2': {'name': 'Simple Coin', 'duration': 6 * 3600, 'end_time': None},
    'task3': {'name': 'Gleam', 'duration': 3 * 3600, 'end_time': None},
    'task4': {'name': 'Time', 'duration': 4 * 3600, 'end_time': None},
    'task5': {'name': 'Bump', 'duration': 6 * 3600, 'end_time': None},
    'task6': {'name': 'Clayton', 'duration': 6 * 3600, 'end_time': None},
    'task7': {'name': 'Blum', 'duration': 8 * 3600, 'end_time': None},
    'task8': {'name': 'Vertus', 'duration': 6 * 3600, 'end_time': None},
}

app = Flask(__name__)

def reset_task(task_key):
    tasks[task_key]['end_time'] = time.time() + tasks[task_key]['duration']

def format_time(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def check_tasks():
    while True:
        for task_key in tasks:
            task = tasks[task_key]
            if task['end_time']:
                remaining_time = int(task['end_time'] - time.time())
                if remaining_time <= 0:
                    bot.send_message(chat_id, f"⏰ Время на {task['name']} истекло!")
                    task['end_time'] = None
        time.sleep(1)

def send_status_message(chat_id):
    status_message = "Текущий статус дел:\n"
    for task_key in tasks:
        task = tasks[task_key]
        if task['end_time']:
            remaining_time = int(task['end_time'] - time.time())
            status_message += f"📌 <b>{task['name']}</b>: {format_time(remaining_time)} осталось\n"
        else:
            status_message += f"📌 <b>{task['name']}</b>: Таймер не установлен\n"
    bot.send_message(chat_id, status_message, parse_mode='HTML')

def start_all_tasks():
    for task_key in tasks:
        reset_task(task_key)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global chat_id
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_start_all = types.KeyboardButton("Запустить все")
    btn_reset = types.KeyboardButton("Сбросить")
    btn_all_tasks = types.KeyboardButton("Все задачи")
    btn_live_status = types.KeyboardButton("Реальное время")
    markup.add(btn_start_all, btn_reset, btn_all_tasks, btn_live_status)
    bot.send_message(chat_id, "Привет! Это бот для отслеживания дел. Выбери действие.", reply_markup=markup)
    threading.Thread(target=check_tasks, daemon=True).start()

@bot.message_handler(func=lambda message: message.text == "Запустить все")
def handle_start_all(message):
    start_all_tasks()
    bot.send_message(message.chat.id, "Все задачи запущены на 4 часа.")

@bot.message_handler(func=lambda message: message.text == "Сбросить")
def choose_task_to_reset(message):
    markup = types.InlineKeyboardMarkup()
    for task_key in tasks:
        btn = types.InlineKeyboardButton(tasks[task_key]['name'], callback_data=f"reset_{task_key}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери задачу для сброса таймера:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Все задачи")
def choose_task_to_set_time(message):
    markup = types.InlineKeyboardMarkup()
    for task_key in tasks:
        btn = types.InlineKeyboardButton(tasks[task_key]['name'], callback_data=f"start_{task_key}")
        markup.add(btn)
    bot.send_message(message.chat.id, "Выбери задачу для запуска таймера на 4 часа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reset_'))
def handle_reset(call):
    task_key = call.data[len('reset_'):]
    reset_task(task_key)
    bot.answer_callback_query(call.id, f"Таймер для {tasks[task_key]['name']} сброшен!")
    bot.send_message(call.message.chat.id, f"Таймер для {tasks[task_key]['name']} сброшен на {tasks[task_key]['duration'] // 3600} часов.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('start_'))
def handle_start(call):
    task_key = call.data[len('start_'):]
    reset_task(task_key)
    bot.answer_callback_query(call.id, f"Таймер для {tasks[task_key]['name']} запущен на 4 часа!")
    bot.send_message(call.message.chat.id, f"Таймер для {tasks[task_key]['name']} запущен на 4 часа.")

@bot.message_handler(func=lambda message: message.text == "Реальное время")
def live_status(message):
    markup = types.InlineKeyboardMarkup()
    btn_refresh = types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh_status")
    markup.add(btn_refresh)
    send_status_message(message.chat.id)
    bot.send_message(message.chat.id, "Нажмите '🔄 Обновить', чтобы обновить статус дел.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_status")
def handle_refresh(call):
    send_status_message(call.message.chat.id)
    bot.answer_callback_query(call.id, "Статус обновлен!")

@app.route('/')
def index():
    status_message = "--------------------------------------------------------------------------:<br>"
    for task_key in tasks:
        task = tasks[task_key]
        if task['end_time']:
            remaining_time = int(task['end_time'] - time.time())
            status_message += f"📌 <b>{task['name']}</b>: {format_time(remaining_time)} осталось<br>"
        else:
            status_message += f"📌 <b>{task['name']}</b>: Таймер не установлен<br>"
    return render_template_string('''
        <html>
            <head>
                <meta http-equiv="refresh" content="60">
                <title>Статус дел</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: black;
                        color: white;
                        text-align: center;
                    }
                    .task {
                        margin-bottom: 10px;
                    }
                    .tasks {
                        display: inline-block;
                        text-align: left;
                        margin-top: 50px;
                    }
                </style>
            </head>
            <body>
                <h1>Текущий статус дел</h1>
                <div class="tasks">
                    {{ status_message|safe }}
                </div>
            </body>
        </html>
    ''', status_message=status_message)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False), daemon=True).start()
    bot.polling()


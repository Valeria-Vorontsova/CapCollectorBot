import telebot
from telebot import types
from ServerAPI import ServerAPI
import threading
import time
from collections import defaultdict

BOT_TOKEN = '8314416685:AAFtQTsB_o8QlB7fID1vObGDAveut3pkgnk'
bot = telebot.TeleBot(BOT_TOKEN)
api = ServerAPI()
user_tokens = {}
user_queue_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()

    btn_register = types.InlineKeyboardButton(
        text="Зарегистрироваться",
        callback_data="register"
    )

    btn_login = types.InlineKeyboardButton(
        text="Войти",
        callback_data="login"
    )

    markup.add(btn_register, btn_login)

    bot.send_message(
        message.chat.id,
        "Добро пожаловать в CapCollector!\n\nВыберите действие:",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_login(call):
    bot.answer_callback_query(call.id)

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    if call.data == "register":
        msg = bot.send_message(call.message.chat.id, "Введите email")
        bot.register_next_step_handler(msg, process_register_email)

    elif call.data == "login":
        msg = bot.send_message(call.message.chat.id, "Введите email:")
        bot.register_next_step_handler(msg, process_email, msg.message_id)


# REGISTER

def process_register_email(message):
    email = message.text.strip()

    if not is_valid_email(email):
        msg = bot.send_message(message.chat.id, "Введите корректный email ❌\nПопробуйте снова:")
        bot.register_next_step_handler(msg, process_register_email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(
        msg,
        process_register_password,
        email,
        msg.message_id
    )


def process_register_password(message, email, bot_msg_id=None):
    password = message.text.strip()

    if not is_valid_password(password):
        msg = bot.send_message(message.chat.id, "Пароль не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(
            msg,
            process_register_password,
            email,
            msg.message_id
        )
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
        if bot_msg_id:
            bot.delete_message(message.chat.id, bot_msg_id)
    except:
        pass

    telegram_id = message.from_user.id

    data = api.register(email, password, telegram_id)
    print(data)

    if handle_api_response(bot, message, data, process_register_email):
        return

    token = data.get("access_token")
    if token:
        user_tokens[telegram_id] = token

    bot.send_message(message.chat.id, "Вы успешно зарегистрированы ✅")
    send_main_menu(message)


# LOGIN

def process_email(message, bot_msg_id=None):
    email = message.text.strip()

    if not is_valid_email(email):
        msg = bot.send_message(message.chat.id, "Введите корректный email ❌\nПопробуйте снова:")
        bot.register_next_step_handler(msg, process_email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
        if bot_msg_id:
            bot.delete_message(message.chat.id, bot_msg_id)
    except:
        pass

    msg = bot.send_message(message.chat.id, "Введите пароль:")
    bot.register_next_step_handler(
        msg,
        process_password,
        email,
        msg.message_id
    )


def process_password(message, email, bot_msg_id=None):
    password = message.text.strip()

    if not is_valid_password(password):
        msg = bot.send_message(message.chat.id, "Пароль не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(
            msg,
            process_password,
            email,
            msg.message_id
        )
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
        if bot_msg_id:
            bot.delete_message(message.chat.id, bot_msg_id)
    except:
        pass

    data = api.login(email, password)
    print(data)

    if handle_api_response(bot, message, data, process_email):
        return

    token = data.get("access_token")
    if not token:
        msg = bot.send_message(
            message.chat.id,
            "Неверный email или пароль ❌\nВведите email:"
        )
        bot.register_next_step_handler(msg, process_email)
        return

    user_id = message.from_user.id
    user_tokens[user_id] = token

    bot.send_message(message.chat.id, "Вы успешно вошли ✅")
    send_main_menu(message)


# VALIDATION

def is_valid_password(password):
    return isinstance(password, str) and len(password.strip()) > 0


def is_valid_email(email):
    return (
        isinstance(email, str)
        and "@" in email
        and "." in email
        and len(email.strip()) > 0
    )


# ERROR HANDLER

def handle_api_response(bot, data, chat_id=None, message=None, retry_callback=None):
    """
    Обрабатывает ответ API.
    - bot: экземпляр TeleBot
    - data: словарь с ответом от API
    - chat_id: ID чата (используется, если message=None)
    - message: объект сообщения (если есть, используется его chat.id и retry)
    - retry_callback: функция для повторного шага (только если есть message)
    Возвращает True, если была ошибка и сообщение отправлено.
    """
    target_chat_id = chat_id if chat_id is not None else (message.chat.id if message else None)
    if target_chat_id is None:
        # Нет ни chat_id, ни message – невозможно отправить ответ
        return True

    if not data:
        text = "Ошибка соединения с сервером 🌐\nПопробуйте снова:"
        msg = bot.send_message(target_chat_id, text)
        if message and retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    if "error" in data:
        if data["error"] == "connection_error":
            text = "Нет соединения с сервером 🌐\nПопробуйте снова:"
        elif data["error"].startswith("server_error"):
            text = "Ошибка сервера ⚙️\nПопробуйте снова:"
        else:
            text = "Неизвестная ошибка ❌\nПопробуйте снова:"

        msg = bot.send_message(target_chat_id, text)
        if message and retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    if data.get("status") == "Failed":
        text = data.get("message", "Ошибка ❌") + "\nВведите email заново:"
        msg = bot.send_message(target_chat_id, text)
        if message and retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    return False

def send_main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🪙 Проверить баланс", "📥 Пополнить баланс")
    keyboard.add("🛠 Поддержка", "❓ FAQ")
    keyboard.add("🌐 Сайт проекта")

    bot.send_message(
        message.chat.id,
        "Главное меню:",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == "🪙 Проверить баланс")
def handle_check_balance(message):
    user_id = message.from_user.id

    token = user_tokens.get(user_id)

    if not token:
        msg = bot.send_message(
            message.chat.id,
            "Вы не авторизованы ❌\nВведите email:"
        )
        bot.register_next_step_handler(msg, process_email, msg.message_id)
        return
    print("TOKEN:", token) #TEST
    data = api.get_current_user(token)
    print("DATA:", data) #TEST
    if handle_api_response(bot, message, data, process_email):
        return

    user = data.get("user", {})
    balance = user.get("balance", 0)

    bot.send_message(
        message.chat.id,
        f"💰 Ваш баланс: {balance}"
    )

@bot.message_handler(func=lambda message: message.text == "📥 Пополнить баланс")
def handle_top_up(message):
    msg = bot.send_message(
        message.chat.id,
        "Введите код установки (4 символа):"
    )
    bot.register_next_step_handler(msg, process_machine_code)

def process_machine_code(message):
    user_id = message.from_user.id
    token = user_tokens.get(user_id)

    if not token:
        msg = bot.send_message(
            message.chat.id,
            "Вы не авторизованы ❌\nВведите email:"
        )
        bot.register_next_step_handler(msg, process_email, msg.message_id)
        return

    code = message.text.strip()

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    if not is_valid_machine_code(code):
        msg = bot.send_message(
            message.chat.id,
            "Код должен состоять из 4 символов (буквы или цифры) ❌\nВведите снова:"
        )
        bot.register_next_step_handler(msg, process_machine_code)
        return

    data = api.add_to_queue(token, code)
    print(data)

    if handle_api_response(bot, message, data, process_machine_code):
        return

    # Если ошибка (статус Failed) – обрабатываем
    if data.get("status") == "Failed":
        msg = bot.send_message(
            message.chat.id,
            data.get("message", "Ошибка ❌") + "\nПопробуйте снова:"
        )
        bot.register_next_step_handler(msg, process_machine_code)
        return

    # Успешный ответ: выводим информацию и планируем таймеры
    queue_data = data.get("data", {})
    position = queue_data.get("user_position") or 0
    wait_time = queue_data.get("estimated_wait_time") or 0

    message_text = data.get("message", "")
    prefix = "ℹ️" if "уже" in message_text.lower() else "✅"

    bot.send_message(
        message.chat.id,
        f"{prefix} {message_text}\n"
        f"📍 Позиция: {position}\n"
        f"⏳ Ожидание: {wait_time} сек"
    )

    # Запускаем планировщик очереди
    schedule_queue_checks(user_id, token, code, data)

def is_valid_machine_code(code):
    return isinstance(code, str) and len(code) == 4 and code.isalnum()

def schedule_queue_checks(user_id, token, machine_code, response_data):
    """
    Планирует таймеры на основе ответа от add_to_queue.
    Если estimated_wait_time == 0, сразу переходим к этапу внесения.
    """
    # Отменяем старые таймеры пользователя
    cancel_user_timers(user_id)

    # Извлекаем данные из ответа
    queue_data = response_data.get("data", {})
    estimated_wait = queue_data.get("estimated_wait_time", 0)  # секунды до начала внесения
    my_time = queue_data.get("my_time", 0)                    # секунды на внесение
    queue_item_id = queue_data.get("queue_item_id")

    # Сохраняем контекст
    user_queue_data[user_id] = {
        "machine_code": machine_code,
        "token": token,
        "queue_item_id": queue_item_id,
        "timers": {}
    }

    # Если estimated_wait == 0, значит пользователь уже первый
    if estimated_wait == 0:
        # Сообщаем, что очередь подошла
        bot.send_message(user_id, f"✅ Ваша очередь подошла! У вас есть {my_time} секунд, чтобы внести крышки.")
        # Планируем запрос на получение данных о внесении через my_time
        timer_deposit = threading.Timer(my_time, check_deposits, args=[user_id, token])
        user_queue_data[user_id]["timers"]["deposit"] = timer_deposit
        timer_deposit.start()
    else:
        # Планируем повторную проверку очереди через estimated_wait секунд
        timer_wait = threading.Timer(estimated_wait, check_queue_position, args=[user_id, token, machine_code])
        user_queue_data[user_id]["timers"]["wait"] = timer_wait
        timer_wait.start()

def check_queue_position(user_id, token, machine_code):
    """
    Вызывается, когда истёк estimated_wait_time.
    Делает повторный запрос add_to_queue, чтобы получить актуальное состояние.
    """
    # Если пользователь уже удалил таймер или вышел, выходим
    if user_id not in user_queue_data:
        return

    data = api.add_to_queue(token, machine_code)
    print(f"Re-check queue for {user_id}: {data}")

    # Обрабатываем ошибки
    if handle_api_response(bot, None, data, None):  # передаём message=None, но для ошибок нужно отправить сообщение
        bot.send_message(user_id, "❌ Ошибка при проверке очереди. Попробуйте позже.")
        cancel_user_timers(user_id)
        return

    if data.get("status") == "Successful":
        queue_data = data.get("data", {})
        estimated_wait = queue_data.get("estimated_wait_time", 0)
        my_time = queue_data.get("my_time", 0)

        if estimated_wait == 0:
            # Теперь очередь подошла
            bot.send_message(user_id, f"✅ Ваша очередь подошла! У вас есть {my_time} секунд, чтобы внести крышки.")
            # Планируем получение данных о внесении
            timer_deposit = threading.Timer(my_time, check_deposits, args=[user_id, token])
            user_queue_data[user_id]["timers"]["deposit"] = timer_deposit
            timer_deposit.start()
        else:
            # Всё ещё не первый – планируем снова (хотя по логике такого быть не должно, т.к. время ожидания истекло)
            timer_wait = threading.Timer(estimated_wait, check_queue_position, args=[user_id, token, machine_code])
            user_queue_data[user_id]["timers"]["wait"] = timer_wait
            timer_wait.start()
    else:
        bot.send_message(user_id, "❌ Не удалось проверить очередь. Попробуйте позже.")
        cancel_user_timers(user_id)

def check_deposits(user_id, token):
    """
    Вызывается после окончания времени на внесение.
    Запрашивает get_last_deposits и выводит результат.
    """
    if user_id not in user_queue_data:
        return

    data = api.get_last_deposits(token)
    print(f"Deposits for {user_id}: {data}")

    if handle_api_response(bot, None, data, None):
        bot.send_message(user_id, "❌ Ошибка при получении данных о внесении.")
        cancel_user_timers(user_id)
        return

    if data.get("status") == "Successful":
        message_text = data.get("message", "")
        if message_text == "В эту сессию вы не загружали крышки":
            bot.send_message(user_id, "ℹ️ В эту сессию вы не загружали крышки.")
        else:
            deposits = data.get("deposits", [])
            if deposits:
                # Формируем красивое сообщение о крышках
                deposit_lines = []
                for dep in deposits:
                    # Предполагаем структуру deposits (уточните по документации)
                    # Например, может быть deposit_time, amount, etc.
                    amount = dep.get("amount", "?")
                    timestamp = dep.get("created_at", "")
                    deposit_lines.append(f"• {amount} крышек в {timestamp}")
                reply = "✅ Данные о внесённых крышках:\n" + "\n".join(deposit_lines)
                bot.send_message(user_id, reply)
            else:
                bot.send_message(user_id, "ℹ️ Данные о крышках не получены.")
    else:
        bot.send_message(user_id, "❌ Не удалось получить данные о внесении.")

    # Завершаем сессию очереди для пользователя
    cancel_user_timers(user_id)

def cancel_user_timers(user_id):
    """Отменяет все активные таймеры пользователя и удаляет запись."""
    if user_id in user_queue_data:
        timers = user_queue_data[user_id].get("timers", {})
        for t in timers.values():
            if t and t.is_alive():
                t.cancel()
        del user_queue_data[user_id]

@bot.message_handler(func=lambda message: message.text == "🛠 Поддержка")
def handle_support(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

@bot.message_handler(func=lambda message: message.text == "❓ FAQ")
def handle_faq(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

@bot.message_handler(func=lambda message: message.text == "🌐 Сайт проекта")
def handle_website(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

bot.polling(none_stop=True)
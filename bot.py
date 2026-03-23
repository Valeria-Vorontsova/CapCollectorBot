import traceback

import telebot
from dotenv import load_dotenv
from telebot import types
from ServerAPI import ServerAPI
import threading
import os
from flask import Flask, request
import json
from telebot.types import Update

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
print("BOT_TOKEN:", BOT_TOKEN)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
api = ServerAPI()
user_tokens = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("🔥 START HANDLER TRIGGERED")
    try:
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
        print("✅ Message sent")
    except Exception as e:
        print(f"❌ Error in send_welcome: {e}")
        import traceback
        traceback.print_exc()

'''@bot.message_handler(func=lambda message: True)
def debug_all(message):
    print("📩 MESSAGE:", repr(message.text))'''

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

    bot.send_message(message.chat.id, "⏳ Регистрация...")
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

    bot.send_message(message.chat.id, "⏳ Вход...")
    data = api.login(email, password)
    print(data)

    if handle_api_response(bot, message, data, process_email):
        bot.send_message(message.chat.id, "Введите email ещё раз:")
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

def handle_api_response(bot, message, data, retry_callback):
    if not data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка соединения с сервером 🌐\nПопробуйте снова:"
        )
        if retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    if "error" in data:
        if data["error"] == "connection_error":
            text = "⏳ Сервер отвечает медленно, пробуем ещё раз..."
        elif data["error"].startswith("server_error"):
            text = "Ошибка сервера ⚙️\nПопробуйте снова:"
        else:
            text = "Неизвестная ошибка ❌\nПопробуйте снова:"

        msg = bot.send_message(message.chat.id, text)

        if retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    if data.get("status") == "Failed":
        msg = bot.send_message(
            message.chat.id,
            data.get("message", "Ошибка ❌") + "\nВведите email заново:"
        )

        if retry_callback:
            bot.register_next_step_handler(msg, retry_callback)
        return True

    return False

def send_main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🪙 Проверить баланс", "📥 Пополнить баланс")
    keyboard.add("🌐 Сайт проекта", "❓ FAQ")

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
    bot.send_message(message.chat.id, "⏳ Получаю баланс...")
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
        bot.register_next_step_handler(msg, process_email)
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

    bot.send_message(message.chat.id, "⏳ Проверяю установку...")
    data = api.add_to_queue(token, code)
    print(data)

    if not data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка соединения 🌐\nВведите код снова:"
        )
        bot.register_next_step_handler(msg, process_machine_code)
        return

    if "error" in data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка сервера ❌\nВведите код снова:"
        )
        bot.register_next_step_handler(msg, process_machine_code)
        return

    if data.get("status") == "Failed":
        msg = bot.send_message(
            message.chat.id,
            data.get("message", "Ошибка ❌") + "\nПопробуйте снова:"
        )
        bot.register_next_step_handler(msg, process_machine_code)
        return

    queue_data = data.get("data", {})

    position = queue_data.get("user_position") or 0
    wait_time = queue_data.get("estimated_wait_time") or 0
    my_time = queue_data.get("my_time") or 0

    message_text = data.get("message", "")
    is_already_in_queue = "уже" in message_text.lower()
    prefix = "ℹ️" if is_already_in_queue else "✅"

    bot.send_message(
        message.chat.id,
        f"{prefix} {message_text}\n"
        f"📍 Позиция: {position}\n"
        f"⏳ Ожидание: {wait_time} сек"
    )

    # если НЕ первый — ждем очередь
    if wait_time > 0:
        wait_for_turn(message.chat.id, token, code, wait_time)

    else:
        if my_time <= 0:
            bot.send_message(
                message.chat.id,
                "⚠️ Время для внесения уже истекло или недоступно.\nПопробуйте снова."
            )
            return

        bot.send_message(
            message.chat.id,
            f"🔥 Вы первый в очереди!\n"
            f"У вас есть {my_time} сек для внесения крышек"
        )

        threading.Timer(
            my_time,
            finish_session,
            args=[message.chat.id, token]
        ).start()

def is_valid_machine_code(code):
    return isinstance(code, str) and len(code) == 4 and code.isalnum()

def wait_for_turn(chat_id, token, code, wait_time):
    def check():
        data = api.add_to_queue(token, code)

        if not data or data.get("status") != "Successful":
            bot.send_message(chat_id, "Ошибка при проверке очереди ❌")
            return

        queue_data = data.get("data", {})

        position = queue_data.get("user_position", 0)
        my_time = queue_data.get("my_time", 0)
        wait_time_new = queue_data.get("estimated_wait_time", 0)

        if position == 1:
            bot.send_message(
                chat_id,
                f"🔥 Теперь ваша очередь!\nУ вас есть {my_time} сек для внесения крышек"
            )

            # запускаем завершение сессии
            threading.Timer(my_time, finish_session, args=[chat_id, token]).start()

        else:
            bot.send_message(
                chat_id,
                f"⏳ Всё ещё ждёте...\nПозиция: {position}\nОсталось: {wait_time_new} сек"
            )

            threading.Timer(wait_time_new, check).start()

    threading.Timer(wait_time, check).start()

def finish_session(chat_id, token):
    data = api.get_last_deposits(token)

    if not data or data.get("status") != "Successful":
        bot.send_message(chat_id, "Ошибка при получении данных ❌")
        return

    if "deposits" not in data:
        bot.send_message(chat_id, "❌ В эту сессию вы не загружали крышки")
        return

    bot.send_message(chat_id, "⏳ Получаю данные о внесённых крышках...")
    deposits = data.get("deposits", [])

    user = data.get("user", {})
    total = sum(d.get("tokens_count", 0) for d in deposits)
    balance = user.get("balance", 0)
    bot.send_message(
        chat_id,
        f"✅ Сессия завершена\n"
        f"Зачислено: {total} крышек 🪙\n"
        f"💰 Текущий баланс: {balance}"
    )

@bot.message_handler(func=lambda message: message.text == "❓ FAQ")
def handle_faq(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

@bot.message_handler(func=lambda message: message.text == "🌐 Сайт проекта")
def handle_website(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

@bot.message_handler(func=lambda message: True)
def fallback(message):
    print("❗ UNKNOWN:", repr(message.text))

# ---------- ВЕБХУКИ ----------

print("DEBUG: handlers defined")

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running"


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        print("📥 Received update:", json_data)

        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])

        print("✅ Updates processed by bot")

    except Exception as e:
        print(f"❌ Error processing update: {e}")
        traceback.print_exc()
        return 'Error', 500

    return 'OK', 200


def set_webhook():
    webhook_url = 'https://capcollectorbot.onrender.com/webhook'

    try:
        bot.remove_webhook()
        success = bot.set_webhook(url=webhook_url)

        print("Webhook set:", success)
        print("Webhook info:", bot.get_webhook_info())

    except Exception as e:
        print("❌ Webhook error:", e)

print("DEBUG: before set_webhook")
set_webhook()
print("DEBUG: after set_webhook")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

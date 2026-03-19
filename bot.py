import telebot
from telebot import types
from ServerAPI import ServerAPI

BOT_TOKEN = '8314416685:AAFtQTsB_o8QlB7fID1vObGDAveut3pkgnk'
bot = telebot.TeleBot(BOT_TOKEN)
api = ServerAPI()
user_tokens = {}

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
    except Exception as e:
        print(e)

    if call.data == "register":
        msg = bot.send_message(
            call.message.chat.id,
            "Введите email"
        )
        bot.register_next_step_handler(msg, process_register_email)

    elif call.data == "login":
        msg = bot.send_message(
            call.message.chat.id,
            "Введите email:"
        )
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


def process_register_password(message, email, bot_msg_id):
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
        bot.delete_message(message.chat.id, bot_msg_id)
    except:
        pass

    telegram_id = message.from_user.id

    data = api.register(email, password, telegram_id)
    print(data)

    if handle_api_response(
        bot,
        message,
        data,
        process_register_email
    ):
        return

    token = data.get("access_token")
    if token:
        user_tokens[telegram_id] = token

    bot.send_message(message.chat.id, "Вы успешно зарегистрированы ✅")
    send_main_menu(message)


# LOGIN

def process_email(message, bot_msg_id):
    email = message.text.strip()

    if not is_valid_email(email):
        msg = bot.send_message(message.chat.id, "Введите корректный email ❌\nПопробуйте снова:")
        bot.register_next_step_handler(
            msg,
            process_email,
            msg.message_id
        )
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
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


def process_password(message, email, bot_msg_id):
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
        bot.delete_message(message.chat.id, bot_msg_id)
    except:
        pass

    data = api.login(email, password)
    print(data)

    if handle_api_response(
        bot,
        message,
        data,
        process_email
    ):
        return

    token = data.get("access_token")
    if not token:
        msg = bot.send_message(
            message.chat.id,
            "Неверный email или пароль ❌\nВведите email:"
        )
        bot.register_next_step_handler(
            msg,
            process_email,
            msg.message_id
        )
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
            text = "Нет соединения с сервером 🌐\nПопробуйте снова:"
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
    keyboard.add("🛠 Поддержка", "❓ FAQ")
    keyboard.add("🌐 Сайт проекта")

    bot.send_message(
        message.chat.id,
        "Главное меню:",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: message.text == "🪙 Проверить баланс")
def handle_check_balance(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

@bot.message_handler(func=lambda message: message.text == "📥 Пополнить баланс")
def handle_pay_balance(message):
    bot.send_message(message.chat.id, "Скоро будет доступно")

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
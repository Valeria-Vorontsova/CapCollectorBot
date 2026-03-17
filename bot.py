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
        bot.register_next_step_handler(msg, process_email)

def process_register_email(message):
    email = message.text

    msg = bot.send_message(
        message.chat.id,
        "Введите пароль:"
    )
    bot.register_next_step_handler(msg, process_register_password)

def process_register_password(message, email):
    password = message.text

    telegram_id = message.from_user.id

    data = api.register(telegram_id, email, password)

    if not data or "error" in data:
        bot.send_message(
            message.chat.id,
            "Ошибка регистрации ❌"
        )
        return
    token = data("token")
    if token:
        user_id = message.from_user.id
        user_tokens[user_id] = token

    bot.send_message(
        message.chat.id,
        "Вы успешно зарегистрированы ✅"
    )

def process_email(message):
    email = message.text

    msg = bot.send_message(
        message.chat.id,
        "Введите пароль:"
    )

    bot.register_next_step_handler(msg, process_password, email)

def process_password(message, email):
    password = message.text

    data = api.login(email, password)

    if not data or "token" not in data:
        bot.send_message(
            message.chat.id,
            "Неверный email или пароль ❌"
        )
        return

    token = data.get("token")

    user_id = data.from_user.id
    user_tokens[user_id] = token

    bot.send_message(
        message.chat.id,
        "Вы успешно вошли ✅"
    )

    send_main_menu(message)

def send_main_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard.add("🪙 Проверить баланс", "📥 Пополнить баланс")
    keyboard.add("🛠 Поддержка", "❓ FAQ")
    keyboard.add("🌐 Сайт проекта")

    bot.send_message(
        message.chat.id,
        " ",
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
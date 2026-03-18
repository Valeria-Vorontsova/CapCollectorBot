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
        bot.register_next_step_handler(msg, process_email)

def process_register_email(message):
    email = message.text.strip()

    if not email:
        msg = bot.send_message(message.chat.id, "Email не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(msg, process_register_email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(e)

    msg = bot.send_message(
        message.chat.id,
        "Введите пароль:"
    )
    bot.register_next_step_handler(msg, process_register_password, email)

def process_register_password(message, email, bot_message_id = None):
    password = message.text.strip()
    if not password:
        msg = bot.send_message(message.chat.id, "Пароль не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(msg, process_register_password, email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print("Не удалось удалить сообщение:", e)

    telegram_id = message.from_user.id

    data = api.register(email, password, telegram_id)
    print(data) # TEST

    if not data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка соединения ❌\nВведите email:"
        )
        bot.register_next_step_handler(msg, process_register_email)
        return

    if "error" in data:
        msg = bot.send_message(message.chat.id, "Ошибка соединения ❌\nВведите email:")
        bot.register_next_step_handler(msg, process_register_email)
        return

    if data.get("status") == "Failed":
        msg = bot.send_message(
            message.chat.id, "Такой пользователь уже существует ❌\Введите email:"
        )
        bot.register_next_step_handler(msg, process_register_email)
        return

    token = data.get("access_token")
    if token:
        user_tokens[telegram_id] = token

    bot.send_message(
        message.chat.id,
        "Вы успешно зарегистрированы ✅"
    )
    send_main_menu(message)


def process_email(message):
    email = message.text
    if not email:
        msg = bot.send_message(message.chat.id, "Email не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(msg, process_email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e: print(e)
    msg = bot.send_message(
        message.chat.id,
        "Введите пароль:"
    )
    bot.register_next_step_handler(msg, process_password, email)

def process_password(message, email):
    password = message.text.strip()
    if not password:
        msg = bot.send_message(message.chat.id, "Пароль не может быть пустым ❌\nВведите снова:")
        bot.register_next_step_handler(msg, process_password, email)
        return

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e: print(e)

    data = api.login(email, password)
    print(data) #TEST

    if not data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка соединения с сервером 🌐\nПопробуйте снова ввести пароль:"
        )
        bot.register_next_step_handler(msg, process_password, email)
        return

    if "error" in data:
        msg = bot.send_message(
            message.chat.id,
            "Ошибка авторизации ❌\nВведите пароль снова:"
        )
        bot.register_next_step_handler(msg, process_password, email)
        return

    token = data.get("access_token")
    if not token:
        msg = bot.send_message(
            message.chat.id,
            "Неверный email или пароль ❌\nВведите email"
        )
        bot.register_next_step_handler(msg, process_email)
        return

    user_id = message.from_user.id
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
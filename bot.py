import telebot
from telebot import*


BOT_TOKEN = '8314416685:AAFtQTsB_o8QlB7fID1vObGDAveut3pkgnk'
bot = telebot.TeleBot(BOT_TOKEN)

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
def callback_handler(call):

    if call.data == "register":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Регистрация скоро будет доступна.")
        send_main_menu(call.message)

    elif call.data == "login":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "Вход скоро будет доступен.")
        send_main_menu(call.message)

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
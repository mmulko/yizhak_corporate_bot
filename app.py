from telebot import credentials as cert
from flask import Flask, request
import logging
from telebot.credentials import bot_token, bot_user_name, URL
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
import telegram

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

cred = credentials.Certificate('yizhak-533ce-firebase-adminsdk-j45mn-3508c70645.json')
firebase_admin.initialize_app(cred, {'databaseURL': cert.database_url})
global bot
global TOKEN
global code_key
code_key = ""
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)
CODE, STEP_1, STEP_2, AVAILABILITY = range(4)


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the corp for their code."""
    update.message.reply_text(
        'Привіт, я Їжак!\n'
        'Дякую, що ви обрали співпрацю зі мною та моєю командою!\n'
        'Введіть /cancel аби завершити роботу зі мною\n'
        'Будь ласка, введіть ключ доступу вашого закладу',
    )

    return CODE


def apply_code(update: Update, context: CallbackContext) -> int:
    """Prints out menu and generates next steps for corp"""
    user = update.message.from_user
    logger.info("Code of %s: %s", user.first_name, update.message.text)
    code = update.message.text
    global code_key
    code_key = code
    print("[DEBUG]: Passcode accepted")
    bot_stand_by_pass = "Код прийнято, оброблюю запит..."
    bot.sendMessage(chat_id=update.message.chat_id, text=bot_stand_by_pass)
    ref = db.reference("/")
    print("[DEBUG]: DB reference created")
    answer = ref.get()
    bot_menu_reply = "Меню закладу <<" + answer[code]['Name'] + ">>"
    menu = answer[code]["Menu"]
    menu_keys = menu.keys()
    for elem in menu_keys:
        bot_menu_reply += "\n" + str(elem) + " - " + str(menu[elem]) + " грн"
    print("[DEBUG]: Menu formed")
    bot.sendMessage(chat_id=update.message.chat_id, text=bot_menu_reply)
    list_of_options = ["Подати на продаж", "Перевірити наявність"]
    reply_keyboard = [list_of_options]
    print("[DEBUG]: Option buttons created")
    update.message.reply_text(
        'Оберіть наступну дію або введіть /cancel',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )

    return STEP_1


def step_1(update: Update, context: CallbackContext) -> int:
    """Prints out possible items for selling"""
    global code_key
    code = code_key
    user = update.message.from_user
    logger.info("Choice of %s: %s", user.first_name, update.message.text)
    text_2 = update.message.text
    ref = db.reference("/")
    print("[DEBUG]: DB reference created")
    answer = ref.get()
    menu = answer[code]["Menu"] # Possible Key Error
    menu_keys = menu.keys()
    if text_2 == "Подати на продаж":
        list_of_options_2 = []
        for elem in menu_keys:
            list_of_options_2.append(elem)
        reply_keyboard = [list_of_options_2]
        update.message.reply_text(
            'Оберіть страву для виставлення на продаж (Кожну одиницю потрібно вводити окремо)',
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True
            ),
        )
        print("STep_2")
        return STEP_2
    elif text_2 == "Перевірити наявність":
        update.message.reply_text(
            'Оброблюю запит...'
            )
        print("avail")
        return AVAILABILITY


def step_2(update: Update, context: CallbackContext) -> int:
    """Stores the product to the database and prints confirmation and end of work message"""
    user = update.message.from_user
    logger.info("Product of %s: %s", user.first_name, update.message.text)
    choice = update.message.text
    global code_key
    code = code_key
    ref = db.reference("/")
    print("[DEBUG]: DB reference created")
    answer = ref.get()
    price = str(answer[code]["Menu"][choice])
    users_ref = ref.child(f'{code}')
    avail_ref = users_ref.child('Availability')
    avail_ref.push(f'{choice}, {price}')
    update.message.reply_text(
        f'{choice} за {price} гривень тепер доступний для придбання!\n\nПерезапуск бота...\n\nНапишіть /start для початку роботи'
    )

    return ConversationHandler.END


def availability(update: Update, context: CallbackContext) -> int:
    """Prints out products that are available for sale and end of work message"""
    try:
        print("Started function")
        global code_key
        print(1)
        code = code_key
        print(2)
        user = update.message.from_user
        print(3)
        ref = db.reference("/")
        print(4)
        answer = ref.get()
        print(5)
        bot_answer = "Товари, що виставлені на продаж:"
        print(6)
        available_list = answer[code]["Availability"]
        print(7)
        av_list_keys = available_list.keys()
        print(8)
        menu = answer[code]["Menu"]
        print(9)
        menu_keys = []
        print(10)
        for key in av_list_keys:
            if available_list[key] == "null":
                print("null caught")
                continue
            else:
                print("new key")
                menu_keys.append(available_list[key])
        print("list formed")
        print(menu_keys)
        for elem in menu_keys:
            print("forming answer")
            print(elem)
            bot_answer += "\n" + str(elem)
        print("answer got")
        update.message.reply_text(
            f'{bot_answer}\n\nПерезапуск бота...\n\nНапишіть /start для початку роботи'
        )

        return ConversationHandler.END
    except Exception as e:
        print("[ERROR]: " + str(e))
        return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


@app.route('/{}'.format(TOKEN), methods=['POST'])
def main() -> None:
    """Run the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CODE: [MessageHandler(Filters.text & ~Filters.command, apply_code)],
            STEP_1: [MessageHandler(Filters.text & ~Filters.command, step_1)],
            STEP_2: [MessageHandler(Filters.text & ~Filters.command, step_2)],
            AVAILABILITY: [MessageHandler(Filters.all, availability)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()
    updater.idle()


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook('{URL}{HOOK}'.format(URL="https://4cb7f59f317f.ngrok.io/", HOOK=TOKEN))
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
    return '[STATUS]: Working'


if __name__ == '__main__':
    app.run(threaded=True)

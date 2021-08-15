import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from telebot import credentials as cert
from flask import Flask, request
import telegram
from telebot.credentials import bot_token, bot_user_name, URL

cred = credentials.Certificate('yizhak-533ce-firebase-adminsdk-j45mn-3508c70645.json')
firebase_admin.initialize_app(cred, {'databaseURL': cert.database_url})
global bot
global TOKEN
global count
count = 0
TOKEN = bot_token
bot = telegram.Bot(token=TOKEN)

app = Flask(__name__)


@app.route('/{}'.format(TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    global count
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    chat_id = update.message.chat.id
    msg_id = update.message.message_id

    # Telegram understands UTF-8, so encode text for unicode compatibility
    text = update.message.text.encode('utf-8').decode()
    # for debugging purposes only
    print("[RECEIVE] Got text message :", text)
    # the first time you chat with the bot AKA the welcoming message
    if text == "/start":
        # print the welcoming message
        bot_welcome = """Привіт, я Їжак!\nДякую, що ви обрали співпрацю зі мною та моєю командою!"""
        # send the welcoming message
        bot.sendMessage(chat_id=chat_id, text=bot_welcome)
        bot_ask_pass = """Будь ласка, введіть ключ доступу вашого закладу"""
        bot.sendMessage(chat_id=chat_id, text=bot_ask_pass)
    else:
        try:
            if "@%" in text:
                print("[DEBUG]: Passcode accepted")
                code = text
                bot_stand_by_pass = "Код прийнято, оброблюю запит..."
                bot.sendMessage(chat_id=chat_id, text=bot_stand_by_pass)
                ref = db.reference("/")
                print("[DEBUG]: DB reference created")
                answer = ref.get()
                bot_menu_reply = "Меню закладу " + answer[text]['Name']
                menu = answer[code]["Menu"]
                menu_keys = menu.keys()
                for elem in menu_keys:
                    bot_menu_reply += "\n" + str(elem) + " - " + str(menu[elem]) + " грн"
                print("[DEBUG]: Menu formed")
                bot.sendMessage(chat_id=chat_id, text=bot_menu_reply)
                list_of_options = ['001@%SASHKO', '002@%POLIA', '003@%MISHA']
                button_list = [list_of_options]
                print("[DEBUG]: Option buttons created")
                bot.sendMessage(chat_id=chat_id, text="Оберіть наступну дію:", reply_markup=telegram.ReplyKeyboardMarkup(button_list, one_time_keyboard=True))
                # bot_ask_pass = """Будь ласка, введіть ключ доступу вашого закладу"""
                # bot.sendMessage(chat_id=chat_id, text=bot_ask_pass)
                # while True:
                #     update = telegram.Update.de_json(request.get_json(force=True), bot)
                #     chat_id = update.message.chat.id
                #     text_2 = update.message.text.encode('utf-8').decode()
                #     if text_2 == text:
                #         continue
                #     else:
                #         break
                # if
            else:
                print(00)
                raise ValueError
        except Exception as e:
            # if things went wrong
            print("[ERROR]: " + str(e))
            bot.sendMessage(chat_id=chat_id,
                            text="Я розгубився, спробуй написати щось інше")

    return 'ok'


# def city(update, context):
#     list_of_cities = ['Erode', 'Coimbatore', 'London', 'Thunder Bay', 'California']
#     button_list = []
#     for each in list_of_cities:
#         button_list.append(InlineKeyboardButton(each, callback_data=each))
#     reply_markup = InlineKeyboardMarkup(
#         build_menu(button_list, n_cols=1))  # n_cols = 1 is for single column and mutliple rows
#     bot.send_message(chat_id=update.message.chat_id, text='Choose from the following', reply_markup=reply_markup)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


@app.route('/setwebhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=TOKEN))
    # something to let us know things work
    if s:
        return "webhook setup ok"
    else:
        return "webhook setup failed"


@app.route('/')
def index():
    return '.'


if __name__ == '__main__':
    # note the threaded arg which allow
    # your app to have more than one thread
    app.run(threaded=True)

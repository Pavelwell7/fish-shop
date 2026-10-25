import logging
from io import BytesIO

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from strapi import get_picture, get_product, get_products


logger = logging.getLogger(__name__)

_database = None


def start(update, context):
    products = get_products(
        context.bot_data["strapi_url"],
        context.bot_data["strapi_token"],
    )

    keyboard = []
    for product in products:
        button = InlineKeyboardButton(
            product["title"],
            callback_data=product["documentId"],
        )
        keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text("Please choose:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def handle_menu(update, context):
    query = update.callback_query
    if query is None:
        return "HANDLE_MENU"

    if query.data == "back":
        return start(update, context)

    strapi_url = context.bot_data["strapi_url"]
    product = get_product(strapi_url, context.bot_data["strapi_token"], query.data)

    text = f"{product['title']} — {product['price']} ₽\n\n{product['description']}"
    keyboard = [[InlineKeyboardButton("Назад", callback_data="back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    picture = product.get("picture")
    image = get_picture(strapi_url, picture[0]["url"]) if picture else None

    context.bot.delete_message(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
    )

    if image:
        context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=BytesIO(image),
            caption=text[:1024],
            reply_markup=reply_markup,
        )
    else:
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=reply_markup,
        )
    return "HANDLE_DESCRIPTION"

def handle_description(update, context):
    query = update.callback_query
    if query is None:
        return "HANDLE_DESCRIPTION"

    if query.data == "back":
        next_state = start(update, context)
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        return next_state

    return "HANDLE_DESCRIPTION"

def handle_users_reply(update, context):
    db = get_database_connection()

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        update.callback_query.answer()
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = db.get(chat_id)
        if user_state is None:
            user_state = "START"

    states_functions = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description,
    }
    state_handler = states_functions[user_state]

    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception:
        logger.exception("Ошибка в обработчике состояния %s", user_state)


def get_database_connection():
    global _database
    if _database is None:
        env = Env()
        _database = redis.Redis(
            host=env.str("REDIS_HOST", "localhost"),
            port=env.int("REDIS_PORT", 6379),
            password=env.str("REDIS_PASSWORD", None),
            decode_responses=True,
        )
    return _database


def main():
    logging.basicConfig(level=logging.INFO)

    env = Env()
    env.read_env()

    token = env.str("TG_BOT_TOKEN")
    strapi_url = env.str("STRAPI_URL")
    strapi_token = env.str("STRAPI_TOKEN")

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data["strapi_url"] = strapi_url
    dispatcher.bot_data["strapi_token"] = strapi_token
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
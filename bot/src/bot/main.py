import logging
from io import BytesIO

import redis
from environs import Env
from strapi import (
    add_product_to_cart,
    delete_cart_item,
    get_cart,
    get_or_create_cart,
    get_picture,
    get_product,
    get_products,
    save_client,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

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

    keyboard.append([InlineKeyboardButton("Моя корзина", callback_data="cart")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text("Please choose:", reply_markup=reply_markup)
    return "HANDLE_MENU"


def show_cart(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id

    cart = get_cart(
        context.bot_data["strapi_url"],
        context.bot_data["strapi_token"],
        chat_id,
    )
    cart_items = cart["cart_items"] if cart else []

    keyboard = []
    if cart_items:
        lines = []
        total = 0
        for item in cart_items:
            product = item["product"]
            cost = product["price"] * item["quantity"]
            total += cost
            lines.append(f"{product['title']}: {item['quantity']:g} кг — {cost:.2f} ₽")
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"Убрать: {product['title']}",
                        callback_data=f"remove:{item['documentId']}",
                    )
                ]
            )
        lines.append(f"\nИтого: {total:.2f} ₽")
        text = "\n".join(lines)
        keyboard.append([InlineKeyboardButton("Оплатить", callback_data="pay")])
    else:
        text = "Корзина пуста."

    keyboard.append([InlineKeyboardButton("В меню", callback_data="back")])

    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    context.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)
    return "HANDLE_CART"


def handle_menu(update, context):
    query = update.callback_query
    if query is None:
        return "HANDLE_MENU"

    if query.data == "back":
        return start(update, context)

    if query.data == "cart":
        return show_cart(update, context)

    strapi_url = context.bot_data["strapi_url"]
    product = get_product(strapi_url, context.bot_data["strapi_token"], query.data)

    text = f"{product['title']} — {product['price']} ₽\n\n{product['description']}"
    keyboard = [
        [
            InlineKeyboardButton(
                "Добавить в корзину",
                callback_data=f"add_to_cart:{query.data}",
            )
        ],
        [InlineKeyboardButton("Моя корзина", callback_data="cart")],
        [InlineKeyboardButton("Назад", callback_data="back")],
    ]

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
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        return start(update, context)

    if query.data == "cart":
        return show_cart(update, context)

    if query.data.startswith("add_to_cart:"):
        product_document_id = query.data.removeprefix("add_to_cart:")
        strapi_url = context.bot_data["strapi_url"]
        strapi_token = context.bot_data["strapi_token"]

        cart = get_or_create_cart(strapi_url, strapi_token, query.message.chat_id)
        add_product_to_cart(
            strapi_url,
            strapi_token,
            cart["documentId"],
            product_document_id,
        )
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Товар добавлен в корзину.",
        )

    return "HANDLE_DESCRIPTION"


def handle_cart(update, context):
    query = update.callback_query
    if query is None:
        return "HANDLE_CART"

    if query.data == "back":
        context.bot.delete_message(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
        )
        return start(update, context)

    if query.data.startswith("remove:"):
        delete_cart_item(
            context.bot_data["strapi_url"],
            context.bot_data["strapi_token"],
            query.data.removeprefix("remove:"),
        )
        return show_cart(update, context)

    if query.data == "pay":
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Пришлите вашу почту для связи с менеджером:",
        )
        return "WAITING_EMAIL"

    return "HANDLE_CART"


def is_valid_email(email):
    name, separator, domain = email.partition("@")
    return (
        bool(name)
        and separator == "@"
        and "@" not in domain
        and "." in domain
        and " " not in email
    )


def handle_waiting_email(update, context):
    if update.message is None:
        return "WAITING_EMAIL"

    email = update.message.text.strip()
    chat_id = update.message.chat_id

    if not is_valid_email(email):
        context.bot.send_message(
            chat_id=chat_id,
            text="Это не похоже на почту. Попробуйте ещё раз, например: name@mail.ru",
        )
        return "WAITING_EMAIL"

    logger.info("Почта пользователя %s: %s", chat_id, email)
    save_client(
        context.bot_data["strapi_url"],
        context.bot_data["strapi_token"],
        chat_id,
        email,
    )

    logger.info("Почта пользователя %s: %s", chat_id, email)
    context.bot.send_message(
        chat_id=chat_id,
        text=f"Спасибо! Мы напишем на {email}, чтобы оформить заказ.",
    )
    return start(update, context)


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
        "HANDLE_CART": handle_cart,
        "WAITING_EMAIL": handle_waiting_email,
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

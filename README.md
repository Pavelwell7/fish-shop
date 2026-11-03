# Fish Shop

Telegram-бот для заказа морепродуктов.

## Что получится

Бот в Telegram, в котором покупатель может:

- посмотреть меню товаров;
- открыть карточку товара с фото, ценой и описанием;
- добавить товары в корзину, посмотреть её содержимое с итоговой суммой и убрать лишнее;
- оставить почту для связи с менеджером.

Менеджер видит клиентов и корзины в админке Strapi.

## Зависимости

Python 3.11, управление через [uv](https://docs.astral.sh/uv/).

| Пакет | Для чего |
|---|---|
| `python-telegram-bot==13.15` | Работа с Telegram API, синхронная версия библиотеки |
| `requests` | Запросы к REST API Strapi |
| `redis` | Подключение к Redis для хранения состояний пользователей |
| `environs` | Чтение настроек и токенов из файла `.env` |
| `setuptools<81` | Нужен планировщику внутри `python-telegram-bot` 13.15 |
| `ruff` (dev) | Линтер и форматтер кода |

## Внешние сервисы

Бот не содержит код этих сервисов, ему нужен только доступ к ним.

| Сервис | Для чего |
|---|---|
| [Strapi 5](https://strapi.io/) | CMS: товары, корзины, клиенты. Может быть запущен локально или на удалённом сервере |
| Redis | Хранение текущего состояния каждого пользователя в диалоге |

### Что должно быть в Strapi

| Коллекция | Поля |
|---|---|
| `Product` | `title` (Text), `description` (Text), `price` (Number), `picture` (Media). Товары должны быть опубликованы |
| `CartItem` | `quantity` (Number, decimal), `product` (Relation с `Product`) |
| `Cart` | `tg_id` (Text, Unique), `cart_items` (Relation с `CartItem`) |
| `Client` | `tg_id` (Text, Unique), `email` (Email) |

Для `Cart`, `CartItem` и `Client` отключён Draft & publish. Боту нужен API-токен (**Settings → API Tokens**, тип `Full access`).

## Что потребуется

- Linux, macOS или Windows с WSL (Ubuntu)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.11 он скачает сам)
- Запущенный Redis
- Доступный Strapi с API-токеном
- Токен Telegram-бота от [@BotFather](https://t.me/BotFather)

## Установка

Клонирование и установка зависимостей:

```bash
git clone git@github.com:Pavelwell7/fish-shop.git
cd fish-shop
uv sync
```

Redis (если ещё не установлен):

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping    # должно ответить PONG
```

Если в WSL нет systemd: `sudo service redis-server start`.

## Настройка

Скопируйте пример и заполните значения:

```bash
cp .env.example .env
```

| Переменная | Значение |
|---|---|
| `TG_BOT_TOKEN` | Токен бота от @BotFather |
| `STRAPI_URL` | Адрес Strapi, например `http://localhost:1337` |
| `STRAPI_TOKEN` | API-токен из админки Strapi |
| `REDIS_HOST` | Хост Redis, по умолчанию `localhost` |
| `REDIS_PORT` | Порт Redis, по умолчанию `6379` |
| `REDIS_PASSWORD` | Пароль Redis, если он задан (необязательно) |

Файл `.env` содержит секреты и не попадает в git.

## Запуск

Убедитесь, что Redis и Strapi запущены, затем:

```bash
uv run python src/bot/main.py
```

Откройте бота в Telegram и отправьте `/start`.

## Разработка

Форматирование и проверка кода:

```bash
uv run ruff format .
uv run ruff check --fix .
```

Добавление зависимостей: `uv add имя_пакета`.
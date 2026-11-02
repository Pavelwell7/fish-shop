# Fish Shop

Telegram-бот для заказа морепродуктов.

## Что получится

Бот в Telegram, в котором покупатель может:

- посмотреть меню товаров;
- открыть карточку товара с фото, ценой и описанием;
- добавить товары в корзину, посмотреть её содержимое с итоговой суммой и убрать лишнее;
- оставить почту для связи с менеджером.

Менеджер видит клиентов и корзины в админке Strapi.

## Стек и зависимости

Проект состоит из двух независимых частей: `cms/` (Strapi) и `bot/` (Telegram-бот).

**Бот (Python 3.11, управление через [uv](https://docs.astral.sh/uv/))**

| Пакет | Для чего |
|---|---|
| `python-telegram-bot==13.15` | Работа с Telegram API, синхронная версия библиотеки |
| `requests` | Запросы к REST API Strapi |
| `redis` | Подключение к Redis для хранения состояний пользователей |
| `environs` | Чтение настроек и токенов из файла `.env` |
| `setuptools<81` | Нужен планировщику внутри `python-telegram-bot` 13.15 |
| `ruff` (dev) | Линтер и форматтер кода |

**Сервисы**

| Сервис | Для чего |
|---|---|
| [Strapi 5](https://strapi.io/) (Node.js, SQLite) | CMS: товары, корзины, клиенты, REST API |
| Redis | Хранение текущего состояния каждого пользователя в диалоге |

## Что потребуется

- Linux, macOS или Windows с WSL (Ubuntu)
- [Node.js](https://nodejs.org/) LTS (удобно ставить через [nvm](https://github.com/nvm-sh/nvm))
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 3.11 он скачает сам)
- Redis
- Токен Telegram-бота от [@BotFather](https://t.me/BotFather)

## Установка

### 1. Клонирование

```bash
git clone git@github.com:Pavelwell7/fish-shop.git
cd fish-shop
```

### 2. Redis

```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
redis-cli ping    # должно ответить PONG
```

Если в WSL нет systemd: `sudo service redis-server start`.

### 3. Strapi

```bash
cd cms
cp .env.example .env
npm install
```

В `cms/.env` замените заглушки на случайные значения (для `APP_KEYS` нужно четыре ключа через запятую). Случайную строку можно получить так:

```bash
openssl rand -base64 16
```

Запустите Strapi в режиме разработки:

```bash
npm run develop
```

Админка откроется на `http://localhost:1337/admin`. При первом входе создайте администратора.

Описание коллекций хранится в репозитории и подхватится само. База данных в git не попадает, поэтому товары нужно завести заново: **Content Manager → Product**, заполнить данные и нажать **Publish**, иначе API их не вернёт.

### 4. API-токен Strapi

**Settings → API Tokens → Create new API Token**: имя `bot`, срок `Unlimited`, тип `Full access`. Токен показывается один раз, скопируйте его сразу.

### 5. Бот

```bash
cd bot
uv sync
```

Создайте файл `bot/.env`:

```
TG_BOT_TOKEN=токен_от_BotFather
STRAPI_URL=http://localhost:1337
STRAPI_TOKEN=токен_из_админки_Strapi
REDIS_HOST=localhost
REDIS_PORT=6379
```

`REDIS_PASSWORD` необязателен, нужен только для защищённого Redis. Файл `.env` содержит секреты и не должен попадать в git.

## Запуск

Нужны два терминала, Redis должен быть запущен.

**Терминал 1: Strapi**

```bash
cd cms
npm run develop
```

**Терминал 2: бот**

```bash
cd bot
uv run python src/bot/main.py
```

Откройте бота в Telegram и отправьте `/start`.

## Разработка

Форматирование и проверка кода:

```bash
cd bot
uv run ruff format .
uv run ruff check --fix .
```

Добавление зависимостей: `uv add имя_пакета`.
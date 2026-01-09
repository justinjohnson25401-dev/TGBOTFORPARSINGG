# 2GIS Database Sales Telegram Bot

Telegram-бот для продажи баз данных контактов 2GIS с автоматической оплатой через ЮMoney и доставкой файлов из Google Drive.

## Возможности

- Каталог баз данных по категориям (салоны красоты, автосервисы, медицина и т.д.)
- Автоматическая проверка оплаты через ЮMoney API
- Автоматическая доставка файлов после оплаты
- Система пакетов без дубликатов при повторных покупках
- Демо-файл для ознакомления
- FAQ и поддержка
- Админ-панель для управления

---

## Требования

- Python 3.10 или выше
- Telegram Bot Token (от @BotFather)
- Google Cloud Service Account с доступом к Google Drive
- ЮMoney кошелек с API-токеном
- Railway аккаунт (для деплоя)

---

## Пошаговая настройка

### 1. Создание Telegram бота

1. Откройте Telegram и найдите бота **@BotFather**
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "База данных 2GIS")
4. Введите username бота (например: `my2gisbot` - должен заканчиваться на `bot`)
5. Скопируйте полученный токен (выглядит как: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Настройка Google Drive

#### 2.1 Создание Service Account

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Перейдите в **APIs & Services** → **Library**
4. Найдите и включите **Google Drive API**
5. Перейдите в **APIs & Services** → **Credentials**
6. Нажмите **Create Credentials** → **Service Account**
7. Введите имя (например: `drive-bot-access`)
8. Нажмите **Create and Continue** → **Done**
9. Кликните на созданный Service Account
10. Перейдите на вкладку **Keys**
11. Нажмите **Add Key** → **Create new key** → **JSON**
12. Скачайте файл и переименуйте в `credentials.json`

#### 2.2 Настройка папок на Google Drive

1. Создайте папку для баз данных (например: "База Данных")
2. Создайте папку для демо-файла (например: "Демо База данных")
3. Откройте файл `credentials.json` и найдите поле `"client_email"` (например: `bot@project.iam.gserviceaccount.com`)
4. Откройте каждую папку на Google Drive
5. Нажмите **Поделиться** и добавьте email Service Account с правами **Читатель**
6. Скопируйте ID папок из URL (после `folders/`):
   - URL: `https://drive.google.com/drive/folders/1ABC123xyz`
   - ID: `1ABC123xyz`

#### 2.3 Загрузка файлов баз данных

Загрузите файлы в папку "База Данных" по следующей схеме именования:

```
{Город}_{Категория}_PACK_{НомерПакета}.xlsx
```

**Примеры:**
- `Moscow_SalonKrasoty_PACK_01.xlsx`
- `Moscow_SalonKrasoty_PACK_02.xlsx`
- `Moscow_Avtoservisy_PACK_01.xlsx`
- `SPB_Medicina_PACK_01.xlsx`

**Важно:**
- Каждый файл = 1000 контактов (1 пакет)
- Номер пакета с ведущим нулем: 01, 02, 03...
- Названия городов и категорий должны совпадать с конфигурацией бота

**Поддерживаемые категории:**
| Ключ | Название |
|------|----------|
| SalonKrasoty | Салоны красоты |
| Avtoservisy | Автосервисы |
| Medicina | Медицина |
| Restorany | Рестораны |

**Поддерживаемые города:**
| Ключ | Название |
|------|----------|
| Moscow | Москва |
| SPB | Санкт-Петербург |

#### 2.4 Демо-файл

Загрузите файл `DEMO.xlsx` в папку "Демо База данных" с примерами данных (можно с замаскированными контактами).

### 3. Настройка ЮMoney

#### 3.1 Получение Access Token

1. Перейдите на [yoomoney.ru/api/access-token](https://yoomoney.ru/api/access-token)
2. Или зарегистрируйте приложение на [yoomoney.ru/myservices/new](https://yoomoney.ru/myservices/new):
   - Название приложения: любое
   - Redirect URI: `https://localhost/callback`
   - Права: `operation-history` (просмотр истории операций)
3. Получите `client_id`
4. Авторизуйте приложение и получите `access_token`

#### 3.2 Получение Access Token вручную

Если у вас есть `client_id`, выполните в браузере:

```
https://yoomoney.ru/oauth/authorize?client_id=ВАШ_CLIENT_ID&response_type=code&redirect_uri=https://localhost/callback&scope=operation-history
```

После авторизации вы будете перенаправлены на URL вида:
```
https://localhost/callback?code=ВАШИЙ_КОД
```

Затем выполните POST-запрос для получения токена:

```bash
curl -X POST https://yoomoney.ru/oauth/token \
  -d "code=ВАШИЙ_КОД" \
  -d "client_id=ВАШ_CLIENT_ID" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=https://localhost/callback"
```

В ответе получите `access_token`.

### 4. Локальный запуск (Windows)

#### 4.1 Установка Python

1. Скачайте Python с [python.org](https://python.org/downloads/)
2. При установке отметьте галочку **"Add Python to PATH"**

#### 4.2 Подготовка проекта

1. Откройте командную строку (cmd) или PowerShell
2. Перейдите в папку проекта:
   ```
   cd C:\путь\к\TGBOTFORPARSINGG
   ```
3. Создайте виртуальное окружение:
   ```
   python -m venv venv
   ```
4. Активируйте окружение:
   ```
   venv\Scripts\activate
   ```
5. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

#### 4.3 Настройка переменных окружения

1. Скопируйте `.env.example` в `.env`:
   ```
   copy .env.example .env
   ```
2. Откройте `.env` в текстовом редакторе и заполните:
   ```
   BOT_TOKEN=ваш_токен_от_botfather
   ADMIN_IDS=ваш_telegram_user_id
   SUPPORT_USERNAME=ваш_username_без_собаки

   YOOMONEY_WALLET=ваш_номер_кошелька
   YOOMONEY_ACCESS_TOKEN=ваш_access_token
   YOOMONEY_CLIENT_ID=ваш_client_id

   GDRIVE_BASE_FOLDER_ID=id_папки_с_базами
   GDRIVE_DEMO_FOLDER_ID=id_папки_с_демо
   ```

#### 4.4 Добавление credentials.json

Скопируйте файл `credentials.json` (из шага 2.1) в корневую папку проекта.

#### 4.5 Запуск бота

```
python -m bot.main
```

Бот должен запуститься в режиме polling. Откройте его в Telegram и отправьте `/start`.

### 5. Деплой на Railway

#### 5.1 Подготовка

1. Создайте аккаунт на [railway.app](https://railway.app)
2. Установите [Railway CLI](https://docs.railway.app/develop/cli) (опционально)
3. Создайте новый проект в Railway

#### 5.2 Подключение GitHub репозитория

1. В Railway нажмите **New Project** → **Deploy from GitHub repo**
2. Выберите репозиторий с ботом
3. Railway автоматически определит Python-проект

#### 5.3 Настройка переменных окружения

В Railway перейдите в **Variables** и добавьте:

```
BOT_TOKEN=ваш_токен
ADMIN_IDS=ваш_telegram_id
SUPPORT_USERNAME=username_поддержки

YOOMONEY_WALLET=номер_кошелька
YOOMONEY_ACCESS_TOKEN=access_token
YOOMONEY_CLIENT_ID=client_id

GDRIVE_BASE_FOLDER_ID=id_папки_баз
GDRIVE_DEMO_FOLDER_ID=id_папки_демо

# Для работы через webhook
WEBHOOK_HOST=https://ваш-проект.railway.app
USE_WEBHOOK=true
```

#### 5.4 Добавление credentials.json

**Способ 1 (рекомендуемый):** Через переменную окружения

1. Откройте `credentials.json` и скопируйте содержимое
2. В Railway добавьте переменную `GDRIVE_CREDENTIALS_JSON` со значением содержимого файла
3. Измените код в `bot/services/gdrive.py` для чтения из переменной

**Способ 2:** Добавьте файл в репозиторий (не рекомендуется для публичных репозиториев)

#### 5.5 Деплой

1. Убедитесь, что файл `Procfile` содержит:
   ```
   web: python -m bot.main
   ```
2. Сделайте коммит и пуш в GitHub
3. Railway автоматически задеплоит обновления

---

## Структура проекта

```
TGBOTFORPARSINGG/
├── bot/
│   ├── config.py           # Конфигурация
│   ├── main.py             # Точка входа
│   ├── database/
│   │   ├── db.py           # Подключение к БД
│   │   └── models.py       # Модели данных
│   ├── handlers/
│   │   ├── start.py        # /start команда
│   │   ├── catalog.py      # Каталог
│   │   ├── purchase.py     # Покупка и оплата
│   │   ├── profile.py      # Профиль пользователя
│   │   ├── faq.py          # FAQ
│   │   ├── demo.py         # Демо-файл
│   │   ├── admin.py        # Админ-панель
│   │   └── custom_order.py # Заказ другого города
│   ├── keyboards/
│   │   └── inline.py       # Inline-кнопки
│   ├── services/
│   │   ├── yoomoney.py     # ЮMoney API
│   │   ├── gdrive.py       # Google Drive API
│   │   └── file_generator.py # Работа с файлами
│   └── utils/
│       └── helpers.py      # Вспомогательные функции
├── .env.example            # Пример переменных окружения
├── requirements.txt        # Зависимости Python
├── Procfile                # Для Railway
└── README.md               # Эта документация
```

---

## Как работает оплата

1. Пользователь выбирает категорию и количество контактов
2. Бот создает заказ и показывает ссылку на оплату ЮMoney
3. Пользователь переводит деньги на кошелек
4. В комментарии к платежу указывается номер заказа (автоматически)
5. Пользователь нажимает "Проверить оплату"
6. Бот проверяет историю операций ЮMoney
7. Если платеж найден — отправляет файлы

**Логика проверки платежа:**
- Точная сумма или переплата до 100₽ → ОК
- Переплата больше 100₽ → ОК с предупреждением
- Недоплата → Отказ с просьбой доплатить

---

## Добавление новых категорий/городов

Отредактируйте файл `bot/config.py`:

```python
CATEGORIES = {
    "SalonKrasoty": {"name": "Салоны красоты", "emoji": "💅"},
    "Avtoservisy": {"name": "Автосервисы", "emoji": "🚗"},
    "NovayaKategoriya": {"name": "Новая категория", "emoji": "🆕"},
}

CITIES = {
    "Moscow": {"name": "Москва"},
    "SPB": {"name": "Санкт-Петербург"},
    "Kazan": {"name": "Казань"},
}
```

Не забудьте загрузить соответствующие файлы на Google Drive!

---

## Устранение неполадок

### Бот не запускается

1. Проверьте, что все переменные в `.env` заполнены
2. Убедитесь, что `credentials.json` находится в корне проекта
3. Проверьте логи на наличие ошибок

### Файлы не скачиваются

1. Проверьте, что Service Account имеет доступ к папкам Google Drive
2. Убедитесь, что ID папок указаны правильно
3. Проверьте именование файлов

### Платеж не находится

1. Убедитесь, что `YOOMONEY_ACCESS_TOKEN` действителен
2. Платеж должен быть сделан в течение 30 минут после создания заказа
3. Сумма должна совпадать (или быть больше)

### Ошибка webhook

При локальном тестировании уберите `WEBHOOK_HOST` из `.env` или закомментируйте:
```
# WEBHOOK_HOST=...
# USE_WEBHOOK=true
```

---

## Поддержка

При возникновении проблем обращайтесь к @Oroani

---

## Лицензия

Частный проект. Все права защищены.

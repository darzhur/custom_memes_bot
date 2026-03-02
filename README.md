# 📦 Meme Bot + MCP + Supabase

## Общая архитектура

Проект состоит из трёх частей:

1. **Telegram-бот**

   * Получает фото
   * Загружает на Catbox
   * Генерирует подпись через ProxyAPI
   * Сохраняет результат в Supabase

2. **MCP (Model Context Protocol)**

   * FastAPI сервер
   * Парсит Memepedia
   * Отдаёт JSON с актуальными мемами
   * Используется как источник контекста

3. **Supabase**

   * Хранит мемы
   * Таблица `memes`
   * Используется через REST (PostgREST)

---

# 🧠 Логика работы

## 1️⃣ Telegram-бот

### Поток:

1. Пользователь отправляет фото
2. Фото:

   * скачивается
   * загружается на Catbox
3. MCP запрашивается для получения мемного контекста
4. ProxyAPI генерирует подпись
5. Сохраняем результат в Supabase

---

# 🌐 MCP сервер

## FastAPI

Запуск:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Если бот в Docker:

```
http://host.docker.internal:8000/memes
```

---

## Эндпоинты

### `GET /`

Проверка статуса:

```json
{
  "status": "MCP Memes server running"
}
```

---

### `GET /memes`

Возвращает массив мемов:

```json
[
  {
    "title": "Название мема",
    "url": "https://memepedia.ru/..."
  }
]
```

Используется ботом для формирования контекста.

---

# 🤖 ProxyAPI (генерация подписи)

### Важно

Для картинки **обязательно** передавать объект:

```json
{
  "type": "image_url",
  "image_url": {
    "url": "https://..."
  }
}
```

Текст с MCP-контекстом:

```python
{
  "type": "text",
  "text": f"Придумай смешную подпись:\n{mcp_context}"
}
```

---

# 🗄 Supabase

## Таблица `memes`

Обязательные поля:

| поле       | тип       |
| ---------- | --------- |
| id         | bigint    |
| image_url  | text      |
| caption    | text      |
| created_at | timestamp |

---

## Частая ошибка

### `PGRST204`

Причина: нет колонки `caption`.

### Решение:

1. Добавить колонку `caption` типа `text`
2. Нажать **Refresh Schema**
3. Перезапустить запрос

---

# 🔄 Интеграция

```
Telegram
   ↓
Catbox
   ↓
MCP (/memes)
   ↓
ProxyAPI
   ↓
Supabase (memes table)
```

---

# 🚨 Типовые проблемы

## MCP не отвечает

* Сервер не запущен
* Неверный host (в Docker нужен `host.docker.internal`)
* Не та директория при запуске

---

## ProxyAPI падает

* Картинка передана не объектом
* Неверная структура JSON

---

## Supabase ошибка

* Нет колонки
* Схема не обновлена
* Неверный ключ API

---

# 🧩 Минимальный рабочий стек

* Python 3.10+
* FastAPI
* requests
* beautifulsoup4
* python-telegram-bot / aiogram
* httpx / aiohttp
* Supabase REST

---

Проект сейчас:

* ✔ MCP работает
* ✔ Бот получает фото
* ✔ Контекст мемов подключён
* ✔ Подписи генерируются
* ✔ Данные сохраняются в Supabase

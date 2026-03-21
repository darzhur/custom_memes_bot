# 📦 Meme Bot + Supabase

## Общая архитектура

Проект состоит из одной части: **Telegram-бот**, который использует облачный Supabase как базу данных для мем-контекста и хранения сгенерированных мемов.

### Telegram-бот:

* Получает фото от пользователя
* Кодирует фото в base64
* Формирует контекст мемов из **memepedia** + **good_memes**
* Генерирует подписи через ProxyAPI
* Сохраняет результат в Supabase (`generated_memes`)
* Отправляет подписи пользователю

### Supabase:

* Хранит мем-контекст (`memepedia`)
* Хранит сгенерированные мемы (`generated_memes`)
* Хранит «хорошие мемы» для стиля и примеров (`good_memes`)

---

# 🧠 Логика работы

## Поток:

1. Пользователь отправляет фото в Telegram
2. Бот получает ссылку на фото через Telegram API
3. Берётся контекст мемов из Supabase (`memepedia` + `good_memes`)
4. ProxyAPI генерирует 3 подписи (с сарказмом, черным юмором и дерзким стилем)
5. Каждая подпись сохраняется в `generated_memes`
6. Подписи отправляются пользователю

---

# 🤖 ProxyAPI

## Важно для работы с изображением

Картинка передаётся как base64:

```json
{
  "type": "image_base64",
  "image_base64": "<тут_строка_с_base64>"
}
```

Текстовый контекст:

```json
{
  "type": "text",
  "text": "Придумай 3 саркастичные подписи:\n<контекст из memepedia + good_memes>"
}
```

---

# ⚡ Быстрый старт

### Локально

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

### FastAPI (если используется MCP для мем-контекста)

```bash
uvicorn app:app --reload
```

---

# 📌 Ссылка на бота

[@custom_memes_bot](https://t.me/custom_memes_bot)

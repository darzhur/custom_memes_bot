# context.py
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# создаём клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def build_context(limit: int = 5) -> str:
    """
    Формирует контекст мемов для генерации подписей.
    Возвращает строку с caption последних 'good_memes'.
    """
    try:
        # execute() возвращает синхронный ответ, поэтому async не нужен
        resp = supabase.table("good_memes") \
            .select("caption, tags") \
            .order("score", desc=True) \
            .limit(limit) \
            .execute()

        data = resp.data if resp.data else []

        # формируем контекст
        lines = []
        for i, m in enumerate(data, 1):
            caption = m.get("caption", "").strip()[:120]
            tags = m.get("tags", "")
            lines.append(f"{i}. {caption} ({tags})")

        return "\n".join(lines) if lines else "сарказм, черный юмор, дерзко"

    except Exception as e:
        print("Ошибка build_context:", e)
        return "сарказм, черный юмор, дерзко"
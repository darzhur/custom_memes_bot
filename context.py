# context.py
def build_context(limit: int = 5) -> str:
    try:
        resp = supabase.table("good_memes") \
            .select("caption, tags") \
            .order("score", desc=True) \
            .limit(limit) \
            .execute()  # синхронный вызов

        data = resp.data if resp.data else []

        lines = []
        for i, m in enumerate(data, 1):
            caption = m.get("caption", "").strip()[:120]
            tags = m.get("tags", "")
            lines.append(f"{i}. {caption} ({tags})")

        return "\n".join(lines) if lines else "сарказм, черный юмор, дерзко"

    except Exception as e:
        print("Ошибка build_context:", e)
        return "сарказм, черный юмор, дерзко"
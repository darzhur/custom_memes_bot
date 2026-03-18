from supabase.client import AsyncClient

async def build_context(supabase: AsyncClient, limit: int = 5):
    good = await supabase.table("good_memes")\
        .select("caption, tags")\
        .limit(limit)\
        .execute()

    memepedia = await supabase.table("memepedia")\
        .select("title, content")\
        .limit(limit)\
        .execute()

    context = []

    if good.data:
        context.append("Примеры мемов:")
        for m in good.data:
            context.append(f"- {m['caption']} ({m.get('tags','')})")

    if memepedia.data:
        context.append("\nЗнания:")
        for m in memepedia.data:
            text = (m.get("content") or "")[:100]
            context.append(f"- {m['title']}: {text}")

    return "\n".join(context) or "сарказм, черный юмор"
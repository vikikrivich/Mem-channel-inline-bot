import re
from supabase import Client

# Стоп-слова можно не фильтровать строго, но убрать мусор и спецсимволы стоит
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", re.UNICODE)


def parse_query_words(query: str) -> list[str]:
    """Разбивает запрос пользователя на список слов в нижнем регистре."""
    clean_text = PUNCTUATION_REGEX.sub(" ", query.lower())
    words = [w.strip() for w in clean_text.split() if len(w.strip()) > 1]
    return list(set(words))


def search_memes(supabase: Client, query: str) -> list[dict]:
    query_words = parse_query_words(query)
    if not query_words:
        return []

    # 1. Поиск по пересечению массивов тегов (overlaps / оператор && в PostgreSQL)
    # Находит все записи, у которых в массиве `tags` есть ХОТЯ БЫ ОДНО слово из query_words
    try:
        response = (
            supabase.table("memes")
            .select("id, photo_file_id, caption, tags")
            .overlaps("tags", query_words)
            .limit(50)
            .execute()
        )
        items = response.data or []
    except Exception:
        items = []

    # 2. Если по тегам ничего не нашли, делаем fallback на текстовый поиск по подписи (caption)
    if not items:
        # Ищем по каждому слову через ilike
        filters = [f"caption.ilike.%{w}%" for w in query_words]
        response = (
            supabase.table("memes")
            .select("id, photo_file_id, caption, tags")
            .or_(",".join(filters))
            .limit(30)
            .execute()
        )
        items = response.data or []

    if not items:
        return []

    # 3. Сортировка по релевантности (ранжирование)
    # Чем больше слов из запроса пользователя найдено в тегах или подписи, тем выше результат
    query_set = set(query_words)

    def calculate_score(item: dict) -> int:
        meme_tags = set(item.get("tags") or [])
        # Количество совпавших тегов
        score = len(query_set.intersection(meme_tags)) * 2
        
        # Дополнительные очки, если слово целиком встречается в тексте caption
        caption_lower = (item.get("caption") or "").lower()
        for word in query_words:
            if word in caption_lower:
                score += 1
        return score

    # Сортируем от большего числа совпадений к меньшему
    items.sort(key=calculate_score, reverse=True)

    return items[:20]
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from supabase import Client

# Скачиваем список стоп-слов при первом запуске
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

stemmer = SnowballStemmer("russian")
# Исключаем 'не' и 'нет' из стоп-слов, так как для мемов они критически важны
STOP_WORDS = set(stopwords.words("russian")) - {"не", "нет"}
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", re.UNICODE)


def stem_word(word: str) -> str:
    """Обрезает окончание слова до основы."""
    return stemmer.stem(word.strip().lower())


def extract_stems(text: str) -> list[str]:
    """Разбивает текст на слова, убирает стоп-слова и возвращает основы (стемы)."""
    clean_text = PUNCTUATION_REGEX.sub(" ", text.lower())
    words = clean_text.split()
    
    stems = []
    for w in words:
        w = w.strip()
        if len(w) > 1 and w not in STOP_WORDS:
            stems.append(stem_word(w))
    return list(set(stems))


def search_memes(supabase: Client, query: str) -> list[dict]:
    # 1. Получаем основы слов из запроса пользователя
    # Например: "я не договорила" -> ["не", "договор"]
    query_stems = extract_stems(query)
    if not query_stems:
        return []

    # 2. Ищем в Supabase по подстроке (ilike) в caption или tags.
    # Так как мы ищем по основе ("договор"), ilike найдет и "договорила", и "договорились"
    caption_filters = [f"caption.ilike.%{stem}%" for stem in query_stems]
    # Приведение массива тегов к строке для поиска подстроки через ilike
    tags_filters = [f"tags.cs.{{{stem}}}" for stem in query_stems]

    all_filters = caption_filters + [f"caption.ilike.%{stem}%" for stem in query_stems]

    items = []
    try:
        # Ищем записи, где хотя бы одна основа встречается в caption
        # Для охвата тегов используется оператор ilike по caption
        response = (
            supabase.table("memes")
            .select("id, photo_file_id, caption, tags")
            .or_(",".join(caption_filters))
            .limit(60)
            .execute()
        )
        items = response.data or []
    except Exception:
        items = []

    # Если через caption ничего не нашлось, делаем поиск по точному совпадению основ в тегах
    if not items:
        try:
            response = (
                supabase.table("memes")
                .select("id, photo_file_id, caption, tags")
                .overlaps("tags", query_stems)
                .limit(60)
                .execute()
            )
            items = response.data or []
        except Exception:
            items = []

    if not items:
        return []

    # 3. Ранжирование по релевантности
    query_stems_set = set(query_stems)

    def calculate_score(item: dict) -> int:
        score = 0
        
        # Стеммим теги мема на лету и ищем пересечения
        raw_tags = item.get("tags") or []
        meme_tag_stems = {stem_word(t) for t in raw_tags if t}
        score += len(query_stems_set.intersection(meme_tag_stems)) * 3

        # Проверяем вхождение основ слов в caption
        caption_lower = (item.get("caption") or "").lower()
        for stem in query_stems:
            if stem in caption_lower:
                score += 2

        return score

    # Сортируем от наиболее подходящих к наименее подходящим
    items.sort(key=calculate_score, reverse=True)

    return items[:50]
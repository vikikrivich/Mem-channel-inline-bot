import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from supabase import Client

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", quiet=True)

stemmer = SnowballStemmer("russian")
STOP_WORDS = set(stopwords.words("russian")) - {"не", "нет"}
PUNCTUATION_REGEX = re.compile(r"[^\w\s]", re.UNICODE)


def stem_word(word: str) -> str:
    return stemmer.stem(word.strip().lower())


def extract_stems(text: str) -> list[str]:
    clean_text = PUNCTUATION_REGEX.sub(" ", text.lower())
    words = clean_text.split()
    stems = []
    for w in words:
        w = w.strip()
        if len(w) > 1 and w not in STOP_WORDS:
            stems.append(stem_word(w))
    return list(dict.fromkeys(stems))  # сохраняем порядок, убираем дубли


def search_memes(supabase: Client, query: str) -> list[dict]:
    clean_query = PUNCTUATION_REGEX.sub(" ", query.lower()).strip()
    if not clean_query:
        return []

    query_stems = extract_stems(query)
    if not query_stems:
        return []

    # 1. Формируем единый OR-фильтр: поиск по подстроке в caption + вхождение в массив tags
    caption_filters = [f"caption.ilike.%{stem}%" for stem in query_stems]
    # tags.ov.{stem1,stem2} проверяет пересечение массива тегов со стемами
    tags_filter = f"tags.ov.{{{','.join(query_stems)}}}"
    
    # Также ищем точное вхождение всей фразы целиком в caption
    exact_phrase_filter = f"caption.ilike.%{clean_query}%"
    
    or_condition = ",".join([exact_phrase_filter] + caption_filters + [tags_filter])

    try:
        # Увеличиваем лимит выборки до 200, чтобы высокочастотные слова не вытесняли точные совпадения
        response = (
            supabase.table("memes")
            .select("id, photo_file_id, caption, tags")
            .or_(or_condition)
            .limit(200)
            .execute()
        )
        items = response.data or []
    except Exception:
        items = []

    if not items:
        return []

    # 2. Ранжирование
    query_stems_set = set(query_stems)

    def calculate_score(item: dict) -> int:
        score = 0
        caption = (item.get("caption") or "").lower()
        raw_tags = item.get("tags") or []
        meme_tag_stems = {stem_word(t) for t in raw_tags if t}

        # Огромный бонус за точное совпадение фразы целиком
        if clean_query in caption:
            score += 100

        # Бонус за совпадение отдельных стемов в caption
        matched_stems_caption = 0
        for stem in query_stems:
            if stem in caption:
                score += 5
                matched_stems_caption += 1

        # Бонус, если ВСЕ слова из запроса нашлись в caption
        if matched_stems_caption == len(query_stems):
            score += 25

        # Совпадения по тегам
        matched_tags = query_stems_set.intersection(meme_tag_stems)
        score += len(matched_tags) * 8

        return score

    items.sort(key=calculate_score, reverse=True)
    return items[:50]
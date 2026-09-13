import random
from supabase import Client
from utils.logger import logger


def get_random_meme(supabase: Client) -> dict | None:
    """Возвращает один случайный мем из базы данных Supabase."""
    try:
        # Способ через RPC, если в базе есть функция getRandom
        # Либо через подсчет общего числа строк:
        count_response = (
            supabase.table("memes")
            .select("id", count="exact")
            .limit(1)
            .execute()
        )
        total_count = count_response.count or 0

        if total_count == 0:
            return None

        # Генерируем случайный индекс строки
        random_index = random.randint(0, total_count - 1)

        # Запрашиваем ровно одну строку со случайным смещением
        response = (
            supabase.table("memes")
            .select("id, photo_file_id")
            .range(random_index, random_index)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as e:
        logger.error(f"Ошибка при получении случайного мема: {e}")
        return None
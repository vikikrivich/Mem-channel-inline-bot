import re
from aiogram import Router, F
from aiogram.types import Message
from supabase import Client

from utils.logger import logger

router = Router()

STOP_WORDS = {
    "и", "а", "но", "в", "во", "на", "с", "со", "к", "по", "у",
    "о", "об", "за", "из", "до", "от", "для", "не", "ни", "то", "же"
}


def extract_tags(text: str) -> list[str]:
    """Разбивает подпись на отдельные слова-теги."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower())
    return list({w for w in words if w not in STOP_WORDS and len(w) > 1})


@router.channel_post(F.photo)
async def handle_new_channel_photo(message: Message, supabase: Client):
    """
    Срабатывает автоматически при выходе нового поста с фото в канале,
    где бот является администратором.
    """
    caption = message.caption or ""
    if not caption.strip():
        logger.info(f"Новый пост #{message.message_id} без подписи, пропуск.")
        return

    tags = extract_tags(caption)
    best_photo = message.photo[-1]
    file_id = best_photo.file_id

    data_payload = {
        "channel_message_id": message.message_id,
        "caption": caption,
        "tags": tags,
        "photo_file_id": file_id,
    }

    try:
        supabase.table("memes").upsert(
            data_payload,
            on_conflict="channel_message_id"
        ).execute()
        logger.info(f"Автоматически сохранён новый мем #{message.message_id} | Теги: {tags[:5]}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении нового поста #{message.message_id} в Supabase: {e}")
import asyncio
import re
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from supabase import create_client, Client

from utils.logger import logger
from utils.settings import settings

START_MSG_ID = 1
END_MSG_ID = 15  # укажите номер последнего поста в канале


def extract_tags(text: str) -> list[str]:
    """Разбивает строку на отдельные слова-теги."""
    if not text:
        return []
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower())
    return list({w for w in words if len(w) > 1})


async def run_parser():
    settings.load_from_dotenv()

    if not settings.TOKEN or not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.error("Не заполнены обязательные переменные в .env")
        return

    if not settings.CHANNEL_ID or not settings.MY_TELEGRAM_ID:
        logger.error("Укажите CHANNEL_ID и MY_TELEGRAM_ID в .env файле")
        return

    bot = Bot(token=settings.TOKEN)
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    logger.info(f"Старт парсинга сообщений с {START_MSG_ID} по {END_MSG_ID}...")
    saved_count = 0

    for msg_id in range(START_MSG_ID, END_MSG_ID + 1):
        try:
            # Пересылаем пост ботом в ваш личный чат, чтобы получить объект Message с photo.file_id
            forwarded = await bot.forward_message(
                chat_id=settings.MY_TELEGRAM_ID,
                from_chat_id=settings.CHANNEL_ID,
                message_id=msg_id
            )

            # Если у сообщения есть картинка и подпись
            if forwarded.photo and forwarded.caption:
                caption = forwarded.caption
                tags = extract_tags(caption)
                best_photo = forwarded.photo[-1]

                data_payload = {
                    "channel_message_id": msg_id,
                    "caption": caption,
                    "tags": tags,
                    "photo_file_id": best_photo.file_id,
                }

                supabase.table("memes").upsert(
                    data_payload,
                    on_conflict="channel_message_id"
                ).execute()

                saved_count += 1
                logger.info(f"[{saved_count}] Сохранен мем #{msg_id} | Теги: {tags[:4]}")

            # Удаляем пересланное сообщение, чтобы не засорять чат
            await bot.delete_message(
                chat_id=settings.MY_TELEGRAM_ID,
                message_id=forwarded.message_id
            )

            # Задержка 0.25 сек во избежание flood-limit от Telegram
            await asyncio.sleep(0.25)

        except TelegramBadRequest:
            # Пустое/удаленное сообщение или служебный сервисный лог — пропускаем
            continue
        except TelegramRetryAfter as e:
            logger.warning(f"Флуд-контроль: пауза {e.retry_after} сек.")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logger.error(f"Ошибка при обработке поста #{msg_id}: {e}")

    await bot.session.close()
    logger.info(f"Парсинг завершен! Успешно сохранено: {saved_count} мемов.")


if __name__ == "__main__":
    asyncio.run(run_parser())
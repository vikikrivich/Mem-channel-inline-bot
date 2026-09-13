import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters.command import Command
from aiogram.types import InlineQuery, InlineQueryResultCachedPhoto
from aiogram.exceptions import TelegramBadRequest
from supabase import create_client, Client

from services.db import search_memes
from services.handler_new import router as channel_router
from services.random import get_random_meme
from utils.logger import logger
from utils.settings import settings


async def main():
    settings.load_from_dotenv()

    session = None
    if getattr(settings, "PROXY_URL", None):
        session = AiohttpSession(proxy=settings.PROXY_URL)

    bot = Bot(token=settings.TOKEN, session=session)
    dp = Dispatcher()

    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    dp["supabase"] = supabase
    dp.include_router(channel_router)

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(
            "Привет! Бот активен и следит за каналом.\n\n"
            "• Команда /random — прислать случайный мем прямо сюда\n"
            "• В любом чате пиши `@mem_find_bot <слово>` для поиска\n"
            "• Или `@mem_find_bot random` для случайного мема в инлайне."
        )

    @dp.message(Command("random"))
    async def cmd_random(message: types.Message):
        """Отправляет случайный мем в личный чат."""
        meme = await asyncio.to_thread(get_random_meme, supabase)
        if not meme or not meme.get("photo_file_id"):
            await message.answer("В базе пока нет мемов или произошла ошибка.")
            return

        await message.answer_photo(
            photo=meme["photo_file_id"]
        )

    @dp.inline_query()
    async def handle_inline_query(inline_query: InlineQuery):
        query = inline_query.query.strip().lower()

        # Если запрос пустой — отдаем пустой результат с коротким кэшем
        if not query:
            try:
                await inline_query.answer([], cache_time=5, is_personal=True)
            except TelegramBadRequest:
                pass
            return

        # Если пользователь набрал "random" или "рандом" в инлайн-поиске
        if query in ["random", "рандом"]:
            meme = await asyncio.to_thread(get_random_meme, supabase)
            results = []
            if meme and meme.get("photo_file_id"):
                results.append(
                    InlineQueryResultCachedPhoto(
                        id=str(meme["id"]),
                        photo_file_id=meme["photo_file_id"]
                    )
                )
            try:
                # cache_time=1, чтобы при каждом открытии выдавался действительно новый случайный мем
                await inline_query.answer(results, cache_time=1, is_personal=True)
            except TelegramBadRequest:
                pass
            return

        # Стандартный поиск по тегам
        items = await asyncio.to_thread(search_memes, supabase, query)

        results = [
            InlineQueryResultCachedPhoto(
                id=str(item["id"]),
                photo_file_id=item["photo_file_id"]
            )
            for item in items[:50]
        ]

        try:
            await inline_query.answer(results, cache_time=30, is_personal=True)
        except TelegramBadRequest as e:
            if "query is too old" in str(e):
                logger.warning("Запрос устарел и был пропущен")
            else:
                raise

    logger.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters.command import Command
from aiogram.types import InlineQuery, InlineQueryResultCachedPhoto
from aiogram.exceptions import TelegramBadRequest
from supabase import create_client, Client

from services.db import search_memes
from services.handler_new import router as channel_router
from utils.logger import logger
from utils.settings import settings


async def main():
    settings.load_from_dotenv()

    # proxi
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
            "Привет! Бот активен и следит за каналом.\n"
            "Ищи мемы в любом чате через `@test_vikikrivich_bot <слово>`."
        )

    @dp.inline_query()
    async def handle_inline_query(inline_query: InlineQuery):
        query = inline_query.query.strip()
        if not query:
            try:
                await inline_query.answer([], cache_time=10, is_personal=True)
            except TelegramBadRequest:
                pass
            return

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
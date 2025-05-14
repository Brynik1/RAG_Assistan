import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

import asyncio
from dotenv import load_dotenv
from app.RAGOpenAiPipeline import RAGOpenAiPipeline

from handlers.commands import router as commands_router
from handlers.messages import router as messages_router

load_dotenv()


async def main() -> None:
    storage = MemoryStorage()
    user_tokens = {}

    pipeline = RAGOpenAiPipeline(
        vector_storage_kwargs={'chunk_size': 800, 'chunk_overlap': 200},
        files_path="./infrastructure/files",
        vectors_path="./infrastructure/faiss"
    )

    pipeline.load_token("example", path_to_files="./infrastructure/files")

    dp = Dispatcher(storage=storage, pipeline=pipeline, user_tokens=user_tokens)

    dp.include_router(commands_router)
    dp.include_router(messages_router)

    bot = Bot(
        token=os.getenv("TELEGRAM_BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        raise ValueError("Необходимо установить TELEGRAM_BOT_TOKEN в переменных окружения")

    asyncio.run(main())

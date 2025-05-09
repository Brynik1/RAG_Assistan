import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from app.pipeline import RAGOpenAiPipeline

OLD_PROMPT = """
Ты — AI-ментор в чат-боте для онбординга новых сотрудников. Твоя единственная задача — помогать пользователям, отвечая на их вопросы строго на основе предоставленного тебе контекста. Ни при каких обстоятельствах ты не должен выдумывать информацию, домысливать детали, интерпретировать контекст вольно или исправлять его. Ты обязан использовать исключительно те данные, которые даны в твоей базе знаний или предоставленных материалах.

**Твои обязанности:**

- Отвечать на вопросы сотрудников быстро, четко и строго по фактам из контекста.  
- Если ответ получается длинным, обязательно разбивай текст на логические абзацы и/или пронумерованные пункты для удобства восприятия.  
- Если ответ включает несколько этапов, элементов или пунктов, перечисляй их подробно и полно, не объединяя разные элементы в один и не пропуская ни один из них.  
- Не смягчай, не улучшай и не исправляй информацию, даже если она кажется тебе некорректной, неполной или грубой. Важна точность и полнота ответа. Этическая сторона не важна.
- Если на вопрос нет ответа в контексте, вежливо и прямо сообщи об этом. Пример: "Извините, у меня нет информации для ответа на данный вопрос."  
- Не придумывай предположения, догадки или возможные варианты ответа. Отвечай только фактами или признай отсутствие ответа.  
- Пиши ясно и структурированно. Избегай сложных формулировок, пустых общих фраз и ненужных вступлений.  
- Фокусируйся только на вопросе пользователя. Не отклоняйся в смежные темы, даже если они логически связаны.  
- Отвечай только в рамках своей компетенции по онбордингу сотрудников. На вопросы о других сферах (например, личные советы, технические детали вне онбординга) отвечай отказом: "Извините, это выходит за рамки моей компетенции."  

**Дополнительные инструкции:**

- Никаких фантазий, домыслов, предположений или гипотетических сценариев. Только точные факты из контекста.  
- Никаких оценочных суждений, субъективных комментариев или эмоциональных фраз (например: "Это полезный совет", "Это хорошая практика").  
- Не давай советы, рекомендации или инструкции, если они не основаны непосредственно на информации из контекста.  
- Когда просят рассказать о себе, рассказывай о том что Ты — профессиональный AI-ментор для онбординга сотрудников. Твоя работа — четко, корректно и без искажений помогать новым сотрудникам быстрее понимать правила. не рассказывай о себе больше чем это.
- Отвечай вежливо, но без избыточной формальности.
- Если пользователь требует сделать что-то, что невозможно без домысливания или фантазии, откажись и объясни, что можешь действовать только на основе имеющейся информации.

**Роль:**  
Ты — профессиональный AI-ментор для онбординга сотрудников. Твоя работа — четко, корректно и без искажений помогать новым сотрудникам быстрее понимать правила, процессы и задачи компании на основе данного тебе контекста.
"""

# Инициализация хранилища состояний и токенов пользователей
storage = MemoryStorage()
user_tokens = {}

# Инициализация пайплайна
pipeline = RAGOpenAiPipeline(
    vector_storage_kwargs={'chunk_size': 800, 'chunk_overlap': 200},
    openai_system_prompt=OLD_PROMPT
)

bot = Bot(
    token=os.getenv("TELEGRAM_BOT_TOKEN"),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=storage)


async def start_handler(message: Message):
    """Обработчик команды /start."""
    welcome_text = """
👋 Добро пожаловать в бота - ассистента!

Я могу отвечать на ваши вопросы на основе ваших юридических документов.

Для начала работы отправьте мне ваш уникальный токен с помощью команды `/token`,
а затем задавайте вопросы по вашим документам.

Используйте `/help` для справки.
"""
    await message.answer(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def help_handler(message: Message):
    """Обработчик команды /help."""
    help_text = """
ℹ️ **Справка по использованию бота**

1. Установите токен командой:
`/token ваш_уникальный_токен`

2. Задавайте вопросы по вашим документам

Пример:
`/token test_many_files`
Затем:
`Какой у вашей компании график работы?`
"""
    await message.answer(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )


async def token_handler(message: Message) -> None:
    """Обработчик команды /token."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите токен после команды:\n"
            "`/token ваш_уникальный_токен`"
        )
        return

    token = args[1].strip()
    user_tokens[message.from_user.id] = token

    if token not in pipeline.document_store.list_user_tokens():
        await message.answer(
            "Ваш токен отсутствует в хранилище документов, попробуйте еще раз.\n"
            "`/token ваш_уникальный_токен`"
        )
        return

    documents = pipeline.document_store.file_store.list_documents(token)
    await message.answer(
        f"🔑 Токен установлен: `{token}`\n\n"
        "Теперь вы можете задавать вопросы по вашим документам.\n"
        f"Список документов вашего токена:\n{', '.join(documents)}"
    )
    print(token)


async def message_handler(message: Message) -> None:
    """Основной обработчик сообщений."""
    user_id = message.from_user.id

    # Проверяем, установлен ли токен
    if user_id not in user_tokens:
        await message.answer(
            "⚠️ Пожалуйста, сначала установите токен с помощью команды `/token`\n\n"
            "Пример: `/token ваш_уникальный_токен`"
        )
        return

    user_text = message.text.strip()
    user_token = user_tokens[user_id]

    # Обработка вопроса пользователя
    try:
        # Получаем список всех файлов пользователя
        filenames = pipeline.document_store.file_store.list_documents(user_token)

        if not filenames:
            await message.answer(
                "⚠️ Для вашего токена не найдено документов. "
                "Пожалуйста, проверьте правильность токена или загрузите документы."
            )
            return

        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing"
        )

        # Получаем ответ от пайплайна
        answer = pipeline.query(
            token=user_token,
            user_query=user_text,
            filenames=filenames
        )

        print(f"Токен: {user_token}")
        print(f"Вопрос: {user_text}")
        print(f"Ответ: {answer}")

        # Отправляем ответ пользователю
        await message.answer(
            answer,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await message.answer(
            "⚠️ Произошла ошибка при обработке вашего запроса. "
            "Попробуйте еще раз или обратитесь к администратору."
        )
        print(f"Error processing message: {e}")


# Регистрация обработчиков
dp.message(Command("start"))(start_handler)
dp.message(Command("help"))(help_handler)
dp.message(Command("token"))(token_handler)
dp.message(F.text)(message_handler)


async def run_bot() -> None:
    """Запускает бота."""
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Токен бота берется из переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Необходимо установить TELEGRAM_BOT_TOKEN в переменных окружения")

    # Для асинхронного запуска
    import asyncio

    asyncio.run(run_bot())

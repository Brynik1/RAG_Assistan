from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(Command(commands=['start']))
async def start_handler(message: Message):
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


@router.message(Command(commands=['help']))
async def help_handler(message: Message):
    """Обработчик команды /help."""
    help_text = """
ℹ️ **Справка по использованию бота**

1. Установите токен командой:
`/token ваш_уникальный_токен`

2. Задавайте вопросы по вашим документам

Пример:
`Какой у вашей компании график работы?`
"""
    await message.answer(
        help_text,
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['token']))
async def token_handler(message: Message, user_tokens, pipeline) -> None:
    """Обработчик команды /token."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите токен после команды:\n"
            "`/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    token = args[1].strip()
    if token not in pipeline.document_store.list_user_tokens():
        await message.answer(
            "Ваш токен отсутствует в хранилище документов, попробуйте еще раз.\n"
            "`/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        user_tokens.pop(message.from_user.id, None)
        return

    user_tokens[message.from_user.id] = token

    documents = pipeline.document_store.file_store.list_documents(token)
    await message.answer(
        f"🔑 Токен установлен: `{token}`\n\n"
        "Теперь вы можете задавать вопросы по вашим документам.\n"
        f"📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['documents']))
async def documents_handler(message: Message, user_tokens, pipeline) -> None:
    """Показывает список документов пользователя."""
    if message.from_user.id not in user_tokens:
        await message.answer(
            "⚠️ Пожалуйста, сначала установите токен с помощью команды `/token`\n\n"
            "Пример: `/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    token = user_tokens[message.from_user.id]
    documents = pipeline.document_store.list_documents(token)

    if not documents:
        await message.answer("Для вашего токена документы не найдены")
        return

    await message.answer(
        f"📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )
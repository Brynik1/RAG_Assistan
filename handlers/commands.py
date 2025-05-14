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
    user_tokens[message.from_user.id] = token
    if token not in pipeline.document_store.list_user_tokens():
        await message.answer(
            "Ваш токен отсутствует в хранилище документов, попробуйте еще раз.\n"
            "`/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    documents = pipeline.document_store.file_store.list_documents(token)
    await message.answer(
        f"🔑 Токен установлен: `{token}`\n\n"
        "Теперь вы можете задавать вопросы по вашим документам.\n"
        f"Список документов вашего токена:\n{', '.join(documents)}",
        parse_mode=ParseMode.MARKDOWN
    )

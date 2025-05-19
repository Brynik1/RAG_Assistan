from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(Command(commands=['start']))
async def start_handler(message: Message, user_tokens, pipeline):
    welcome_text = """
👋 Добрый день! Я ваш персональный ассистент Эмили!

Я помогу вам быстро находить информацию в ваших документах. Просто задайте вопрос в свободной форме, например:
   • Какой график работы в компании?
"""
    token = "example"

    user_tokens[message.from_user.id] = token

    documents = pipeline.list_documents(token)
    await message.answer(
        welcome_text + f"\n📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['help']))
async def help_handler(message: Message):
    """Обработчик команды /help. Предоставляет полную справку по функционалу бота."""
    help_text = """
📚 *Полное руководство по функциям*

🔹 *Основные команды:*
`/start` - Начало работы с ботом
`/help` - Это руководство
`/token [ваш_токен]` - Установить ваш персональный токен доступа
`/documents` - Показать список ваших документов

🔹 *Как работать с ботом:*
1. Сначала установите ваш токен:
`/token 12345abcde`

2. Затем можете задавать вопросы по вашим документам:
   • Какой график работы в компании?
   • Основные правила противопожарной безопасности?
   • Положение о коммерческой тайне?

🔹 *Особенности работы:*
   • Бот анализирует только ваши документы
   • Ответы формируются на основе загруженных файлов
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

    documents = pipeline.list_documents(token)
    await message.answer(
        f"🔑 Токен установлен: `{token}`\n\n"
        "Теперь вы можете задавать вопросы по вашим документам.\n\n"
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
    documents = pipeline.list_documents(token)

    if not documents:
        await message.answer("Для вашего токена документы не найдены")
        return

    await message.answer(
        f"📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )
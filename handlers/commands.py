from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
import os
from dotenv import load_dotenv
from app.text_utils import TextProcessor

load_dotenv()  # Загружаем переменные окружения

router = Router()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


@router.message(Command(commands=['start']))
async def start_handler(message: Message, user_tokens, pipeline):
    welcome_text = """
👋 Добрый день! Я ваш персональный ассистент Эмили!

Я помогу вам быстро находить информацию в ваших документах. 

Для начала работы необходимо установить ваш токен с помощью команды:
`/token ваш_уникальный_токен`

Примеры вопросов после установки токена:
• Какой график работы в компании?
• Основные правила безопасности?
"""
    await message.answer(
        welcome_text,
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

    # Сохраняем токен с учетом возможных админских прав
    if isinstance(user_tokens.get(message.from_user.id), dict):
        user_tokens[message.from_user.id]['token'] = token
    else:
        user_tokens[message.from_user.id] = {
            'token': token,
            'is_admin': False
        }

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

    token = user_tokens[message.from_user.id]['token']
    documents = pipeline.list_documents(token)

    if not documents:
        await message.answer("Для вашего токена документы не найдены")
        return

    await message.answer(
        f"📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['admin']))
async def admin_handler(message: Message, user_tokens, pipeline) -> None:
    """Обработчик команды /admin для получения прав администратора."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Для получения прав администратора введите:\n"
            "`/admin ваш_пароль`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    password = args[1].strip()
    if password != ADMIN_PASSWORD:
        await message.answer("❌ Неверный пароль администратора")
        return

    # Помечаем пользователя как администратора
    user_tokens[message.from_user.id] = {
        'token': user_tokens.get(message.from_user.id, 'example'),
        'is_admin': True
    }

    await message.answer(
        "🔓 Вы получили права администратора!\n\n"
        "Доступные команды:\n"
        "• /create\_token - создать новый токен\n"
        "• /add\_file - добавить файл к токену\n"
        "• /shutdown - выключение бота\n"
        "• Все обычные команды",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['info']))
async def info_handler(message: Message, user_tokens, pipeline) -> None:
    """Обработчик команды /info - вывод информации о пользователе"""
    user_id = message.from_user.id

    # Получаем информацию о пользователе
    user_info = {
        'username': message.from_user.username,
        'full_name': message.from_user.full_name,
        'user_id': user_id,
        'is_admin': False,
        'token': None,
        'documents': []
    }

    # Проверяем наличие токена
    if user_id in user_tokens:
        user_data = user_tokens[user_id]

        # Обрабатываем как старый формат (просто токен), так и новый (словарь)
        if isinstance(user_data, dict):
            user_info['token'] = user_data.get('token')
            user_info['is_admin'] = user_data.get('is_admin', False)
        else:
            user_info['token'] = user_data

    # Получаем список документов, если есть токен
    if user_info['token']:
        user_info['documents'] = pipeline.list_documents(user_info['token'])

    # Формируем ответ
    response_text = "📋 <b>Информация о пользователе:</b>\n\n" + \
        f"👤 <b>Username:</b> @{user_info['username'] or user_info['full_name']}\n"+ \
        f"🆔 <b>User ID:</b> <code>{user_info['user_id']}</code>\n"+ \
        f"🔑 <b>Токен:</b> <code>{user_info['token'] or 'не установлен'}</code>\n"+ \
        f"🛡 <b>Админ:</b> {'✅ да' if user_info['is_admin'] else '❌ нет'}\n\n"


    # Добавляем информацию о документах
    if user_info['token']:
        token = user_tokens[message.from_user.id]['token']
        documents = pipeline.list_documents(token)

        response_text += f"\n📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents)

    else:
        response_text += "\n⚠️ Для просмотра документов необходимо установить токен:\n<code>/token ваш_токен</code>"

    await message.answer(
        response_text,
        parse_mode=ParseMode.HTML
    )

@router.message(Command(commands=['shutdown']))
async def shutdown_handler(message: Message, user_tokens) -> None:
    """Обработчик команды /shutdown для выключения бота."""
    user_data = user_tokens.get(message.from_user.id, {})
    if not user_data.get('is_admin', False):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    await message.answer("🛑 Выключаю бота...")
    raise SystemExit(0)


@router.message(Command(commands=['create_token']))
async def create_token_handler(message: Message, user_tokens, pipeline) -> None:
    """Создание нового токена (только для администраторов)"""
    user_data = user_tokens.get(message.from_user.id, {})
    if not user_data.get('is_admin', False):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите токен для создания:\n"
            "`/create_token новый_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    token = args[1].strip()
    if token in pipeline.document_store.list_user_tokens():
        await message.answer(f"❌ Токен `{token}` уже существует", parse_mode=ParseMode.MARKDOWN)
        return

    # Создаем пустые директории для токена
    pipeline.document_store.file_store.add_document(token, "__init__.txt", "Initial file")
    pipeline.document_store.vector_store.load_for_user(token)

    await message.answer(f"✅ Токен `{token}` успешно создан", parse_mode=ParseMode.MARKDOWN)


@router.message(Command(commands=['add_file']))
async def add_file_handler(message: Message, user_tokens, pipeline) -> None:
    """Добавление файла к токену (только для администраторов)"""
    user_data = user_tokens.get(message.from_user.id, {})
    if not user_data.get('is_admin', False):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Проверяем, есть ли документ в сообщении
    if not message.document:
        await message.answer(
            "Пожалуйста, пришлите файл с командой:\n"
            "`/add_file токен`\n\n"
            "И прикрепите файл к сообщению",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Получаем токен из caption или текста сообщения
    token = None
    if message.caption:  # Если файл отправлен с подписью
        parts = message.caption.split(maxsplit=1)
        if len(parts) > 1 and parts[0] == '/add_file':
            token = parts[1].strip()
    elif message.text:  # Если это обычное сообщение с текстом
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1 and parts[0] == '/add_file':
            token = parts[1].strip()

    if not token:
        await message.answer(
            "Пожалуйста, укажите токен для добавления файла:\n"
            "`/add_file токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if token not in pipeline.document_store.list_user_tokens():
        await message.answer(f"❌ Токен `{token}` не существует", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        filename = message.document.file_name
        file_path = f"./infrastructure/files/{token}/{filename}"

        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            await message.answer(
                f"❌ Файл `{filename}` уже существует для токена `{token}`\n\n"
                "Используйте другое имя файла или удалите существующий файл.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # Скачиваем файл
        file = await message.bot.get_file(message.document.file_id)

        # Создаем директорию, если ее нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Сохраняем файл
        await message.bot.download_file(file.file_path, file_path)

        # Добавляем документ в хранилище
        text = TextProcessor.extract_text(file_path)
        if not text:
            raise ValueError("Не удалось извлечь текст из файла")

        pipeline.document_store.add_document(token, filename, text)

        await message.answer(
            f"✅ Файл `{filename}` успешно добавлен к токену `{token}`",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении файла: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
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
async def start_handler(message: Message, user_states, pipeline):
    await message.answer(
        "👋 Добрый день! Я ваш персональный ассистент Эмили!\n\n"
        "Я помогу вам быстро находить информацию в ваших документах.\n\n"
        "Для начала работы необходимо установить ваш токен с помощью команды:\n"
        "`/token [ваш_токен]`\n\n"
        "Примеры вопросов после установки токена:\n"
        "   • Какой график работы в компании?\n"
        "   • Основные правила безопасности?",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['help']))
async def help_handler(message: Message):
    """Обработчик команды /help. Предоставляет полную справку по функционалу бота."""
    await message.answer(
        "📚 *Полное руководство по функциям*\n\n"
        "🔹 *Основные команды:*\n"
        "`/start` - Начало работы с ботом\n"
        "`/help` - Это руководство\n"
        "`/token [ваш_токен]` - Установить ваш персональный токен доступа\n"
        "`/documents` - Показать список ваших документов\n\n"
        "🔹 *Как работать с ботом:*\n"
        "1. Сначала установите ваш токен:\n"
        "`/token 12345abcde`\n\n"
        "2. Затем можете задавать вопросы по вашим документам:\n"
        "   • Какой график работы в компании?\n"
        "   • Основные правила противопожарной безопасности?\n"
        "   • Положение о коммерческой тайне?\n\n"
        "🔹 *Особенности работы:*\n"
        "   • Бот анализирует только ваши документы\n"
        "   • Ответы формируются на основе загруженных файлов",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['token']))
async def token_handler(message: Message, user_states, pipeline) -> None:
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
        user_states.pop(message.from_user.id, None)
        return

    # Сохраняем токен с учетом возможных админских прав
    if isinstance(user_states.get(message.from_user.id), dict):
        user_states[message.from_user.id]['token'] = token
    else:
        user_states[message.from_user.id] = {
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
async def documents_handler(message: Message, user_states, pipeline) -> None:
    """Показывает список документов пользователя."""
    if message.from_user.id not in user_states:
        await message.answer(
            "⚠️ Пожалуйста, сначала установите токен с помощью команды `/token`\n\n"
            "Пример: `/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    token = user_states[message.from_user.id]['token']
    documents = pipeline.list_documents(token)

    if not documents:
        await message.answer("Для вашего токена документы не найдены")
        return

    await message.answer(
        f"📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents),
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['admin']))
async def admin_handler(message: Message, user_states, pipeline) -> None:
    """Обработчик команды /admin для получения прав администратора."""
    if message.from_user.id in user_states and user_states[message.from_user.id]['is_admin']:
        await message.answer("🔓 Вы уже администратор")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Для получения прав администратора введите:\n"
            "`/admin [ваш пароль]`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    password = args[1].strip()
    if password != ADMIN_PASSWORD:
        await message.answer("❌ Неверный пароль администратора")
        return

    # Помечаем пользователя как администратора
    if message.from_user.id in user_states:
        user_states[message.from_user.id]['is_admin'] = True
    else:
        user_states[message.from_user.id] = {
            'token': 'example',
            'is_admin': True
        }

    await message.answer(
        "🔓 Вы получили права администратора!\n\n"
        "Доступные команды:\n"
        "   • /create\_token - создать новый токен\n"
        "   • /add\_file [токен]- добавить файл к токену\n"
        "   • /revoke\_admin - снять с себя права администратора\n"
        "   • Все обычные команды",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['revoke_admin']))
async def revoke_admin_handler(message: Message, user_states) -> None:
    """Обработчик команды для снятия прав администратора с текущего пользователя"""
    # Проверяем, является ли пользователь администратором
    if message.from_user.id not in user_states or not user_states[message.from_user.id].get('is_admin', False):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Снимаем права администратора
    user_states[message.from_user.id]['is_admin'] = False

    await message.answer(
        "🔒 Вы успешно сняли с себя права администратора.\n\n"
        "Теперь вам доступны только обычные команды.\n"
        "Для повторного получения прав администратора используйте команду:\n"
        "`/admin ваш_пароль`",
        parse_mode=ParseMode.MARKDOWN
    )


@router.message(Command(commands=['info']))
async def info_handler(message: Message, user_states, pipeline) -> None:
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
    if user_id in user_states:
        user_data = user_states[user_id]

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
                    f"👤 <b>Username:</b> @{user_info['username'] or user_info['full_name']}\n" + \
                    f"🆔 <b>User ID:</b> <code>{user_info['user_id']}</code>\n" + \
                    f"🔑 <b>Токен:</b> <code>{user_info['token'] or 'не установлен'}</code>\n" + \
                    f"🛡 <b>Админ:</b> {'✅ да' if user_info['is_admin'] else '❌ нет'}\n\n"

    # Добавляем информацию о документах
    if user_info['token']:
        token = user_states[message.from_user.id]['token']
        documents = pipeline.list_documents(token)

        response_text += f"\n📂 Ваши документы:\n\n" + "\n".join(f"•  {doc}" for doc in documents)

    else:
        response_text += "\n⚠️ Для просмотра документов необходимо установить токен:\n<code>/token ваш_токен</code>"

    await message.answer(
        response_text,
        parse_mode=ParseMode.HTML
    )


@router.message(Command(commands=['create_token']))
async def create_token_handler(message: Message, user_states, pipeline) -> None:
    """Создание нового токена (только для администраторов)"""
    user_data = user_states.get(message.from_user.id, {})
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
    if token in pipeline.document_store.list_user_states():
        await message.answer(f"❌ Токен `{token}` уже существует", parse_mode=ParseMode.MARKDOWN)
        return

    # Создаем пустые директории для токена
    pipeline.document_store.file_store.add_document(token, "__init__.txt", "Initial file")
    pipeline.document_store.vector_store.load_for_user(token)

    await message.answer(f"✅ Токен `{token}` успешно создан", parse_mode=ParseMode.MARKDOWN)


@router.message(Command(commands=['add_file']))
async def add_file_handler(message: Message, user_states, pipeline) -> None:
    """Добавление файла к токену (только для администраторов)"""
    user_data = user_states.get(message.from_user.id, {})
    if not user_data.get('is_admin', False):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Проверяем, есть ли документы в сообщении
    if not message.document:
        await message.answer(
            "Пожалуйста, пришлите файл с командой:\n"
            "`/add_file [токен]`\n\n"
            "И прикрепите файл к сообщению\n"
            "Поддерживаемые форматы: .docx, .pdf, .txt",
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
            "Пожалуйста, укажите токен для добавления файлов:\n"
            "`/add_file токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if token not in pipeline.document_store.list_user_tokens():
        await message.answer(f"❌ Токен `{token}` не существует", parse_mode=ParseMode.MARKDOWN)
        return

    # Обрабатываем прикрепленный документ
    if message.media_group_id:
        await message.answer("❌ Пожалуйста, присылайте файлы по одному.", parse_mode=ParseMode.MARKDOWN)
        return
    elif message.document:
        doc = message.document
    else:
        await message.answer("ℹ️ Нет файлов для обработки", parse_mode=ParseMode.MARKDOWN)
        return

    allowed_extensions = {'.docx', '.pdf', '.txt'}

    file_name = doc.file_name
    file_ext = os.path.splitext(file_name)[1].lower()

    if file_ext not in allowed_extensions:
        await message.answer(f"❌ Не удалось добавить файл `{file_name}`: недопустимый формат", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        file_path = f"./infrastructure/files/{token}/{file_name}"

        # Проверяем, существует ли файл
        if os.path.exists(file_path):
            await message.answer(f"❌ Файл `{file_name}` уже существует для токена `{token}`", parse_mode=ParseMode.MARKDOWN)
            return

        # Скачиваем файл
        file = await message.bot.get_file(doc.file_id)

        # Создаем директорию, если ее нет
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Сохраняем файл
        await message.bot.download_file(file.file_path, file_path)

        # Добавляем документ в хранилище
        text = TextProcessor.extract_text(file_path)
        if not text:
            raise ValueError("Не удалось извлечь текст из файла")

        pipeline.document_store.add_document(token, file_name, text)
        await message.answer(f"✅ Файл `{file_name}` успешно добавлен для токена `{token}`", parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)


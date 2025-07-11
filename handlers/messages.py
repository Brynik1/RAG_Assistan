from aiogram import Router
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import Message

router = Router()


@router.message(F.text)
async def message_handler(message: Message, user_states, pipeline) -> None:
    """Основной обработчик сообщений."""
    user_id = message.from_user.id

    if user_id not in user_states:
        await message.answer(
            "⚠️ Пожалуйста, сначала установите токен с помощью команды `/token`\n\n"
            "`/token ваш_уникальный_токен`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    user_data = user_states[user_id]
    user_token = user_data.get('token', 'example') if isinstance(user_data, dict) else user_data
    user_text = message.text.strip()

    try:
        documents = pipeline.list_documents(user_token)

        if not documents:
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
            top_k = 7
        )

        print(f"\nПользователь: {message.from_user.username}")
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

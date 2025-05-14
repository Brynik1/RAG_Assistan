from dotenv import load_dotenv

from app.RAGOpenAiPipeline import RAGOpenAiPipeline

load_dotenv()



if __name__ == "__main__":
    pipeline = RAGOpenAiPipeline(
        vector_storage_kwargs={'chunk_size': 800, 'chunk_overlap': 200},
    )

    # Выбор токена для пользователя
    user_token = "example"

    # Добавление документов из файлового хранилища в векторное
    pipeline.load_token(user_token)


    # Пример работы ассистента
    print("\n\033[35mРобот Алёша:\033[0m")
    print("Добро пожаловать! Я ваш личный консультант, задавайте любые вопросы!")

    while True:
        print("\n\033[35mВы:\033[0m")
        user_input = input()

        if user_input.lower() in ['выход', 'exit']:
            print("\n\033[35mРобот Алёша:\033[0m")
            print("Всего хорошего! Возвращайтесь снова!")
            break

        if not user_input.strip():
            print("\n\033[35mРобот Алёша:\033[0m")
            print("Пожалуйста, введите ваш вопрос.")
            continue

        try:
            answer = pipeline.query(user_token, user_input, top_k=7)
            print("\n\033[35mРобот Алёша:\033[0m")
            print(answer)

        except Exception as e:
            print(f"Ошибка: {str(e)}")

from dotenv import load_dotenv

import os

from app.RAGOpenAiPipeline import RAGOpenAiPipeline

load_dotenv()



if __name__ == "__main__":
    pipeline = RAGOpenAiPipeline(
        vector_storage_kwargs={'chunk_size': 800, 'chunk_overlap': 200},
    )

    input_directory = "../infrastructure/input_files"  # Буферная директория с файлами для добавления
    files = ['Глоссарий корпоративных терминов.txt',
             'Политика конфиденциальности.txt',
             'Положение о коммерческой тайне.txt',
             'Положение об оплате труда и премировании.txt',
             'Правила внутреннего трудового распорядка.txt',
             'Правила противопожарной безопасности.txt',
             'Программа адаптации новых сотрудников.txt',
             'Часто задаваемые вопросы.txt']  # Список файлов для добавления

    user_token = "many_files"

    print(pipeline.document_store.file_store.list_documents(user_token))

    # Проверка наличия буферной директории
    if not os.path.exists(input_directory):
        os.makedirs(input_directory)
        print(f"Создана директория: {input_directory}")
        print("Пожалуйста, положите свои файлы в директорию")
        exit()

    # Процесс добавления файлов
    for file in files:
        pipeline.ingest(user_token, file)

    # pipeline.document_store.vector_store.delete_document("user123",file_id="file_xyz")
    # print(pipeline.document_store.vector_store.get_document("user123", "file_xyz"))
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

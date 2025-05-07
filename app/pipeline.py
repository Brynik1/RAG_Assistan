from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import os

from storage.document_storage import DocumentStorage
from storage.components import FileStorage, VectorStorage
from app.text_utils import TextProcessor

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI

load_dotenv()


class RAGOpenAiPipeline:
    """
    Базовый пайплайн реализующий логику:
    запрос -> релевантные чанки + ллм -> ответ
    """

    def __init__(self,
                 files_path: str = "../infrastructure/files",
                 vectors_path: str = "../infrastructure/faiss",
                 openai_model: str = "gpt-4o-mini",
                 openai_model_temperature: float = 0.1,
                 openai_proxy_url: str = "https://api.proxyapi.ru/openai/v1",
                 openai_model_system_prompt: str = "Default",
                 vector_storage_kwargs: Optional[Dict[str, int]] = None):
        """
        Инициализирует хранилище текстов и векторное хранилище с заданными параметрами.

        Args:
            persist_path (str): Путь для сохранения/загрузки векторного хранилища.
            По умолчанию "../infrastructure/faiss".
            openai_model (str): Название модели OpenAI. По умолчанию "gpt-4o-mini".
            openai_model_temperature (float): Температура для модели OpenAI.
            По умолчанию 0.5.
            openai_proxy_url (str): URL прокси для API OpenAI.
            По умолчанию "https://api.proxyapi.ru/openai/v1".
            openai_model_system_prompt (str): Системный промт для модели OpenAI.
            По умолчанию "Default".
            vector_storage_kwargs (Optional[Dict[str, Any]]): Дополнительные параметры
            для векторного хранилища. такие как:
                embedding_model_name: str = "cointegrated/LaBSE-en-ru",
                splitter_chunk_size: int = 400,
                splitter_chunk_overlap: int = 150
        """
        self.files_path = files_path
        self.vectors_path = vectors_path
        files_store = FileStorage(base_path=files_path)
        vectors_store = VectorStorage(base_path=vectors_path,
                                      **(vector_storage_kwargs if vector_storage_kwargs else {}))

        self.document_store = DocumentStorage(vectors_store, files_store)

        self.llm = ChatOpenAI(model=openai_model,
                              temperature=openai_model_temperature,
                              api_key=os.environ.get("OPENAI_API_KEY"),
                              base_url=openai_proxy_url)

        if openai_model_system_prompt == "Default":
            self.GPT_TEMPLATE: str = """
Ты — AI-юрист, предоставляющий юридические консультации на основе предоставленного контекста (нормативных документов, законов и прецедентов). Твоя задача — давать точные ответы, строго соответствующие полученным юридическим материалам. Ни при каких обстоятельствах не выдумывай информацию, не интерпретируй законы вольно и не давай субъективных оценок.

**Твои обязанности:**

1. Юридическая точность:
- Все ответы должны содержать прямые ссылки на статьи/пункты из предоставленного контекста
- Цитируй нормативные формулировки дословно в кавычках "..." с указанием источника
- Различай обязательные нормы ("должен", "обязан") и рекомендательные ("может", "вправе")

2. Структура ответов:
- Для сложных вопросов используй нумерованные списки
- Четко разделяй разные правовые нормы
- Указывай противоречия в законодательстве, если они есть в контексте

3. Работа с контекстом:
- Если вопрос выходит за рамки предоставленных документов: "На основании имеющихся материалов не могу дать однозначный ответ"
- При отсутствии информации: "В предоставленных документах не найден ответ на ваш вопрос"
- Для уточняющих вопросов: "Согласно п.X документа Y, требуется уточнение по..."

**Запрещено:**
- Давать оценки типа "это справедливо" или "это хороший закон"
- Предлагать не предусмотренные контекстом способы обхода законов
- Интерпретировать нормы без прямой опоры на текст
- Смешивать разные правовые акты без указания их иерархии

**Важно:** Все выводы должны однозначно следовать из предоставленных материалов без домыслов.
"""
        else:
            self.GPT_TEMPLATE = openai_model_system_prompt

    def ingest(self,
               token: str,
               filename: str,
               input_dir: str = "../infrastructure/input_files"):
        """
            Добавляет текстовый документ в хранилище документов после обработки.

            Args:
                token (str): Уникальный идентификатор пользователя/сессии для привязки документа
                filename (str): Имя файла для добавления (без пути)
                input_dir (str, optional): Директория, в которой находится файл.
                                         По умолчанию "../infrastructure/input_files".
        """

        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            text = TextProcessor.extract_text(filepath)
            if text:
                print(f"\nДобавление '{filename}' пользователю {token}:")
                pipeline.document_store.add_document(token, filename, text)
            else:
                print(f"\nФайл {filename} не содержит текст")
        else:
            print(f"\nФайл {filename} не найден")

    def query(self,
              token: str,
              user_query: str,
              filenames: list[str],
              top_k: int = 3) -> str:
        """
        Отправление запроса к ретриверу и реализация логики самого пайплайна
        :param filename:
        :param token: Уникальный идентификатор пользователя
        :param user_query: Текстовый запрос от пользователя
        :param top_k: Количество возвращённых ретривером чанков
        :return: content - результат генерации LLM по промпту и контексту из ретривера
        """
        retriever = self.document_store.get_retriever(token=token,
                                                      filenames=filenames,
                                                      top_k=top_k)
        retrieved_docs = retriever.invoke(user_query)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.GPT_TEMPLATE + f"\n\nКонтекст:{context}"),
            ("human", "Вопрос:\n{question}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": user_query})

        return response.content


if __name__ == "__main__":
    pipeline = RAGOpenAiPipeline(vector_storage_kwargs={'chunk_size': 800, 'chunk_overlap': 200})

    input_dir = "../infrastructure/input_files"  # Буферная директория с файлами для добавления
    filenames = ["Правила компании.txt", "Частые вопросы.txt", "Онбординг.txt"]  # Список файлов для добавления
    # filenames = ["Уголовный Кодекс.docx"]

    user_token = "test_many_files"

    # Проверка наличия буферной директории
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Создана директория: {input_dir}")
        print("Пожалуйста, положите свои файлы в директорию")
        exit()

    # Процесс добавления файлов
    for filename in filenames:
        pipeline.ingest(user_token, filename)

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
            answer = pipeline.query(user_token, user_input, filenames=filenames)
            print("\n\033[35mРобот Алёша:\033[0m")
            print(answer)

        except Exception as e:
            print(f"Произошла ошибка: {str(e)}")

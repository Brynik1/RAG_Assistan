from dotenv import load_dotenv
from typing import Optional, Dict
from pathlib import Path
import time
import os

from storage.document_storage import DocumentStorage
from storage.components import FileStorage, VectorStorage
from app.text_utils import TextProcessor

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI



class RAGOpenAiPipeline:
    BASE_DIR = Path(__file__).parent.parent

    """RAG пайплайн для обработки запросов с предобработкой и поиском по документам """

    # Константы для промптов
    DEFAULT_SYSTEM_PROMPT = """
    Ты — AI-ментор в чат-боте для ответов на вопросы сотрудников. Твоя единственная задача — помогать пользователям, отвечая на их вопросы строго на основе предоставленного тебе контекста. Ни при каких обстоятельствах ты не должен выдумывать информацию, домысливать детали, интерпретировать контекст вольно или исправлять его. Ты обязан использовать исключительно те данные, которые даны в твоей базе знаний или предоставленных материалах.

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
    Ты — профессиональный AI-ментор для ответов на вопросы сотрудников. Твоя работа — четко, корректно и без искажений помогать новым сотрудникам быстрее понимать правила, процессы и задачи компании на основе данного тебе контекста.
    """

    QUERY_PREPROCESS_PROMPT = """
    Твоя задача - преобразовать пользовательский запрос в набор ключевых тегов/фраз, 
    которые будут полезны для поиска релевантной информации в документах.

    Удали все лишние фразы, не несущие смысловой нагрузки:
    - Приветствия ("Здравствуйте", "Привет" и т.д.)
    - Вежливые формы ("Пожалуйста", "Спасибо", "Будьте добры" и т.д.)
    - Избыточные формулировки

    Оставь только суть запроса в виде ключевых слов и фраз, разделенных запятыми.

    Примеры:
    1. Вход: "Здравствуйте, не могли бы вы подсказать, какие документы нужны для оформления отпуска?"
       Выход: "документы для отпуска, оформление отпуска"

    2. Вход: "Спасибо! А сколько дней отпуска положено за первый год работы?"
       Выход: "дни отпуска, первый год работы"

    3. Вход: "Пожалуйста, расскажите о процедуре увольнения по собственному желанию"
       Выход: "процедура увольнения, увольнение по собственному желанию"

    Запрос для обработки: {query}
    """

    def __init__(self,
                 files_path=str(BASE_DIR / "infrastructure/files"),
                 vectors_path=str(BASE_DIR / "infrastructure/faiss"),
                 openai_model: str = "gpt-4o-mini",
                 openai_model_temperature: float = 0.1,
                 openai_proxy_url: str = "https://api.proxyapi.ru/openai/v1",
                 openai_system_prompt: str = None,
                 vector_storage_kwargs: Optional[Dict[str, int]] = None):

        """Инициализирует пайплайн с хранилищами и моделями."""
        self.files_path = files_path
        self.vectors_path = vectors_path

        files_store = FileStorage(base_path=files_path)
        vectors_store = VectorStorage(
            base_path=vectors_path,
            **(vector_storage_kwargs or {})
        )

        self.document_store = DocumentStorage(vectors_store, files_store)

        self.llm = ChatOpenAI(
            model=openai_model,
            temperature=openai_model_temperature,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=openai_proxy_url
        )

        self.system_prompt = openai_system_prompt or self.DEFAULT_SYSTEM_PROMPT

    def ingest(self,
               token: str,
               filename: str,
               input_dir: str = "../infrastructure/files"):
        """
        Добавляет текстовый документ в хранилище документов после обработки.

        Args:
            token (str): Уникальный идентификатор пользователя/сессии для привязки документа
            filename (str): Имя файла для добавления (без пути)
            input_dir (str, optional): Директория, в которой находится файл.
                                     По умолчанию "../infrastructure/files".
        """

        filepath = os.path.join(input_dir, token, filename)
        if os.path.exists(filepath):
            text = TextProcessor.extract_text(filepath)
            if text:
                print(f"\nДобавление '{filename}' пользователю {token}:")
                self.document_store.add_document(token, filename, text)
            else:
                print(f"\nФайл {filename} не содержит текст")
        else:
            print(f"\nФайл {filename} не найден")

    def _preprocess_query(self, user_query: str):
        """
        Предварительно обрабатывает пользовательский запрос, удаляет все лишнее
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.QUERY_PREPROCESS_PROMPT),
            ("human", "{query}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"query": user_query})

        return response.content

    def query(self,
              token: str,
              user_query: str,
              top_k: int = 5):
        """
        Отправление запроса к ретриверу и реализация логики самого пайплайна
        :param token: Уникальный идентификатор пользователя
        :param user_query: Текстовый запрос от пользователя
        :param top_k: Количество возвращённых ретривером чанков
        :return: content - результат генерации LLM по промпту и контексту из ретривера
        """
        start_time = time.time()
        processed_query = self._preprocess_query(user_query)

        start_time = time.time()
        retriever = self.document_store.get_retriever(
            token=token,
            top_k=top_k
        )

        retrieved_docs = retriever.invoke(processed_query)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt + f"\nКонтекст:{context}"),
            ("human", "Вопрос:\n{question}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"question": user_query})

        return response.content

    def load_token(self,
                   token: str,
                   path_to_files: str = "../infrastructure/files"):
        token_path = path_to_files + f"/{token}"
        for file in os.listdir(token_path):
            self.ingest(token=token, filename=file, input_dir=path_to_files)

    def list_documents(self,
                       token: str):
        return self.document_store.list_documents(token)
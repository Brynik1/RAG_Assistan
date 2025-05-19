from storage.components import FileStorage, VectorStorage
from typing import List


class DocumentStorage:
    """Класс для работы с документами. Является посредником между хранилищами и остальной логикой.
    Собирает вместе файловое и векторное хранилище."""

    def __init__(self,
                 vector_store: VectorStorage,
                 file_store: FileStorage):
        """Инициализирует хранилища документов."""
        self.vector_store = vector_store
        self.file_store = file_store

    def add_document(self, token: str, filename: str, text: str):
        """Добавляет документ в оба хранилища."""
        self.file_store.add_document(token, filename, text)
        self.vector_store.add_document(token, filename, text)

    def get_retriever(self, token: str, top_k: int = 5):
        """Возвращает retriever для поиска документов."""
        return self.vector_store.get_retriever(token, top_k)

    def list_documents(self, token: str) -> List[str]:
        """Возвращает список документов пользователя."""
        file_documents = set(self.file_store.list_documents(token))
        vector_documents = set(self.vector_store.list_documents(token))
        return list(file_documents & vector_documents)

    def list_user_tokens(self) -> List[str]:
        """Возвращает список токенов пользователей."""
        file_tokens = set(self.file_store.list_user_tokens())
        vector_tokens = set(self.vector_store.list_user_tokens())
        return list(file_tokens & vector_tokens)
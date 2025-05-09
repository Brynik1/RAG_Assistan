from typing import Optional, List
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pathlib import Path


class VectorStorage:
    """Векторное хранилище документов (FAISS)."""

    def __init__(self,
                 base_path: str,
                 embedding_model: str = "cointegrated/LaBSE-en-ru",
                 chunk_size: int = 600,
                 chunk_overlap: int = 200):
        self.base_path = Path(base_path)
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=embedding_model,
            cache_folder=str(Path(__file__).parents[2] / "infrastructure" / "embeddings")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.vectordb: Optional[FAISS] = None
        print(f"Векторное хранилище инициализировано в: {self.base_path}")

    def load_for_user(self, token: str) -> None:
        """Загружает или создает хранилище для пользователя."""
        user_path = self.base_path / token

        if user_path.exists():
            self.vectordb = FAISS.load_local(
                folder_path=str(user_path),
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True
            )
        else:
            doc = self.text_splitter.create_documents(["init"])[0]
            doc.metadata = {"token": token, "filename": "__init__"}
            self.vectordb = FAISS.from_documents([doc], self.embedding_model)
            self.vectordb.save_local(str(user_path))

    def add_document(self, token: str, filename: str, text: str) -> None:
        """Добавляет документ в хранилище."""
        self.load_for_user(token)
        if self._document_exists(token, filename):
            print("✅ файл уже есть в векторном хранилище")
            return

        docs = self.text_splitter.create_documents([text])
        for doc in docs:
            doc.metadata.update({"token": token, "filename": filename})

        self.vectordb.add_documents(documents=docs)
        self.vectordb.save_local(str(self.base_path / token))
        print("✅ файл добавлен в векторное хранилище")

    def _document_exists(self, token: str, filename: str) -> bool:
        if not self.vectordb:
            return False
        return any(
            doc.metadata.get("filename") == filename
            for doc in self.vectordb.docstore._dict.values()
        )

    def delete_document(self, token: str, filename: str) -> None:
        """Удаляет документ из хранилища."""
        self.load_for_user(token)
        if not self.vectordb:
            return

        ids = [
            doc_id for doc_id, doc in self.vectordb.docstore._dict.items()
            if doc.metadata.get("filename") == filename
        ]
        if ids:
            self.vectordb.delete(ids)
            self.vectordb.save_local(str(self.base_path / token))

    def list_documents(self, token: str) -> List[str]:
        """Возвращает список документов пользователя."""
        self.load_for_user(token)
        if not self.vectordb:
            return []
        return list({
            doc.metadata["filename"]
            for doc in self.vectordb.docstore._dict.values()
        })

    def get_retriever(self, token: str, filenames: List[str], top_k: int = 5):
        """Возвращает retriever для указанных документов."""
        self.load_for_user(token)
        docs = [
            doc for doc in self.vectordb.docstore._dict.values()
            if doc.metadata.get("filename") in filenames
        ]
        temp_db = FAISS.from_documents(docs, self.embedding_model)
        return temp_db.as_retriever(search_kwargs={"k": top_k})

    def list_user_tokens(self) -> List[str]:
        """Возвращает список токенов пользователей, которые есть в хранилище."""
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]
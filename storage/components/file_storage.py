import os
from typing import List
from pathlib import Path

class FileStorage:
    """Файловое хранилище документов."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else (
            Path(__file__).parents[3] / "infrastructure" / "files"
        )
        self.base_path.mkdir(parents=True, exist_ok=True)
        print(f"Файловое хранилище инициализировано в: {self.base_path}")

    def add_document(self, token: str, filename: str, text: str) -> None:
        """Сохраняет документ в файловое хранилище."""
        user_path = self.base_path / token
        user_path.mkdir(exist_ok=True)
        file_path = user_path / filename

        if not file_path.exists():
            file_path.write_text(text, encoding='utf-8')
            print("✅ файл добавлен в файловое хранилище")
        else:
            print("✅ файл уже есть в файловом хранилище")

    def get_document_path(self, token: str, filename: str) -> str:
        """Возвращает путь к документу."""
        path = self.base_path / token / filename
        if not path.exists():
            raise FileNotFoundError(f"Document {filename} not found")
        return str(path)

    def list_documents(self, token: str) -> List[str]:
        """Возвращает список документов пользователя."""
        user_path = self.base_path / token
        return [f.name for f in user_path.iterdir()] if user_path.exists() else []
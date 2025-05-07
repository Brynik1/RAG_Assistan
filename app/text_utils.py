from pathlib import Path
import PyPDF2
from docx import Document

class TextProcessor:
    """
    Класс для извлечения текста из файлов PDF, DOCX и TXT.
    """

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                return text.strip()
        except Exception as e:
            print(f"Ошибка чтения PDF {file_path}: {e}")
            return ""

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        try:
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Ошибка чтения DOCX {file_path}: {e}")
            return ""

    @staticmethod
    def extract_text_from_txt(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Ошибка чтения TXT {file_path}: {e}")
            return ""

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        Универсальный метод для извлечения текста из файла по его расширению.
        """
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            return cls.extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return cls.extract_text_from_docx(file_path)
        elif ext == ".txt":
            return cls.extract_text_from_txt(file_path)
        else:
            print(f"Неподдерживаемый тип файла: {ext}")
            return ""
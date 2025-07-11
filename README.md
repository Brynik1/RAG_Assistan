# RAG Onboarding Assistant 🤖📚

Проект представляет собой интеллектуального ассистента на основе RAG-архитектуры (Retrieval-Augmented Generation), который расчитан на помощь компаниям в процессе адаптации новых сотрудников. Сервис позволяет администраторам из команий загружать необходимые для ознакомления файлы в токен, после чего передавать данный токен сотрудникам. Сотрудники через токен получают доступ к ознакомлению с документами и отправке вопросов по их содержанию.

## 📌 Основные возможности

- **Хранение документов**: Поддержка форматов PDF, DOCX, TXT
- **Векторный поиск**: Поиск релевантных фрагментов в документах
- **Мультипользовательский режим**: Изоляция документов по токенам пользователей

## 📚 Использование

**Для администраторов**:  
После получения прав администратора вы получаете возможность создавать токены (группы) и добавлять в них необходимые файлы из базы знаний компании.

**Для сотрудников**:  
После применения токена, полученного от администратора, вам открывается доступ ко всем необходимым файлам + вы получаете возможность задавать вопросы по содержимому файлов.

🔹 Основные команды:  
- /start - начать работу с ботом  
- /help - показать это сообщение  
- /token [ваш_токен] - установить токен для доступа к документам  
- /documents - показать список ваших документов  
- /info - информация о текущем пользователе  
  
🔹 Команды администратора:  
- /admin [пароль] - получить права администратора  
- /revoke_admin - снять права администратора  
- /create_token [токен] - создать новый токен  
- /add_file [токен] - добавить файл к токену (прикрепить файл к сообщению)  


## 🛠 Технологический стек

- **Язык**: Python
- **Хранилища**:
  - Файловое (FileStorage)
  - Векторное (FAISS + HuggingFace Embeddings)
- **LLM**: OpenAI (через прокси)
- **Обработка текста**: LangChain, PyPDF2, python-docx
- **Telegram bot**: Aiogram

## ⚙️ Хранилища документов

1. **FileStorage** - файловое хранилище:
   - Сохранение документов по пользователям
   - Получение списка документов
   - Управление путями к файлам

2. **VectorStorage** - векторное хранилище на FAISS:
   - Индексация документов с помощью HuggingFace эмбеддингов
   - Поиск по векторному пространству
   - Управление чанками документов

3. **DocumentStorage** - объединяющий класс:
   - Синхронизация файлового и векторного хранилищ
   - Единый интерфейс для работы с документами
 
## 🤖 Архитектура telegram бота

### **Обработчики**
   - commands.py - обработка команд (/start, /help и др.)
   - messages.py - обработка текстовых сообщений пользователя

### **Хранение состояниq**
   - MemoryStorage для хранения токенов пользователей
   - Изоляция данных по user_id (Telegram) и token

### **Безопасность**
   - Валидация токенов перед обработкой запросов
   - Логирование всех операций
   - Ограничение доступа к документам только по токену

## 🌟 Особенности

- Управление доступом через токены
- Загрузка и хранение корпоративных документов (PDF, DOCX, TXT)
- Интеллектуальный поиск ответов в документах (RAG pipeline)
- Генерация точных ответов с помощью LLM
- Удобный интерфейс в Telegram
- Контроль доступа для администраторов

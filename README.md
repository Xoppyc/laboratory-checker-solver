# Laboratory Checker Quiz Solver

> Автоматизований інструмент для інтелектуального проходження тестів на платформі [laboratory-checker-actions](https://laboratory-checker-actions.onrender.com/) (ЛНУ ім. Івана Франка, факультет електроніки та комп'ютерних технологій).

---

## Можливості

- **Парсинг DOM**: Безпосередній розбір HTML форми та структури питань — жодних помилок розпізнавання коду чи OCR.
- **ШІ-моделі на вибір**:
  - **Google Gemini**
  - **Groq**
  - **OpenAI**
  - **Ollama**
- **Anti-Bot / Human Simulation**: Випадкові затримки між запитаннями (1.2 – 2.8 с), щоб сервер не фіксував миттєвий автоматичний спам.
- **Пакетний режим (`--lab all`)**: Можливість пройти всі лабораторні роботи (Lab_01 – Lab_10) в один клік.
- **Звіти у JSON**: Всі питання, обрані відповіді та аргументація ШІ зберігаються у папці `results/`.
- **Інтерактивний майстер або CLI**: Запуск без аргументів вмикає зручне покрокове опитування.

---

## Як почати?

### 1. Клонувати репозиторій

```bash
git clone https://github.com/Xoppyc/laboratory-checker-solver.git
cd laboratory-checker-solver
```

### 2. Встановити залежності

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Отримати безкоштовний API-ключ

Найпростіший варіант — **Google Gemini** (безкоштовно для персонального використання + сутдентська підписка):

1. Перейдіть на [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Натисніть **"Create API key"** і скопіюйте його.
3. Створіть файл `.env`:

```bash
cp .env.example .env
```

Відкрийте `.env` та вставте ключ:

```env
GEMINI_API_KEY=AIzaSy...
```

_(Або аналогічно для Groq: [console.groq.com/keys](https://console.groq.com/keys) -> `GROQ_API_KEY=gsk_...`)\_

---

## Використання

### Інтерактивний режим (найпростіший)

Просто запустіть скрипт:

```bash
python main.py
```

Скрипт покроково запитає ваше прізвище, групу, лабораторну та посилання на ваш GitHub-репозиторій.

---

### Швидкий запуск через аргументи командного рядка

#### Проходження конкретної лабораторної:

```bash
python main.py \
  --name "Jane Doe" \
  --group "ФеП-32" \
  --lab "Lab_01" \
  --repo "JaneDoe/profesional-python" \
  --provider gemini
```

#### Проходження ВСІХ лабораторних робіт (Lab_01 .. Lab_10):

```bash
python main.py \
  --name "Jane Doe" \
  --group "ФеП-32" \
  --lab "all" \
  --repo "JaneDoe/profesional-python" \
  --provider gemini
```

#### Використання Groq (Llama-3.3-70B):

```bash
python main.py \
  --name "Jane Doe" \
  --group "ФеП-32" \
  --lab "Lab_01" \
  --repo "JaneDoe/profesional-python" \
  --provider groq
```

#### Тестовий прогін (Dry-Run без надсилання відповідей):

```bash
python main.py --dry-run
```

---

## Доступні параметри CLI

| Параметр      | Опис                                                                 | За замовчуванням      |
| :------------ | :------------------------------------------------------------------- | :-------------------- |
| `--name`      | Прізвище та ім'я студента (повинно збігатися з відомістю)            | Інтерактивно          |
| `--group`     | Академічна група (`ФеП-31`, `ФеП-32`, `ФеП-33`)                      | Інтерактивно          |
| `--course`    | Назва курсу (`professional_python` або `functional_programming`)     | `professional_python` |
| `--lab`       | Номер роботи (`Lab_01` .. `Lab_10`, або `all`)                       | Інтерактивно          |
| `--repo`      | GitHub репозиторій (`username/repo`)                                 | Інтерактивно          |
| `--provider`  | ШІ провайдер: `gemini`, `groq`, `openai`, `ollama`                   | `gemini`              |
| `--api-key`   | Передати API-ключ прямо в команді (якщо не задано в `.env`)          | `None`                |
| `--delay-min` | Мінімальна затримка між запитаннями (секунди)                        | `1.2`                 |
| `--delay-max` | Максимальна затримка між запитаннями (секунди)                       | `2.8`                 |
| `--dry-run`   | Завантажити питання та отримати відповідь ШІ без відправки на сервер | `False`               |

---

## Структура проєкту

```text
laboratory-checker-solver/
├── main.py                     # Головна точка входу
├── pyproject.toml              # Метадані пакета та конфігурація
├── requirements.txt            # Мінімальні залежності (httpx, rich, python-dotenv)
├── .env.example                # Шаблон змінних середовища
├── .gitignore                  # Ігнорування кешу та результатів
├── README.md                   # Документація користувача
├── src/
│   └── checker_solver/
│       ├── __init__.py
│       ├── models.py           # Dataclass структури даних
│       ├── parser.py           # DOM/HTML парсер форми і питань
│       ├── client.py           # HTTP сесія (cookies, start, submit)
│       ├── runner.py           # Оркестратор циклу 50 питань із затримками
│       ├── cli.py              # CLI інтерфейс та інтерактивний wizard
│       └── providers/          # Модульні ШІ-двигуни
│           ├── base.py         # Протокол та формування промптів
│           ├── factory.py      # Фабрика провайдерів
│           ├── gemini.py       # Google Gemini REST
│           ├── groq.py         # Groq REST
│           ├── openai_provider.py # OpenAI REST
│           └── ollama.py       # Локальний Ollama
└── results/                    # Папка зі збереженими логами проходжень
```

---

## Часті запитання (FAQ)

### 1. Сервер повертає помилку: `ValueError: Студента не знайдено у students.json`

Перевірте правильність написання вашого прізвища та групи. Сервер порівнює їх з офіційним списком курсу.

### 2. Сервер повертає помилку: `RuntimeError: Не вдалося завантажити GitHub repository`

Переконайтеся, що:

- Репозиторій є **публічним** (Public).
- Назва вказана у форматі `username/repository` (без `https://github.com/`).
- У вашому репозиторії є закомічений код відповідної лабораторної роботи.

---

## License

MIT License. Створено з навчальною та дослідницькою метою.​​​​​​​‌​​‌‌​‌​​​‌​‌​​‌​​​‌​‌​‌​​‌​​​‌​​​‌​​‌​​‌​​​‌​​​‌​‌​‌‌​‌​​‌​‌​​‌​‌​‌​​‌​​​‌​​‌​​‌‌​​​​‌​​​​‌​‌​​‌​​‌​​‌‌​​‌​​​​​

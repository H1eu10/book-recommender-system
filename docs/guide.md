# User and Administrator Guide / Руководство пользователя и администратора

[English](#english) · [Русский](#russian)

## English

The Book Recommendation System is a local demonstration application with a
React interface and a FastAPI backend. It supports recommendations from book
preferences and simulated reading histories. The bundled dataset contains
200 books and 1,000 synthetic reader profiles.

<a id="user-guide"></a>

### User guide

#### Open the application and choose a language

Open the address provided by the administrator. The default address for the
built application is `http://127.0.0.1:8000`.

Use **Interface language** to select English, Russian or Vietnamese. The browser
remembers this choice. Interface language and edition language are separate:
the bundled editions are in English, even when titles and descriptions are
displayed in another language.

#### Browse and search the library

Enter a title or author in **Search books**, optionally select a genre, and use
**Previous** and **Next** to browse pages of up to 15 books. Search matches the
original title, the title in the selected interface language, or the author,
without distinguishing uppercase and lowercase letters.

#### Get recommendations by preferences

1. Select **By preferences**.
2. Choose at least one genre or topic.
3. Optionally set the edition language and maximum number of pages.
4. Set **Number of results** to a value from 1 to 20.
5. Click **Get recommendations** and read the explanations on the book cards.

The match score is a content similarity value between 0 and 1, not the
probability that you will like the book. A maximum-page filter also excludes
books whose page count is unknown. If there are no results, relax the filters
or change your preferences. **Reset** clears the form and its results.

#### Read details and find similar books

Click **View details** to read the full description, genres, topics, page count
and ISBN when available. **Find similar books** displays up to five related
books, excluding the book currently being viewed. Click a suggested title to
open its details. Use **Close** or Escape to return to the main page.

Book translations are automatic and may contain errors. When a translation is
displayed, **Read original metadata** provides the source title and description.
The source link opens the original record in a new tab. Obviously broken or
repetitive translations fall back to the original text without changing the
stored dataset.

#### Get recommendations by reading history

1. Select **By reading history**.
2. Choose a **Demo reader** and review their liked books.
3. Choose an available model: Popularity, Item-CF, NCF or LightGCN.
4. Set the number of results and click **Get recommendations**.

These profiles are synthetic demonstration data, not actual readers. The
application does not require a login, collect your reading history, or save
changes to the profiles. Books already liked in the selected profile are
excluded from the recommendations.

Ranking scores can be negative or greater than 1. They order books within the
selected model; they are not probabilities and cannot be compared directly
across models. If the model has no learned history for a profile, it uses
popularity and the interface explains this fallback. Unavailable models are
disabled in the selector.

#### Common problems

| Problem | What to do |
| --- | --- |
| The library does not load | Check that the server is running and use **Try again**. |
| Reader profiles do not load | Retry the request or use **By preferences**. |
| A model is unavailable | Select another model or ask the administrator to prepare it. |
| No recommendations are returned | Relax the filters or choose another profile. There may be fewer unread candidates than requested. |

<a id="administrator-guide"></a>

### Administrator guide

#### Requirements

- Python 3.11 and the Python launcher on Windows for the commands below.
- Node.js 22.20+ within the 22.x series, or 24.12+ within the 24.x series, and npm.
- Internet access for the initial dependency installation. The prepared dataset
  and model inference run locally.
- The repository's `data/books.sample.json` and `data/user_interactions.json`.
- CPU PyTorch and saved checkpoints for NCF/LightGCN; a GPU is not required for
  the bundled demonstration.

The following commands use PowerShell and start in the repository root. The
single `backend/requirements.txt` contains application, model and test
dependencies, including the CPU wheel index for PyTorch.

#### Install and build

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ../frontend
npm ci
npm run build
```

Version pins reflect the project's existing environment. A clean installation
of every dependency from the registries has not been independently verified.

#### Run the built application

From the `frontend` directory reached above:

```powershell
cd ../backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. FastAPI serves both the built interface and the API.
`/api/health` returns `{"status":"ok"}`; `/docs` provides the OpenAPI interface.
Stop the server with Ctrl+C.

Build the frontend before starting the server. If `frontend/dist` did not exist
at startup, restart the backend after building. Rebuild after changing frontend
code. Do not open `dist/index.html` directly using `file://`.

#### Run in development mode

In one terminal, from `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository root:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Open the address printed by Vite. Its development and preview servers proxy
`/api` to `http://127.0.0.1:8000`. If the backend port changes, update the shared
proxy target in `frontend/vite.config.ts`.

#### Prepare and select checkpoints

Model training is separate from serving requests. To prepare both neural
models using the existing benchmark, run from `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --models ncf lightgcn --seeds 42
```

The application expects these default files:

```text
backend/artifacts/collaborative/seed-42/fold-0/ncf.pt
backend/artifacts/collaborative/seed-42/fold-0/lightgcn.pt
```

To use another directory, set an absolute path before starting the backend:

```powershell
$env:BOOK_MODEL_DIR = 'C:\path\to\checkpoints'
```

Use checkpoints produced by this project's training code. Missing or corrupt
checkpoints cause HTTP 503 when requested; the API never trains a replacement.
The model selector checks for PyTorch and checkpoint files, but an existing
corrupt file can still fail when loaded. Restart after changing model setup.

The current checkpoints are evaluation models trained only on training edges.
For the interactive demo, all likes in the visible profile, including held-out
likes, are excluded without updating the model. Popularity and Item-CF serving
use the full demo interaction data. These interface results therefore differ
from the separate train-only benchmark protocol.

Checkpoints and reports under `backend/artifacts/` are Git-ignored. After cloning
the repository, prepare the checkpoints or use the available content-based and
baseline models. See [the algorithm guide](collaborative_algorithms.md) for the
full evaluation protocol and [the application structure](application_structure.md)
for endpoint details. Do not regenerate the synthetic profiles unless you intend
to replace the interaction dataset and rebuild the corresponding experiments.

#### Verification and troubleshooting

```powershell
# From backend
.\.venv\Scripts\python.exe -m pytest tests -q
# From frontend
npm run build
npm run lint
```

| Symptom | Check |
| --- | --- |
| Port 8000 is already in use | Stop the conflicting local server or choose a free port; update the Vite proxy if needed. |
| UI missing while the API works | Build `frontend/dist` and restart the backend. |
| Profiles return HTTP 503 | Check that the interaction JSON is valid and its book IDs exist in the catalog. |
| NCF/LightGCN return HTTP 503 | Check the PyTorch installation, checkpoint directory, filename and format; inspect backend logs. |
| oxlint native binding is missing | Use a supported Node.js version, stop dev servers using `node_modules`, then run `npm ci` without omitting optional dependencies. |
| Windows reports EPERM during npm installation | Close processes holding esbuild/rollup files and retry. |
| Python asyncio or TestClient stalls in a restricted sandbox | Run the server/tests in a normal local terminal; this environment previously restricted loopback sockets. |

This is a local coursework demonstration. Authentication, access control,
interaction editing and public deployment configuration are outside its scope.

<a id="russian"></a>

## Русский

Система рекомендаций книг — локальное демонстрационное приложение с интерфейсом
React и сервером FastAPI. Она подбирает книги по предпочтениям и по моделируемой
истории чтения. В комплект входят 200 книг и 1 000 синтетических профилей.

<a id="ru-user-guide"></a>

### Руководство пользователя

#### Запуск и выбор языка

Откройте адрес, предоставленный администратором. По умолчанию собранное
приложение доступно по адресу `http://127.0.0.1:8000`.

В поле **Язык интерфейса** выберите английский, русский или вьетнамский язык.
Браузер запоминает выбор. Язык интерфейса не определяет язык издания: все издания
в исходном наборе англоязычные, даже если их названия и описания переведены.

#### Просмотр и поиск книг

Введите название или автора в поле **Поиск книг** и при необходимости выберите
жанр. Кнопки **Назад** и **Вперед** переключают страницы, содержащие до 15 книг.
Поиск учитывает исходное название, название на выбранном языке интерфейса и
автора, не различая регистр букв.

#### Рекомендации по предпочтениям

1. Выберите **По предпочтениям**.
2. Отметьте хотя бы один жанр или тему.
3. При необходимости задайте язык издания и максимальное число страниц.
4. Укажите **Количество результатов** от 1 до 20.
5. Нажмите **Получить рекомендации** и прочитайте пояснения на карточках.

Оценка сходства лежит в диапазоне 0–1 и не является вероятностью того, что книга
вам понравится. При ограничении числа страниц книги с неизвестным объёмом
исключаются. Если результатов нет, ослабьте фильтры или измените предпочтения.
Кнопка **Сбросить** очищает форму и результаты.

#### Подробности и похожие книги

Нажмите **Подробнее**, чтобы открыть полное описание, жанры, темы, число страниц
и ISBN, если они известны. Кнопка **Найти похожие книги** выводит до пяти других
книг. Нажатие на название результата открывает его карточку. Чтобы вернуться,
нажмите **Закрыть** или Escape.

Автоматические переводы могут содержать ошибки. Если используется перевод,
раздел **Читать исходные метаданные** показывает исходные название и описание.
Ссылка на источник открывает оригинальную запись в новой вкладке. При явных
повторах или повреждённом формате перевода показывается исходный текст;
сохранённый набор данных при этом не изменяется.

#### Рекомендации по истории чтения

1. Выберите **По истории чтения**.
2. Выберите **Демо-читателя** и просмотрите понравившиеся ему книги.
3. Выберите доступную модель: Популярность, Item-CF, NCF или LightGCN.
4. Укажите число результатов и нажмите **Получить рекомендации**.

Профили синтетические и не относятся к реальным читателям. Вход в аккаунт не
требуется; приложение не собирает вашу историю чтения и не сохраняет изменения
профилей. Уже понравившиеся выбранному читателю книги исключаются из выдачи.

Оценки ранжирования могут быть отрицательными или превышать 1. Они определяют
порядок книг внутри модели, не являются вероятностями и не сравниваются напрямую
между моделями. Если для профиля нет изученной истории, используется популярность
и выводится соответствующее сообщение. Недоступные модели нельзя выбрать.

#### Типичные затруднения

| Проблема | Действие |
| --- | --- |
| Каталог не загружается | Проверьте, что сервер запущен, и нажмите **Попробовать снова**. |
| Профили не загружаются | Повторите запрос или используйте режим **По предпочтениям**. |
| Модель недоступна | Выберите другую модель или обратитесь к администратору. |
| Рекомендаций нет | Ослабьте фильтры или выберите другой профиль. Неизвестных читателю книг может быть меньше запрошенного числа. |

<a id="ru-administrator-guide"></a>

### Руководство администратора

#### Требования

- Python 3.11 и Python Launcher в Windows для приведённых команд.
- Node.js 22.20+ в ветке 22.x либо 24.12+ в ветке 24.x и npm.
- Интернет для первоначальной установки зависимостей. Подготовленные данные
  и получение рекомендаций работают локально.
- Файлы репозитория `data/books.sample.json` и `data/user_interactions.json`.
- PyTorch для CPU и сохранённые модели для NCF/LightGCN. Для демонстрационного
  набора GPU не требуется.

Команды приведены для PowerShell и начинаются в корне репозитория. Единый файл
`backend/requirements.txt` содержит зависимости приложения, моделей и тестов,
включая адрес индекса CPU-сборок PyTorch.

#### Установка и сборка

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd ../frontend
npm ci
npm run build
```

Версии зафиксированы по существующему окружению проекта. Чистая установка всех
зависимостей из реестров отдельно не проверялась.

#### Запуск собранного приложения

Из каталога `frontend`, в котором завершились предыдущие команды:

```powershell
cd ../backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Откройте `http://127.0.0.1:8000`. FastAPI обслуживает собранный интерфейс и API.
Проверка `/api/health` возвращает `{"status":"ok"}`, а `/docs` открывает OpenAPI.
Остановка сервера — Ctrl+C.

Соберите frontend до запуска сервера. Если при запуске каталога `frontend/dist`
ещё не было, после сборки перезапустите backend. После изменений frontend
повторите сборку. Не открывайте `dist/index.html` напрямую через `file://`.

#### Режим разработки

В первом терминале из каталога `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Во втором терминале из корня репозитория:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Откройте адрес, выведенный Vite. Серверы разработки и preview перенаправляют
`/api` на `http://127.0.0.1:8000`. При смене порта backend измените общий адрес
proxy в `frontend/vite.config.ts`.

#### Подготовка и выбор сохранённых моделей

Обучение выполняется отдельно от обработки запросов. Для подготовки обеих
нейросетевых моделей запустите из `backend`:

```powershell
.\.venv\Scripts\python.exe scripts/benchmark_collaborative.py --models ncf lightgcn --seeds 42
```

По умолчанию приложение использует:

```text
backend/artifacts/collaborative/seed-42/fold-0/ncf.pt
backend/artifacts/collaborative/seed-42/fold-0/lightgcn.pt
```

Для другого каталога задайте абсолютный путь перед запуском backend:

```powershell
$env:BOOK_MODEL_DIR = 'C:\path\to\checkpoints'
```

Используйте модели, сохранённые кодом обучения этого проекта. При отсутствии
или повреждении файла запрос возвращает HTTP 503; API не запускает обучение
взамен. Список моделей проверяет наличие PyTorch и файла, но существующий
повреждённый файл может дать ошибку при загрузке. После изменения настроек
моделей перезапустите сервер.

Текущие сохранённые модели предназначены для оценки и обучены только на train.
В интерфейсе из выдачи исключаются все понравившиеся книги выбранного профиля,
включая отложенные для оценки, без обновления модели. Для выдачи Popularity и
Item-CF используются все демонстрационные взаимодействия. Поэтому результаты
интерфейса отличаются от отдельного benchmark с обучением только на train.

Каталог `backend/artifacts/` с моделями и отчётами исключён из Git. После
клонирования подготовьте модели либо используйте доступные контентные методы
и базовые модели. Полный протокол приведён в [описании алгоритмов](collaborative_algorithms.md),
маршруты API — в [описании структуры приложения](application_structure.md).
Повторная генерация синтетических профилей заменяет исходные взаимодействия
и требует заново подготовить соответствующие эксперименты.

#### Проверки и устранение неполадок

```powershell
# Из backend
.\.venv\Scripts\python.exe -m pytest tests -q
# Из frontend
npm run build
npm run lint
```

| Симптом | Что проверить |
| --- | --- |
| Порт 8000 занят | Остановите конфликтующий локальный сервер или выберите свободный порт; при необходимости обновите proxy Vite. |
| API работает, но интерфейса нет | Соберите `frontend/dist` и перезапустите backend. |
| Профили возвращают HTTP 503 | Проверьте JSON взаимодействий и наличие его ID книг в каталоге. |
| NCF/LightGCN возвращают HTTP 503 | Проверьте PyTorch, каталог, имя и формат файла модели; изучите журнал backend. |
| Для oxlint не найдена native binding | Используйте поддерживаемую версию Node.js, остановите dev-серверы и выполните `npm ci`, не исключая optional dependencies. |
| Windows выдаёт EPERM при установке npm | Закройте процессы, удерживающие файлы esbuild/rollup, и повторите установку. |
| Python asyncio или TestClient зависает в ограниченной песочнице | Запустите сервер или тесты в обычном локальном терминале; ранее в этом окружении ограничивались loopback-сокеты. |

Это локальное учебное приложение. Аутентификация, разграничение доступа,
редактирование взаимодействий и настройка публичного размещения в его состав
не входят.

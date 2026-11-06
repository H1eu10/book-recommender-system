Project: Book Recommendation System — Рекомендательная система для подбора книг.

- Frontend: React + Vite + TypeScript — builds the interface for entering preferences, viewing recommendations, exploring book details, and reading recommendation explanations.

- Backend: Python + FastAPI — provides the API, processes user preferences, and returns recommendations.

- Recommendation engine: TF-IDF and cosine similarity for preferences/similar books; Popularity, Item-CF, NCF and LightGCN for reading-history recommendations.

- Data: JSON catalog of 200 books and 1,000 synthetic reader profiles. Original metadata and automatic EN/VI/RU translations are retained.

### Workflow: 
User enters preferences → frontend sends a request to the backend → recommendation engine ranks books and generates explanations → frontend displays the results.

The initial scope excludes authentication and external AI APIs, prioritizing a complete recommendation workflow with clear explanations.

## How to run

Use Python 3.11 and Node.js 22.20+ (22.x) or 24.12+. Install dependencies and build
the UI as described in the [administrator guide](docs/guide.md#administrator-guide).

After `npm run build` in `frontend`, run the backend from `backend`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` to use the built application. For Vite development,
use the two processes below. The API proxy targets backend port 8000.

### Frontend
    cd frontend
    npm run dev

### Backend
    cd backend
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

## Application features

- Search the existing paginated library by title/author and filter by genre.
- Choose preferences, optional page/language filters and inspect explanations.
- Read full book details, source metadata and find similar books.
- Select a simulated profile and a prepared collaborative model; known likes are excluded.
- English, Vietnamese and Russian UI, including errors and explanations.
- Missing checkpoints are shown as unavailable; requests never train models.

[User guide](docs/guide.md#user-guide) · [Administrator guide](docs/guide.md#administrator-guide) ·
[Application structure and API](docs/application_structure.md)

## Collaborative recommendation experiments

Popularity, Item-CF, NCF and LightGCN share fixed train/validation/test splits,
ranking metrics and validation-based model selection. Algorithm experiments run
independently of the frontend. See [algorithm commands and evaluation protocol](docs/collaborative_algorithms.md).

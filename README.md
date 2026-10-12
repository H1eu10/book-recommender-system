Project: Book Recommendation System — Рекомендательная система для подбора книг.

- Frontend: React + Vite + TypeScript — builds the interface for entering preferences, viewing recommendations, exploring book details, and reading recommendation explanations.

- Backend: Python + FastAPI — provides the API, processes user preferences, and returns recommendations.

- Recommendation engine: Python, with scikit-learn if TF-IDF and cosine similarity are implemented to find similar books based on their descriptions. The initial approach scores books according to genres, themes, and other user-selected criteria.

- Data: A standardized book dataset. The storage format and database will be decided later.

### Workflow: 
User enters preferences → frontend sends a request to the backend → recommendation engine ranks books and generates explanations → frontend displays the results.

The initial scope excludes authentication and external AI APIs, prioritizing a complete recommendation workflow with clear explanations.
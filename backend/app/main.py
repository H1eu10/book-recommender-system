from fastapi import FastAPI

app = FastAPI(title="Book Recommendation API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
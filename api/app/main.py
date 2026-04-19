from fastapi import FastAPI

app = FastAPI(title="Revo Case API")

@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Mi Primer API REST"}

@app.get("/health")
def health():
    return {"status": "ok"}
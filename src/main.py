from fastapi import FastAPI

from src.routers.recipes import router as recipes_router

app = FastAPI()

@app.get("/")
def root():
    return {"hello": "world"}

@app.get("/health")
def check_health():
    return {"status": "ok"}

app.include_router(recipes_router)

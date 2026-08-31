from fastapi import FastAPI

from src.routers.auth import router as auth_router
from src.routers.v1.recipes import router as recipes_router
from src.routers.v1.tags import router as tags_router

app = FastAPI()


@app.get("/")
def root():
    return {"hello": "world"}


@app.get("/health")
def check_health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(recipes_router, prefix="/v1")
app.include_router(tags_router, prefix="/v1")

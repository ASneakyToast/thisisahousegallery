from fastapi import FastAPI
from sqladmin import Admin

from app.db import engine
from app.config import settings

app = FastAPI(
    title="This is a House Gallery Headless CMS",
    version="0.1.0",
    debug=settings.debug,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


admin = Admin(app, engine=engine)

from fastapi import FastAPI

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

app.include_router(auth_router)
app.include_router(organizations_router)


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} is running"}
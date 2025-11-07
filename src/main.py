from fastapi import FastAPI
from src.api.routers import system

app = FastAPI()

app.include_router(system.router)


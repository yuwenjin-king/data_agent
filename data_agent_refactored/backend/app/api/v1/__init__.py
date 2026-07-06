from fastapi import APIRouter
from app.api.v1.routers import agent, datasource, knowledge, chat

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(agent.router)
api_router.include_router(datasource.router)
api_router.include_router(knowledge.router)
api_router.include_router(chat.router)

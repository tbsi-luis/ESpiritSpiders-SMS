from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import get_settings
from routes import sms_sync_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="SMS Mobile Gateway API",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sms_sync_server.router)

# @app.get("/")
# async def root():
#     return {
#         "app": settings.app_name,
#         "version": settings.app_version,
#         "status": "running",
#         "docs": "/docs"
#     }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from jose import JWTError
import uvicorn

from app.core.config import settings
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, RateLimitMiddleware
from app.core.exceptions import (
    AuthError, NotFoundError,
    auth_error_handler, not_found_error_handler, validation_error_handler, db_error_handler, jwt_error_handler
)
from app.api.v1.router import api_router
from app.utils.logging import setup_logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Wearable-based cardiovascular disease detection API service.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure structured logging configurations
setup_logging()

# CORS middleware configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, limit=120)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up CardioGuard AI Backend server...")
    try:
        from app.database.base import Base
        from app.database.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified and updated successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down CardioGuard AI Backend server...")
    try:
        from app.core.dependencies import redis_client
        await redis_client.close()
        logger.info("Redis cache pool connection closed.")
    except Exception as e:
        logger.warning(f"Error closing Redis connection pool: {e}")

# Register custom global exception handlers
app.add_exception_handler(AuthError, auth_error_handler)
app.add_exception_handler(NotFoundError, not_found_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(SQLAlchemyError, db_error_handler)
app.add_exception_handler(JWTError, jwt_error_handler)

# Include central router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

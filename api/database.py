from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
from datetime import datetime
import logging

from config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

try:    
    # Create SQLAlchemy engine with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before using
        # echo=settings.DEBUG,  # Log SQL statements in debug mode
    )
    logger.info(f"Database engine created with URL: {settings.DATABASE_URL}")
except ImportError as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Automatically handles session lifecycle.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def close_db() -> None:
    """
    Close database connections on shutdown.
    """
    engine.dispose()
    logger.info("Database connections closed")


async def check_postgresql_health(database_url: str) -> dict:
    """
    Check PostgreSQL health using SQLAlchemy.

    Args:
        database_url: PostgreSQL connection URL

    Returns:
        dict with status, latency, and message
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.pool import NullPool

        start_time = datetime.utcnow()

        # Create engine with no pooling for health check
        engine = create_engine(database_url, poolclass=NullPool)

        try:
            # Test connection
            with engine.connect() as conn:
                # Execute simple query
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()

                # Get database size
                size_result = conn.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                db_size = size_result.scalar()

                # Get connection count
                conn_result = conn.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                ))
                connections = conn_result.scalar()

                latency = (datetime.utcnow() - start_time).total_seconds() * 1000

                return {
                    "status": "UP",
                    "latency_ms": round(latency, 2),
                    "message": f"PostgreSQL is healthy | Connections: {connections} | Size: {db_size}",
                    "details": {
                        "version": version,
                        "database_size": db_size,
                        "active_connections": connections
                    }
                }

        finally:
            engine.dispose()

    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return {
            "status": "DOWN",
            "latency_ms": None,
            "message": f"PostgreSQL connection failed: {str(e)}",
            "details": None
        }

if __name__ == "__main__":
    try:
        import asyncio
        db_health = asyncio.run(check_postgresql_health(settings.DATABASE_URL))
        print(db_health)
    except Exception as e:
        logger.error(f"Error during standalone execution: {e}")

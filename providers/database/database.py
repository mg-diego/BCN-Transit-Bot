from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

from providers.manager.secrets_manager import SecretsManager

secrets = SecretsManager()

DATABASE_URL = secrets.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "[Database] Error crítico: DATABASE_URL no encontrada en SecretsManager. "
        "Asegúrate de haber añadido la variable en Railway."
    )

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Por si acaso Railway usa el formato antiguo "postgres://"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL,
    echo=False, # Pon True si quieres ver las queries SQL en la consola (útil para debug)
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        import models

        # print("[Database] Borrando tablas existentes...")
        # await conn.run_sync(Base.metadata.drop_all)
        
        await conn.run_sync(Base.metadata.create_all)
        print("[Database] Tablas inicializadas correctamente.")
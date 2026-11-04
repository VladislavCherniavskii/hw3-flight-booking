import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@flight-db:5432/flightdb")
JWT_SECRET = os.getenv("JWT_SECRET", "shared-secret")
JWT_ALGORITHM = "HS256"
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))
REDIS_SENTINELS = [
    ("redis-sentinel-1", 26379),
    ("redis-sentinel-2", 26379),
    ("redis-sentinel-3", 26379),
]
REDIS_MASTER_NAME = "mymaster"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

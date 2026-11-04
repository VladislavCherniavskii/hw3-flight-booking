import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@booking-db:5432/bookingdb")
FLIGHT_GRPC_TARGET = os.getenv("FLIGHT_GRPC_TARGET", "flight-service:50051")
JWT_SECRET = os.getenv("JWT_SECRET", "shared-secret")
JWT_ALGORITHM = "HS256"
GRPC_TIMEOUT = float(os.getenv("GRPC_TIMEOUT", "5.0"))
CB_FAILURE_THRESHOLD = int(os.getenv("CB_FAILURE_THRESHOLD", "5"))
CB_RECOVERY_TIMEOUT = int(os.getenv("CB_RECOVERY_TIMEOUT", "15"))
RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY = float(os.getenv("RETRY_BASE_DELAY", "0.1"))

# Flight Booking System (gRPC + Redis)

## Архитектура
- **Booking Service (REST)**: Управление бронированиями, PostgreSQL, отказоустойчивость (Retry, Circuit Breaker).
- **Flight Service (gRPC)**: Управление рейсами, PostgreSQL, Redis (Cache-Aside + Sentinel HA).
- **Базы данных**: Отдельная PostgreSQL для каждого сервиса (миграции через Flyway).
- **Кеширование**: Redis Master + 2 Replica + 3 Sentinel.

## Запуск
    docker compose up --build -d

API доступно на http://localhost:8002.

## Тестовые сценарии
### 1. Поиск рейсов (кэширование)
    curl -s "http://localhost:8002/flights?origin=SVO&destination=LED"
Повторный запрос вернет данные из кэша (CACHE HIT).

### 2. Создание бронирования
    curl -s -X POST http://localhost:8002/bookings -H "Content-Type: application/json" -d '{"user_id": 1, "flight_id": 1, "passenger_name": "Ivan", "passenger_email": "ivan@test.com", "seat_count": 2}'

### 3. Отмена бронирования
    curl -s -X POST http://localhost:8002/bookings/\<UUID\>/cancel

## Отказоустойчивость
- **Retry**: 3 попытки с экспоненциальным backoff (100ms, 200ms) для UNAVAILABLE/DEADLINE_EXCEEDED.
- **Circuit Breaker**: Переходы CLOSED -> OPEN -> HALF_OPEN -> CLOSED логируются в booking-service.
- **Redis Sentinel**: Автоматическое переключение при падении мастера.

## Проверка логов
    docker compose logs flight-service | grep CACHE
    docker compose logs booking-service | grep CircuitBreaker

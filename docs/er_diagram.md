# ER-диаграмма (3NF)

```mermaid
erDiagram
    FLIGHTS ||--o{ SEAT_RESERVATIONS : "has"
    FLIGHTS {
        bigint id PK
        varchar flight_number
        varchar airline
        char origin
        char destination
        timestamptz departure_time
        timestamptz arrival_time
        int total_seats
        int available_seats
        numeric price
        varchar status
    }
    SEAT_RESERVATIONS {
        bigint id PK
        bigint flight_id FK
        uuid booking_id UK
        int seat_count
        varchar status
    }
    BOOKINGS {
        uuid id PK
        bigint user_id
        bigint flight_id
        varchar passenger_name
        varchar passenger_email
        int seat_count
        numeric total_price
        varchar status
    }
```

**Ограничения целостности:**
- `flights.total_seats > 0`
- `flights.price > 0`
- `0 <= flights.available_seats <= flights.total_seats`
- `UNIQUE(flight_number, departure_time)`
- `seat_reservations.seat_count > 0`
- `seat_reservations.booking_id UNIQUE`
- `bookings.seat_count > 0`
- `bookings.total_price > 0`

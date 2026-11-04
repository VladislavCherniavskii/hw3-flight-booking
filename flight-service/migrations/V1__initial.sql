CREATE TABLE flights (
    id BIGSERIAL PRIMARY KEY,
    flight_number VARCHAR(20) NOT NULL,
    airline VARCHAR(100) NOT NULL,
    origin CHAR(3) NOT NULL,
    destination CHAR(3) NOT NULL,
    departure_time TIMESTAMPTZ NOT NULL,
    arrival_time TIMESTAMPTZ NOT NULL,
    total_seats INTEGER NOT NULL CHECK (total_seats > 0),
    available_seats INTEGER NOT NULL CHECK (available_seats >= 0),
    price NUMERIC(12,2) NOT NULL CHECK (price > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT flights_seats_positive CHECK (available_seats <= total_seats),
    CONSTRAINT flights_unique_schedule UNIQUE (flight_number, departure_time)
);

CREATE INDEX ix_flights_route ON flights(origin, destination, departure_time);

CREATE TABLE seat_reservations (
    id BIGSERIAL PRIMARY KEY,
    flight_id BIGINT NOT NULL REFERENCES flights(id),
    booking_id UUID NOT NULL UNIQUE,
    seat_count INTEGER NOT NULL CHECK (seat_count > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_seat_reservations_flight ON seat_reservations(flight_id, status);

INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, total_seats, available_seats, price, status) VALUES
('SU1234', 'Aeroflot', 'SVO', 'LED', '2026-04-01 08:00:00+03', '2026-04-01 09:30:00+03', 180, 180, 8500.00, 'SCHEDULED'),
('SU1234', 'Aeroflot', 'SVO', 'LED', '2026-04-02 08:00:00+03', '2026-04-02 09:30:00+03', 180, 180, 8500.00, 'SCHEDULED'),
('S7123',  'S7',       'SVO', 'LED', '2026-04-01 14:00:00+03', '2026-04-01 15:30:00+03', 160, 160, 7200.00, 'SCHEDULED'),
('U6456',  'Ural',     'LED', 'SVO', '2026-04-01 18:00:00+03', '2026-04-01 19:30:00+03', 140, 140, 6800.00, 'SCHEDULED');

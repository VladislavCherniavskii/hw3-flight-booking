from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Flight(Base):
    __tablename__ = "flights"
    id = Column(BigInteger, primary_key=True)
    flight_number = Column(String(20), nullable=False)
    airline = Column(String(100), nullable=False)
    origin = Column(String(3), nullable=False)
    destination = Column(String(3), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)


class SeatReservation(Base):
    __tablename__ = "seat_reservations"
    id = Column(BigInteger, primary_key=True)
    flight_id = Column(BigInteger, nullable=False)
    booking_id = Column(UUID(as_uuid=True), nullable=False)
    seat_count = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)

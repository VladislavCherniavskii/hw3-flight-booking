from sqlalchemy import BigInteger, Column, DateTime, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    user_id = Column(BigInteger, nullable=False)
    flight_id = Column(BigInteger, nullable=False)
    passenger_name = Column(String(255), nullable=False)
    passenger_email = Column(String(255), nullable=False)
    seat_count = Column(Integer, nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="CONFIRMED")
    created_at = Column(DateTime(timezone=True), server_default=text("NOW()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("NOW()"))

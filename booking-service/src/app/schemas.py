from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class BookingCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    flight_id: int = Field(..., gt=0)
    passenger_name: str = Field(..., min_length=1, max_length=255)
    passenger_email: EmailStr
    seat_count: int = Field(..., gt=0, le=999)


class BookingResponse(BaseModel):
    id: UUID
    user_id: int
    flight_id: int
    passenger_name: str
    passenger_email: EmailStr
    seat_count: int
    total_price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class FlightInfo(BaseModel):
    id: int
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    total_seats: int
    available_seats: int
    price: Decimal
    status: str


class FlightSearchResult(BaseModel):
    flights: list[FlightInfo]

import logging
import uuid

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.circuit_breaker import CircuitOpenError
from src.app.db import get_db
from src.app.grpc_client import FlightClient
from src.app.models import Booking
from src.app.schemas import BookingCreate, BookingResponse, FlightInfo, FlightSearchResult

logger = logging.getLogger("routes")
router = APIRouter()

_flight_client: FlightClient | None = None


def set_client(client: FlightClient) -> None:
    global _flight_client
    _flight_client = client


def get_client() -> FlightClient:
    return _flight_client


@router.get("/flights", response_model=FlightSearchResult)
async def search_flights(
    origin: str = Query(..., min_length=3, max_length=3),
    destination: str = Query(..., min_length=3, max_length=3),
    date: str | None = Query(None),
):
    client = get_client()
    try:
        flights = await client.search_flights(origin, destination, date)
    except CircuitOpenError:
        raise HTTPException(503, "Flight service unavailable (circuit open)")
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise HTTPException(502, "Flight service auth failed")
        raise HTTPException(502, f"Flight service error: {e.code().name}")
    return FlightSearchResult(flights=[FlightInfo(**f) for f in flights])


@router.get("/flights/{flight_id}", response_model=FlightInfo)
async def get_flight(flight_id: int):
    client = get_client()
    try:
        flight = await client.get_flight(flight_id)
    except CircuitOpenError:
        raise HTTPException(503, "Flight service unavailable (circuit open)")
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(404, "Flight not found")
        raise HTTPException(502, f"Flight service error: {e.code().name}")
    return FlightInfo(**flight)


@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(data: BookingCreate, db: AsyncSession = Depends(get_db)):
    client = get_client()
    booking_id = uuid.uuid4()
    try:
        flight = await client.get_flight(data.flight_id)
    except CircuitOpenError:
        raise HTTPException(503, "Flight service unavailable (circuit open)")
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(404, "Flight not found")
        raise HTTPException(502, f"Flight service error: {e.code().name}")
    if flight["status"] != "SCHEDULED":
        raise HTTPException(409, "Flight is not available for booking")
    try:
        await client.reserve_seats(data.flight_id, data.seat_count, str(booking_id))
    except CircuitOpenError:
        raise HTTPException(503, "Flight service unavailable (circuit open)")
    except grpc.aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
            raise HTTPException(409, f"Not enough seats: {e.details()}")
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(404, "Flight not found")
        raise HTTPException(502, f"Flight service error: {e.code().name}")
    total_price = flight["price"] * data.seat_count
    booking = Booking(
        id=booking_id, user_id=data.user_id, flight_id=data.flight_id,
        passenger_name=data.passenger_name, passenger_email=data.passenger_email,
        seat_count=data.seat_count, total_price=total_price, status="CONFIRMED",
    )
    db.add(booking)
    try:
        await db.commit()
        await db.refresh(booking)
    except Exception:
        await db.rollback()
        try:
            await client.release_reservation(str(booking_id))
        except Exception as rel_err:
            logger.error(f"Failed to release reservation {booking_id}: {rel_err}")
        raise HTTPException(500, "Booking creation failed")
    return BookingResponse.model_validate(booking)


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    return BookingResponse.model_validate(b)


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    if b.status != "CONFIRMED":
        raise HTTPException(409, f"Cannot cancel booking in status {b.status}")
    client = get_client()
    try:
        await client.release_reservation(str(booking_id))
    except CircuitOpenError:
        raise HTTPException(503, "Flight service unavailable (circuit open)")
    except grpc.aio.AioRpcError as e:
        raise HTTPException(502, f"Flight service error: {e.code().name}")
    b.status = "CANCELLED"
    await db.commit()
    await db.refresh(b)
    return BookingResponse.model_validate(b)


@router.get("/bookings", response_model=list[BookingResponse])
async def list_bookings(user_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Booking).where(Booking.user_id == user_id))).scalars().all()
    return [BookingResponse.model_validate(b) for b in rows]

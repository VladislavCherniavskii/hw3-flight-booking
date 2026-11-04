import logging
import uuid

import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from sqlalchemy import func, select

from src.generated import flight_pb2, flight_pb2_grpc
from src.app import cache
from src.app.config import CACHE_TTL
from src.app.db import SessionLocal
from src.app.models import Flight, SeatReservation

logger = logging.getLogger("flight")

STATUS_MAP = {
    "SCHEDULED": flight_pb2.SCHEDULED,
    "DEPARTED": flight_pb2.DEPARTED,
    "CANCELLED": flight_pb2.CANCELLED,
    "COMPLETED": flight_pb2.COMPLETED,
}

def _to_proto(f: Flight) -> flight_pb2.Flight:
    dep = Timestamp()
    dep.FromDatetime(f.departure_time)
    arr = Timestamp()
    arr.FromDatetime(f.arrival_time)
    return flight_pb2.Flight(
        id=f.id, flight_number=f.flight_number, airline=f.airline,
        origin=f.origin, destination=f.destination,
        departure_time=dep, arrival_time=arr,
        total_seats=f.total_seats, available_seats=f.available_seats,
        price=str(f.price),
        status=STATUS_MAP.get(f.status, flight_pb2.FLIGHT_STATUS_UNSPECIFIED),
    )

def _to_dict(f: Flight) -> dict:
    return {
        "id": f.id, "flight_number": f.flight_number, "airline": f.airline,
        "origin": f.origin, "destination": f.destination,
        "departure_time": f.departure_time.isoformat(),
        "arrival_time": f.arrival_time.isoformat(),
        "total_seats": f.total_seats, "available_seats": f.available_seats,
        "price": str(f.price), "status": f.status,
    }

def _from_dict(d: dict) -> flight_pb2.Flight:
    dep = Timestamp(); dep.FromJsonString(d["departure_time"])
    arr = Timestamp(); arr.FromJsonString(d["arrival_time"])
    return flight_pb2.Flight(
        id=d["id"], flight_number=d["flight_number"], airline=d["airline"],
        origin=d["origin"], destination=d["destination"],
        departure_time=dep, arrival_time=arr,
        total_seats=d["total_seats"], available_seats=d["available_seats"],
        price=d["price"],
        status=STATUS_MAP.get(d["status"], flight_pb2.FLIGHT_STATUS_UNSPECIFIED),
    )

class FlightServiceServicer(flight_pb2_grpc.FlightServiceServicer):

    async def SearchFlights(self, request, context):
        key = f"search:{request.origin}:{request.destination}:{request.date or '_'}"
        cached = await cache.get(key)
        if cached:
            return flight_pb2.SearchFlightsResponse(flights=[_from_dict(x) for x in cached["items"]])
        async with SessionLocal() as db:
            q = select(Flight).where(
                Flight.origin == request.origin,
                Flight.destination == request.destination,
                Flight.status == "SCHEDULED",
            )
            if request.date:
                q = q.where(func.date(Flight.departure_time) == request.date)
            q = q.order_by(Flight.departure_time)
            rows = (await db.execute(q)).scalars().all()
        await cache.set(key, {"items": [_to_dict(f) for f in rows]}, CACHE_TTL)
        return flight_pb2.SearchFlightsResponse(flights=[_to_proto(f) for f in rows])

    async def GetFlight(self, request, context):
        key = f"flight:{request.id}"
        cached = await cache.get(key)
        if cached:
            return flight_pb2.FlightResponse(flight=_from_dict(cached))
        async with SessionLocal() as db:
            f = await db.get(Flight, request.id)
            if not f:
                await context.abort(grpc.StatusCode.NOT_FOUND, "Flight not found")
        await cache.set(key, _to_dict(f), CACHE_TTL)
        return flight_pb2.FlightResponse(flight=_to_proto(f))

    async def ReserveSeats(self, request, context):
        if request.seat_count <= 0:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "seat_count must be positive")
        
        booking_uuid = uuid.UUID(request.booking_id)
        origin = dest = None
        
        async with SessionLocal() as db:
            async with db.begin():
                existing = (await db.execute(
                    select(SeatReservation).where(SeatReservation.booking_id == booking_uuid)
                )).scalar_one_or_none()
                if existing:
                    if existing.status == "ACTIVE":
                        return flight_pb2.ReserveSeatsResponse(
                            reservation_id=existing.id,
                            booking_id=request.booking_id,
                            status=existing.status,
                        )
                    await context.abort(grpc.StatusCode.ABORTED, "Reservation already released")
                
                flight = (await db.execute(
                    select(Flight).where(Flight.id == request.flight_id).with_for_update()
                )).scalar_one_or_none()
                
                if not flight:
                    await context.abort(grpc.StatusCode.NOT_FOUND, "Flight not found")
                if flight.status != "SCHEDULED":
                    await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Flight is not scheduled")
                if flight.available_seats < request.seat_count:
                    await context.abort(
                        grpc.StatusCode.RESOURCE_EXHAUSTED,
                        f"Not enough seats: requested={request.seat_count}, available={flight.available_seats}",
                    )
                
                flight.available_seats -= request.seat_count
                reservation = SeatReservation(
                    flight_id=flight.id, booking_id=booking_uuid,
                    seat_count=request.seat_count, status="ACTIVE",
                )
                db.add(reservation)
                await db.flush()
                reservation_id = reservation.id
                origin = flight.origin
                dest = flight.destination
                
        await cache.delete(f"flight:{request.flight_id}")
        if origin and dest:
            await cache.delete_pattern(f"search:{origin}:{dest}:*")
            
        return flight_pb2.ReserveSeatsResponse(
            reservation_id=reservation_id, booking_id=request.booking_id, status="ACTIVE",
        )

    async def ReleaseReservation(self, request, context):
        booking_uuid = uuid.UUID(request.booking_id)
        flight_id = None
        async with SessionLocal() as db:
            async with db.begin():
                reservation = (await db.execute(
                    select(SeatReservation).where(SeatReservation.booking_id == booking_uuid).with_for_update()
                )).scalar_one_or_none()
                if not reservation or reservation.status != "ACTIVE":
                    return flight_pb2.ReleaseReservationResponse(released=False)
                
                flight = (await db.execute(
                    select(Flight).where(Flight.id == reservation.flight_id).with_for_update()
                )).scalar_one()
                
                flight.available_seats += reservation.seat_count
                reservation.status = "RELEASED"
                flight_id = flight.id
                
        await cache.delete(f"flight:{flight_id}")
        return flight_pb2.ReleaseReservationResponse(released=True)

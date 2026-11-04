import logging
import time
from decimal import Decimal

import grpc
from grpc import aio
from jose import jwt

from src.app import config
from src.app.circuit_breaker import CircuitBreaker, CircuitOpenError
from src.app.retry import RetryPolicy
from src.generated import flight_pb2, flight_pb2_grpc

logger = logging.getLogger("grpc_client")

STATUS_NAMES = {
    flight_pb2.SCHEDULED: "SCHEDULED",
    flight_pb2.DEPARTED: "DEPARTED",
    flight_pb2.CANCELLED: "CANCELLED",
    flight_pb2.COMPLETED: "COMPLETED",
}


def _flight_to_dict(f) -> dict:
    return {
        "id": f.id, "flight_number": f.flight_number, "airline": f.airline,
        "origin": f.origin, "destination": f.destination,
        "departure_time": f.departure_time.ToDatetime(),
        "arrival_time": f.arrival_time.ToDatetime(),
        "total_seats": f.total_seats, "available_seats": f.available_seats,
        "price": Decimal(f.price),
        "status": STATUS_NAMES.get(f.status, "UNKNOWN"),
    }


class FlightClient:
    def __init__(self, target: str):
        self.channel = aio.insecure_channel(target)
        self.stub = flight_pb2_grpc.FlightServiceStub(self.channel)
        payload = {"sub": "booking-service", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
        self.metadata = [("authorization", f"Bearer {token}")]
        self.retry = RetryPolicy(config.RETRY_MAX_ATTEMPTS, config.RETRY_BASE_DELAY)
        self.cb = CircuitBreaker(config.CB_FAILURE_THRESHOLD, config.CB_RECOVERY_TIMEOUT)

    async def _call(self, method, request):
        if not self.cb.can_proceed():
            raise CircuitOpenError("Circuit is OPEN")
        try:
            result = await self.retry.execute(
                lambda: method(request, metadata=self.metadata, timeout=config.GRPC_TIMEOUT)
            )
            self.cb.on_success()
            return result
        except grpc.aio.AioRpcError as e:
            if e.code() in (grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED):
                self.cb.on_failure()
            raise

    async def search_flights(self, origin, destination, date=None):
        resp = await self._call(
            self.stub.SearchFlights,
            flight_pb2.SearchFlightsRequest(origin=origin, destination=destination, date=date or ""),
        )
        return [_flight_to_dict(f) for f in resp.flights]

    async def get_flight(self, flight_id: int):
        resp = await self._call(self.stub.GetFlight, flight_pb2.GetFlightRequest(id=flight_id))
        return _flight_to_dict(resp.flight)

    async def reserve_seats(self, flight_id: int, seat_count: int, booking_id: str):
        resp = await self._call(
            self.stub.ReserveSeats,
            flight_pb2.ReserveSeatsRequest(flight_id=flight_id, seat_count=seat_count, booking_id=booking_id),
        )
        return {"reservation_id": resp.reservation_id, "status": resp.status}

    async def release_reservation(self, booking_id: str):
        resp = await self._call(
            self.stub.ReleaseReservation,
            flight_pb2.ReleaseReservationRequest(booking_id=booking_id),
        )
        return resp.released

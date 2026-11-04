import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app import config
from src.app.grpc_client import FlightClient
from src.app.routes import router, set_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = FlightClient(config.FLIGHT_GRPC_TARGET)
    set_client(client)
    yield
    await client.channel.close()


app = FastAPI(title="Booking Service", lifespan=lifespan)
app.include_router(router)

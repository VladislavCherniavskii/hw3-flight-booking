import asyncio
import logging
from grpc import aio

from src.app.config import GRPC_PORT
from src.app.auth import AuthInterceptor
from src.app.servicer import FlightServiceServicer
from src.generated import flight_pb2_grpc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("main")


async def serve():
    server = aio.server(interceptors=[AuthInterceptor()])
    flight_pb2_grpc.add_FlightServiceServicer_to_server(FlightServiceServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    await server.start()
    logger.info(f"Flight service listening on :{GRPC_PORT}")
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())

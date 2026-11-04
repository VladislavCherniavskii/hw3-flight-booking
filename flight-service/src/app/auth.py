import grpc
from grpc import aio
from jose import JWTError, jwt
from src.app.config import JWT_SECRET, JWT_ALGORITHM


class AuthInterceptor(aio.ServerInterceptor):
    def __init__(self):
        async def _deny(request, context):
            await context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid token")
        self._deny_handler = grpc.unary_unary_rpc_method_handler(_deny)

    async def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata or [])
        auth = metadata.get("authorization", "")
        if not auth.startswith("Bearer "):
            return self._deny_handler
        try:
            jwt.decode(auth[7:], JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except JWTError:
            return self._deny_handler
        return await continuation(handler_call_details)

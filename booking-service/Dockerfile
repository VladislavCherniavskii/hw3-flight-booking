FROM python:3.12-slim
WORKDIR /app
COPY booking-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proto ./proto
RUN mkdir -p src/generated && touch src/generated/__init__.py && \
    python -m grpc_tools.protoc -I./proto \
        --python_out=./src/generated \
        --grpc_python_out=./src/generated \
        ./proto/flight.proto && \
    sed -i 's/^import flight_pb2 as flight__pb2$/from . import flight_pb2 as flight__pb2/' src/generated/flight_pb2_grpc.py
COPY booking-service/src ./src
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

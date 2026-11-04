import logging
import time
from enum import Enum

logger = logging.getLogger("circuit_breaker")


class State(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 15):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failure_count = 0
        self.opened_at = None

    def can_proceed(self) -> bool:
        if self.state == State.CLOSED:
            return True
        if self.state == State.OPEN:
            if time.time() - self.opened_at >= self.recovery_timeout:
                self.state = State.HALF_OPEN
                logger.info("CircuitBreaker: OPEN -> HALF_OPEN")
                return True
            return False
        return True

    def on_success(self) -> None:
        if self.state != State.CLOSED:
            logger.info(f"CircuitBreaker: {self.state.value} -> CLOSED")
        self.state = State.CLOSED
        self.failure_count = 0
        self.opened_at = None

    def on_failure(self) -> None:
        self.failure_count += 1
        if self.state == State.HALF_OPEN:
            self.state = State.OPEN
            self.opened_at = time.time()
            logger.info("CircuitBreaker: HALF_OPEN -> OPEN")
        elif self.state == State.CLOSED and self.failure_count >= self.failure_threshold:
            self.state = State.OPEN
            self.opened_at = time.time()
            logger.info(f"CircuitBreaker: CLOSED -> OPEN (failures={self.failure_count})")

    def is_open(self) -> bool:
        return self.state == State.OPEN

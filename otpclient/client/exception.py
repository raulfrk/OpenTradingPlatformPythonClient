from functools import wraps
from typing import Callable, Any

from otpclient.client.response.response import Response, OPStatusEnum


class NATSException(Exception):
    """Exceptions related to NATS connection."""
    pass


class ServerError(Exception):
    """Exceptions related to OTP server errors."""
    pass


class CancelledError(ServerError):
    """Exceptions related to cancelled operations."""
    pass


def parse_error(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Response:
        response: Response = await func(self, *args, **kwargs)
        if response.Status == OPStatusEnum.FAILURE and kwargs.get("fail_on_error", True):
            raise ServerError(response.Err)
        return response

    return wrapper

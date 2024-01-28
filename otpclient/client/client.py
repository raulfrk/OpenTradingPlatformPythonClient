import nats
from nats.aio.client import Client
from abc import ABC
from otpclient.client.response import Response, ResponseSchema, StatusEnum, JSONCommand, JSONCommandSchema, add_json_preamble
from typing import Callable, Any
from functools import wraps

class NATSException(Exception):
    pass

class ServerError(Exception):
    pass

def parse_error(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Response:
        response: Response = await func(self, *args, **kwargs)
        if response.Status == StatusEnum.FAILURE and kwargs.get("fail_on_error", True):
            raise ServerError(response.Err)
        return response
    return wrapper

class OtpClient(ABC):
    def __init__(self, nats_client: Client):
        self.nc = nats_client

class SystemClient(OtpClient):
    def __init__(self, nats_client: Client):
        super().__init__(nats_client)
    
    @parse_error
    async def quit(self, component: str, fail_on_error: bool = True) -> Response:
        request = JSONCommandSchema().dumps(JSONCommand("quit", "", ""))
        request = add_json_preamble(request).encode()
        try:
            response = await self.nc.request(f"{component}.command", request)
        except Exception as e:
            raise NATSException(e)
        cast_response = ResponseSchema()
        response_instance: Response = cast_response.loads(response.data.decode())
        return response_instance
        
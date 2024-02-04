from nats.aio.client import Client

from otpclient.client.client import OtpClient
from otpclient.client.enums import JSONOperationEnum, ComponentEnum, FunctionalityEnum
from otpclient.client.exception import NATSException, parse_error
from otpclient.client.request.request import JSONCommand, JSONCommandSchema, add_json_preamble
from otpclient.client.response.response import Response, ResponseSchema


class SystemClient(OtpClient):
    def __init__(self, nats_client: Client):
        super().__init__(nats_client)

    @parse_error
    async def quit(self, component: ComponentEnum) -> Response:
        """Quit the component. This will stop the component and all of its subscriptions on the OTP backend."""
        request = JSONCommandSchema().dumps(JSONCommand(JSONOperationEnum.QUIT, "", ""))
        request = add_json_preamble(request).encode()
        try:
            response = await self.nc.request(f"{component.value}.{FunctionalityEnum.COMMAND.value}", request)
        except Exception as e:
            raise NATSException(e)
        cast_response = ResponseSchema()
        response_instance: Response = cast_response.loads(response.data.decode())
        return response_instance

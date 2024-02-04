from nats.aio.client import Client

from otpclient.client.client import OtpClient
from otpclient.client.enums import ComponentEnum, FunctionalityEnum
from otpclient.logging.logger import log


class DatastorageClient(OtpClient):
    """Client for interacting with the Datastorage component of the OTP system.
    This client is used to request data."""
    logger = log

    def __init__(self, nats_client: Client):
        super().__init__(nats_client)
        self.command_topic = (
            f"{ComponentEnum.DATASTORAGE.value}.{FunctionalityEnum.COMMAND.value}"
        )

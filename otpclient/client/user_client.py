from nats.aio.client import Client

from otpclient.client.client import OtpClient
from otpclient.client.dataprovider_client import DataproviderClient
from otpclient.client.datastorage_client import DatastorageClient
from otpclient.client.sentimentanalyzer_client import SentimentAnalyzerClient


class UserClient(OtpClient):
    """Wrapper client for all user-facing clients."""

    def __init__(self, nats_client: Client):
        super().__init__(nats_client)
        self.dataprovider = DataproviderClient(nats_client)
        self.datastorage = DatastorageClient(nats_client)
        self.sentimentanalyzer = SentimentAnalyzerClient(nats_client)

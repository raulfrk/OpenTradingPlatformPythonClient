import asyncio
import json

from nats.aio.client import Client

from otpclient.client.client import OtpClient
from otpclient.client.enums import AccountEnum, OPStatusEnum
from otpclient.client.enums import AssetClassEnum
from otpclient.client.enums import ComponentEnum
from otpclient.client.enums import DatatypeEnum
from otpclient.client.enums import FunctionalityEnum
from otpclient.client.enums import SourceEnum
from otpclient.client.enums import StreamRequestOPEnum
from otpclient.client.exception import ServerError
from otpclient.client.request.stream_request import StreamRequest
from otpclient.client.response.response import StreamResponse
from otpclient.client.stream_handler.subscription_potential import SubscriptionCollection
from otpclient.client.stream_handler.subscription_potential import SubscriptionPotential
from otpclient.client.stream_handler.subscription_potential import SubscriptionUpdate


class DataproviderClient(OtpClient):
    """Client for interacting with the Dataprovider component of the OTP system.
    This client is used to request data and subscribe to data streams."""

    def __init__(self, nats_client: Client):
        super().__init__(nats_client)
        self.command_topic = (
            f"{ComponentEnum.DATAPROVIDER.value}.{FunctionalityEnum.COMMAND.value}"
        )
        self.logger = self.logger.bind(
            command_topic=self.command_topic,
        )
        self._subscription_collection: SubscriptionCollection | None = SubscriptionCollection(nats_client)
        self._auto_sync_task: asyncio.Task | None = None
        self._auto_sync_lock = asyncio.Lock()

        self.logger.info("DataproviderClient initialized")

    def get_subscription_collection(self) -> SubscriptionCollection | None:
        """Get the subscription collection for this client. This is used to manage subscriptions."""
        return self._subscription_collection

    async def update_subscription_collections(self, updates: list[SubscriptionUpdate]) -> None:
        """Update the subscription collections associated with the client with the given updates."""
        self.logger.info("Updating subscription collections using external subscription updates",
                         len_updates=len(updates))
        if self._subscription_collection is not None:
            await self._subscription_collection.update(updates)

    async def stream_add(
            self,
            source: SourceEnum,
            asset_class: AssetClassEnum,
            symbols: list[str],
            data_types: list[DatatypeEnum],
            account: AccountEnum,
            timeout_sec: int = 60,
    ) -> tuple[StreamResponse, list[SubscriptionPotential], SubscriptionUpdate]:
        """Request OTP dataprovider to add a stream subscription for the given parameters."""
        logger = self.logger.bind(source=source, asset_class=asset_class, symbols=symbols, data_types=data_types,
                                  account=account, timeout_sec=timeout_sec)
        logger.info("Requesting stream add")

        req = (
            StreamRequest(
                source,
                asset_class,
                symbols,
                StreamRequestOPEnum.ADD,
                data_types,
                account,
            )
            .wrap()
            .dump()
        )

        response = await self.nc.request(
            self.command_topic,
            req.encode(),
            timeout=timeout_sec,
        )

        obj_response = StreamResponse.load(response.data.decode())

        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Stream add failed", response=obj_response)
            raise ServerError(obj_response.Err)
        logger.info("Stream add successful", response=obj_response.Message)
        topics_dict = json.loads(obj_response.Topics)
        # Cast the key to the enum
        topics_dict = {DatatypeEnum(key): value for key, value in topics_dict.items()}
        su = SubscriptionUpdate(topics_dict, StreamRequestOPEnum.ADD, server_bound=True)
        sp = await su.to_sub_potential(self.nc)
        await self.update_subscription_collections([su])
        return obj_response, sp, su

    async def stream_remove(
            self,
            source: SourceEnum,
            asset_class: AssetClassEnum,
            symbols: list[str],
            data_types: list[DatatypeEnum],
            account: AccountEnum,
            timeout_sec: int = 60,
    ) -> tuple[StreamResponse, SubscriptionUpdate]:
        """Request OTP dataprovider to remove a stream subscription for the given parameters."""
        logger = self.logger.bind(source=source, asset_class=asset_class, symbols=symbols, data_types=data_types,
                                  account=account, timeout_sec=timeout_sec)
        logger.info("Requesting stream remove")
        req = (
            StreamRequest(
                source,
                asset_class,
                symbols,
                StreamRequestOPEnum.REMOVE,
                data_types,
                account,
            )
            .wrap()
            .dump()
        )

        response = await self.nc.request(
            self.command_topic,
            req.encode(),
            timeout=timeout_sec,
        )

        obj_response = StreamResponse.load(response.data.decode())
        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Stream remove failed", response=obj_response.Err)
            raise ServerError(obj_response.Err)
        logger.info("Stream remove successful", response=obj_response.Message)

        topics_dict = json.loads(obj_response.Topics)
        # Cast the key to the enum
        topics_dict = {DatatypeEnum(key): value for key, value in topics_dict.items()}
        su = SubscriptionUpdate(topics_dict, StreamRequestOPEnum.REMOVE, server_bound=True)
        await self.update_subscription_collections([su])
        return StreamResponse.load(response.data.decode()), su

    async def stream_get(
            self,
            source: SourceEnum,
            asset_class: AssetClassEnum,
            account: AccountEnum,
            timeout_sec: int = 60,
    ) -> StreamResponse:
        """Request OTP dataprovider to get the current active streams for the given parameters."""
        logger = self.logger.bind(source=source, asset_class=asset_class,
                                  account=account, timeout_sec=timeout_sec)
        logger.info("Requesting stream get")
        req = (
            StreamRequest(
                source,
                asset_class,
                [],
                StreamRequestOPEnum.GET,
                [],
                account,
            )
            .wrap()
            .dump()
        )

        response = await self.nc.request(
            self.command_topic,
            req.encode(),
            timeout=timeout_sec,
        )
        obj_response = StreamResponse.load(response.data.decode())
        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Stream get failed", response=obj_response.Err)
            raise ServerError(obj_response.Err)
        logger.info("Stream get successful", response=obj_response.Message)

        return obj_response

    async def enable_topic_sync(self, interval_sec: int):
        """Enable automatic topic sync with the server at the given interval in seconds. If already enabled, update the
        interval. If disabled, enable it."""
        logger = self.logger.bind(interval_sec=interval_sec)
        async with self._auto_sync_lock:
            logger.debug("Enabling topic sync")
            if self._auto_sync_task is not None:
                logger.debug("Topic sync already enabled, updating interval")
                await self._unsafe_disable_topic_sync()

        async def topic_sync():
            while True:
                srs: list[StreamResponse] = []
                for asset_class in list(AssetClassEnum):
                    response = await self.stream_get(
                        SourceEnum.ALPACA,
                        asset_class,
                        AccountEnum.DEFAULT
                    )
                    srs.append(response)
                logger.debug("Syncing topics with server")
                await self._subscription_collection.sync(srs)
                await asyncio.sleep(interval_sec)

        async with self._auto_sync_lock:
            logger.debug("Starting topic sync task")
            self._auto_sync_task = asyncio.create_task(topic_sync())

    async def _unsafe_disable_topic_sync(self):
        """This is a non-thread safe method to disable topic sync. Only use in a thread safe context!"""
        self.logger.debug("Disabling topic sync")
        if self._auto_sync_task is not None:
            self._auto_sync_task.cancel()
            self._auto_sync_task = None
        else:
            self.logger.debug("Topic sync already disabled, no action taken")

    async def disable_topic_sync(self):
        """Disable automatic topic sync with the server."""
        async with self._auto_sync_lock:
            await self._unsafe_disable_topic_sync()

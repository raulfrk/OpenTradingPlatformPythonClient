import asyncio
from abc import ABC
from datetime import datetime, timedelta
from typing import Any, List

import nats
from nats.aio.client import Client

from otpclient.client.defaults import NATS_SERVER_URL
from otpclient.client.enums import OPStatusEnum, DatatypeEnum, SourceEnum, AssetClassEnum, AccountEnum, TimeFrameEnum, \
    DataRequestOPEnum
from otpclient.client.exception import ServerError, CancelledError
from otpclient.client.request.data_request import DataRequest
from otpclient.client.response.response import DataResponse
from otpclient.client.stream_handler.entity_mapping import loadable_map
from otpclient.logging.logger import log
from otpclient.proto.transmission_message import TransmissionMessage


def extract_queue_count(topic: str) -> int:
    """Extract the queue count from the topic."""
    return int(topic.split(".")[-1])


class OtpClient(ABC):
    """Abstract base class for OTP clients"""
    logger = log

    def __init__(self, nats_client: Client):
        self.nc = nats_client
        self.command_topic: str = ""

    async def data_get(
            self,
            source: SourceEnum,
            asset_class: AssetClassEnum,
            symbol: str,
            data_type: DatatypeEnum,
            account: AccountEnum,
            start_time: datetime,
            end_time: datetime,
            time_frame: TimeFrameEnum,
            no_confirm: bool = False,
            timeout_sec: int = 60,
    ) -> DataResponse:
        """Request OTP component to get data for the given parameters. Setting no_confirm to True will tell the OTP server to
        start streaming the data without waiting for a confirmation from the client that it is listening."""
        start_time_unix = int(start_time.timestamp())
        end_time_unix = int(end_time.timestamp())
        logger = self.logger.bind(source=source, asset_class=asset_class, symbol=symbol, data_types=data_type,
                                  account=account, start_time=start_time, end_time=end_time, time_frame=time_frame,
                                  no_confirm=no_confirm, timeout_sec=timeout_sec)
        logger.info("Requesting data get")

        req = DataRequest(
            "",
            source,
            asset_class,
            symbol,
            DataRequestOPEnum.GET,
            data_type,
            account,
            start_time_unix,
            end_time_unix,
            time_frame,
            no_confirm
        ).wrap().dump()

        response = await self.nc.request(
            self.command_topic,
            req.encode(),
            timeout=timeout_sec,
        )

        obj_response = DataResponse.load(response.data.decode())
        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Data get failed", response=obj_response.Err)
            raise ServerError(obj_response.Err)
        logger.info("Data get successful", response=obj_response.Message)

        return obj_response

    @classmethod
    async def new(cls, nats_url: str = NATS_SERVER_URL) -> "OtpClient":
        """Create a new client, connect to given URL and return the appropriate client object."""
        nc = await nats.connect(nats_url)
        return cls(nc)

    async def close(self) -> None:
        """Close the client."""
        await self.nc.close()

    async def resolve_data(self, data_response: DataResponse, timeout_sec: int = 60) -> List[Any]:
        """Resolve DataResponse to data."""
        if data_response.Status == OPStatusEnum.FAILURE:
            log.error("Attempted to resolve data from failed response", err=data_response.Err)
            raise Exception(data_response.Err)
        out_data = []

        current_time = datetime.now()

        expected_count = extract_queue_count(data_response.ResponseTopic)
        q = asyncio.Queue(expected_count)

        async def _data_response_callback(msg: nats.aio.msg.Msg) -> None:
            if msg.data == b"":
                return

            await q.put(msg)

        async def _break_on_timeout():
            while True:
                if datetime.now() > current_time + timedelta(seconds=timeout_sec):
                    break
                await asyncio.sleep(1)
            await q.put(None)

        t = asyncio.create_task(_break_on_timeout())

        subs = []
        for _ in range(5):
            subs.append(await self.nc.subscribe(data_response.ResponseTopic, queue="queue", cb=_data_response_callback,
                                                pending_msgs_limit=1_000_000))

        await self.nc.publish(data_response.ResponseTopic, b"")
        while True:
            if q.qsize() == expected_count:
                break
            await asyncio.sleep(1)
        for _ in range(expected_count):
            msg = await q.get()
            if msg is None:
                raise CancelledError("Data resolution timed out.")
            msg = TransmissionMessage.load(msg.data)
            loadable = loadable_map[DatatypeEnum(msg.data_type)]
            data = loadable.load(msg.payload)
            out_data.append(data)

        for s in subs:
            await s.unsubscribe()
        return out_data

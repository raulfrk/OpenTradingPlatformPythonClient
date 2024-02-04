import asyncio
import json
from typing import Any, TypeVar, Union
from typing import Awaitable, Callable

from nats.aio.client import Client
from nats.aio.client import Subscription
from nats.aio.msg import Msg

from otpclient.client.enums import AssetClassEnum
from otpclient.client.enums import DatatypeEnum
from otpclient.client.enums import SourceEnum
from otpclient.client.enums import StreamRequestOPEnum
from otpclient.client.response.response import StreamResponse
from otpclient.client.stream_handler.entity_mapping import loadable_map
from otpclient.logging.logger import log
from otpclient.proto.proto_loadable import ProtoLoadable
from otpclient.proto.transmission_message import TransmissionMessage


class SubscriptionUpdate:
    def __init__(
            self,
            topics: dict[DatatypeEnum, list[str]],
            operation: StreamRequestOPEnum,
            server_bound: bool = False,
    ) -> None:
        """SubscriptionUpdate used to update the potential subscription collection by either adding or removing
        topics."""
        self.topics = topics
        self.operation = operation
        self.server_bound = server_bound
        self.sub_potentials: list[SubscriptionPotential] = []
        self._sub_potential_lock = asyncio.Lock()

    async def to_sub_potential(self, nats_client: Client) -> list["SubscriptionPotential"]:
        """Converts the SubscriptionUpdate to a list of SubscriptionPotentials. Calling this method multiple times
        will return the same list of SubscriptionPotentials."""
        async with self._sub_potential_lock:
            if len(self.sub_potentials) == 0 and self.operation == StreamRequestOPEnum.ADD:
                self.sub_potentials = [
                    SubscriptionPotential(nats_client, topic, dtype.value)
                    for dtype, topics in self.topics.items()
                    for topic in topics
                ]
        return self.sub_potentials


class SubscriptionPotential:
    """SubscriptionPotential is used to represent a potential subscription to a topic. It is used to manage the
    subscription to a topic and can be used to subscribe to the topic with a callback or a queue."""
    logger = log

    def __init__(self, nats_client: Client, topic: str, data_type: str) -> None:
        self._nc = nats_client
        self.topic = topic
        self.data_type = data_type
        self._loadable: ProtoLoadable | None = loadable_map.get(
            DatatypeEnum(data_type), None
        )
        self.subscription: Subscription | None = None
        self._subscription_lock = asyncio.Lock()
        self.queue: asyncio.Queue[Any] | None = None
        self._access_queue_lock = asyncio.Lock()

        self.logger = self.logger.bind(topic=topic, data_type=data_type,
                                       loadable=self._loadable.__name__ if self._loadable is not None else None)

    async def subscribe(
            self, callback: Callable[[Any], Awaitable[None]], replace: bool = False
    ) -> SubscriptionUpdate | None:
        """Subscribe to the topic with the given callback. If replace is True, the current subscription will be
        replaced with the new callback. If replace is False and there is already a subscription, an exception will be
        raised."""
        logger = self.logger.bind(replace=replace)
        async with self._subscription_lock:
            if self.subscription is not None and not replace:
                logger.error("Already subscribed to topic")
                raise Exception(
                    f"Already subscribed to topic {self.topic}, use replace=True to replace callback/queue.")
            if self.subscription is not None:
                await self.subscription.unsubscribe()
                self.subscription = None

            if self._loadable is None:
                logger.error("Cannot load entity type")
                raise Exception(f"Cannot load {self.data_type}")

            async def _callback(msg: Msg):
                if self._loadable is None:
                    logger.error("Cannot load entity type in callback")
                    raise Exception(f"Cannot load {self.data_type}")
                entity = self._loadable.load(TransmissionMessage.load(msg.data).payload)
                await callback(entity)

            subscription = await self._nc.subscribe(self.topic, cb=_callback)
            self.subscription = subscription

            logger.info("Subscribed to topic")

            return SubscriptionUpdate(
                {DatatypeEnum(self.data_type): [self.topic]}, StreamRequestOPEnum.ADD
            )

    async def is_subscribed(self) -> bool:
        """Returns True if the SubscriptionPotential is currently subscribed to the topic."""
        async with self._subscription_lock:
            return self.subscription is not None

    async def subscribe_queue(
            self, q: asyncio.Queue, replace: bool = False
    ) -> SubscriptionUpdate | None:
        """Subscribe to the topic and send data to the given queue. If replace is True, the current subscription will be
        replaced with the new one. If replace is False and there is already a subscription, an exception will be
        raised."""
        logger = self.logger.bind(replace=replace)

        async def _callback(entity: Any):
            await q.put(entity)

        logger.info("Subscribing using queue handler")

        sub = await self.subscribe(_callback, replace)
        async with self._access_queue_lock:
            if sub is not None:
                self.queue = q
        return sub

    async def unsubscribe(
            self,
            subscription_collection: Union["SubscriptionCollection", None] = None,
            server_driven: bool = False,
    ) -> SubscriptionUpdate | None:
        """Unsubscribe from the topic. If server_driven is True, the subscription will be removed from the given
        subscription_collection."""
        async with self._subscription_lock:
            if self.subscription is not None:
                await self.subscription.unsubscribe()
                self.subscription = None
                async with self._access_queue_lock:
                    if self.queue is not None:
                        await self.queue.put(None)
                        self.queue = None

                su = SubscriptionUpdate(
                    {DatatypeEnum(self.data_type): [self.topic]},
                    StreamRequestOPEnum.REMOVE,
                    server_driven,
                )
                if subscription_collection is not None:
                    await subscription_collection.update([su])
                self.logger.info("Unsubscribed from topic")
                return su
            return None


EntityTypeVar = TypeVar("EntityTypeVar")


class SubscriptionCollection:
    """SubscriptionCollection is used to manage a collection of SubscriptionPotentials."""
    logger = log

    def __init__(
            self,
            nats_client: Client,
            sub_potentials: list[SubscriptionPotential] | None = None,
    ):
        self._sub_potentials: list[SubscriptionPotential] = []
        self._sub_potentials_lock = asyncio.Lock()
        if sub_potentials is not None:
            self._sub_potentials = sub_potentials

        self._nc = nats_client

    async def _subscribe(
            self,
            callback: Callable[[EntityTypeVar], Awaitable[None]] | None = None,
            queue: asyncio.Queue[EntityTypeVar] | None = None,
            source: list[SourceEnum] | None = None,
            asset_class: list[AssetClassEnum] | None = None,
            data_types: list[DatatypeEnum] | None = None,
            symbols: list[str] | None = None,
    ) -> list[SubscriptionPotential]:
        """Subscribe to the topics that match the given criteria. If callback is not None, the given queue will be
        used"""
        logger = self.logger.bind(
            source=source, asset_class=asset_class, data_types=data_types, symbols=symbols)
        async with self._sub_potentials_lock:
            subs = await self._unsafe_filter_subscriptions(
                source, asset_class, data_types, symbols
            )

            for sub_potential in subs:
                if callback is not None:
                    await sub_potential.subscribe(callback)
                elif queue is not None:
                    await sub_potential.subscribe_queue(queue)
                else:
                    raise Exception("Either callback or queue must be provided")

            logger.info("Subscribed to topics matching criteria")

            return subs

    async def _unsafe_filter_subscriptions(self,
                                           source: list[SourceEnum] | None = None,
                                           asset_class: list[AssetClassEnum] | None = None,
                                           data_types: list[DatatypeEnum] | None = None,
                                           symbols: list[str] | None = None,
                                           active_only: bool = False,
                                           ) -> list[SubscriptionPotential]:
        subs = self._sub_potentials
        if source is not None and len(source) != 0:
            subs = [sub for sub in subs if any(s.value in sub.topic for s in source)]

        if asset_class is not None and len(asset_class) != 0:
            subs = [sub for sub in subs if any(a.value in sub.topic for a in asset_class)]

        if data_types is not None and len(data_types) != 0:
            subs = [sub for sub in subs if any(d.value == sub.data_type for d in data_types)]

        if symbols is not None and len(symbols) != 0:
            subs = [sub for sub in subs if any(s in sub.topic for s in symbols)]

        if active_only:
            subs = [sub for sub in subs if sub.is_subscribed()]

        return subs

    async def filter_subscriptions(self,
                                   source: list[SourceEnum] | None = None,
                                   asset_class: list[AssetClassEnum] | None = None,
                                   data_types: list[DatatypeEnum] | None = None,
                                   symbols: list[str] | None = None,
                                   active_only: bool = False,
                                   ) -> list[SubscriptionPotential]:
        """Filter the subscriptions based on the given criteria. If active_only is True, only active subscriptions
        will be returned."""
        async with self._sub_potentials_lock:
            return await self._unsafe_filter_subscriptions(
                source, asset_class, data_types, symbols, active_only)

    async def subscribe_queue(self,
                              queue: asyncio.Queue[EntityTypeVar],
                              source: list[SourceEnum] | None = None,
                              asset_class: list[AssetClassEnum] | None = None,
                              data_types: list[DatatypeEnum] | None = None,
                              symbols: list[str] | None = None,
                              ) -> list[SubscriptionPotential]:
        """Subscribe to the topics that match the given criteria and send data to the given queue."""
        return await self._subscribe(
            None, queue, source, asset_class, data_types, symbols
        )

    async def subscribe_callback(self,
                                 callback: Callable[[EntityTypeVar], Awaitable[None]] | None = None,
                                 source: list[SourceEnum] | None = None,
                                 asset_class: list[AssetClassEnum] | None = None,
                                 data_types: list[DatatypeEnum] | None = None,
                                 symbols: list[str] | None = None,
                                 ) -> list[SubscriptionPotential]:
        """Subscribe to the topics that match the given criteria and use the given callback."""
        return await self._subscribe(
            callback, None, source, asset_class, data_types, symbols
        )

    async def update(self, updates: list[SubscriptionUpdate]):
        self.logger.info("Updating subscriptions")
        async with self._sub_potentials_lock:
            await self._unsafe_update(updates)

    async def _unsafe_update(self, updates: list[SubscriptionUpdate]):
        for update in updates:
            if update.operation == StreamRequestOPEnum.ADD:
                await self._unsafe_update_add(update)
            elif update.operation == StreamRequestOPEnum.REMOVE:
                await self._unsafe_update_delete(update)

    async def _unsafe_update_delete(self, update: SubscriptionUpdate) -> None:
        for _, topics in update.topics.items():
            for topic in topics:
                for sub_potential in self._sub_potentials:
                    if sub_potential.topic == topic:
                        # print("Unsubscribing from", sub_potential._topic)
                        await sub_potential.unsubscribe()
                        if update.server_bound:
                            self._sub_potentials.remove(sub_potential)
                        break

    async def _unsafe_update_add(self, update: SubscriptionUpdate) -> None:
        sps = await update.to_sub_potential(self._nc)

        existing_topics = [sp.topic for sp in self._sub_potentials]
        for sp in sps:
            if sp.topic not in existing_topics:
                self._sub_potentials.append(sp)

    async def get_all_subscriptions(self) -> list[SubscriptionPotential]:
        """Returns all the SubscriptionPotentials."""
        return await self.filter_subscriptions()

    async def sync(self, stream_responses: list[StreamResponse]):
        """Sync the SubscriptionCollection with the given StreamResponses."""
        async with self._sub_potentials_lock:
            dtype_topics: dict[DatatypeEnum, set[str]] = {}
            overall_topics: set[str] = set()
            for response in stream_responses:
                topics_dict = json.loads(response.Topics)
                for k, v in topics_dict.items():
                    k = DatatypeEnum(k)
                    if k not in dtype_topics:
                        dtype_topics[k] = set()
                    dtype_topics[k].update(v)
                    overall_topics.update(v)

            sub_topics = {sub.topic for sub in self._sub_potentials}
            updates: list[SubscriptionUpdate] = []
            topics_to_remove: list[str] = []
            # Check topics to remove
            for sub in self._sub_potentials:
                if sub.topic not in overall_topics:
                    topics_to_remove.append(sub.topic)
            if len(topics_to_remove) > 0:
                updates.append(
                    SubscriptionUpdate(
                        {DatatypeEnum(sub.data_type): topics_to_remove},
                        StreamRequestOPEnum.REMOVE,
                        server_bound=True,
                    )
                )
                self.logger.debug("Topics removed", topics=topics_to_remove)

            topics_to_add = []
            # Check topics to add
            for dtype, topics in dtype_topics.items():
                for topic in topics:
                    if topic not in sub_topics:
                        updates.append(
                            SubscriptionUpdate(
                                {dtype: [topic]}, StreamRequestOPEnum.ADD, server_bound=True
                            )
                        )
                        topics_to_add.append(topic)
            if len(topics_to_add) > 0:
                self.logger.debug("Topics added", topics=topics_to_add)

            await self._unsafe_update(updates)

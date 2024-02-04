from typing import Any

import pandas as pd

from otpclient.proto.orderbook_pb2 import Orderbook as OrderbookProto
from otpclient.proto.orderbook_pb2 import OrderbookEntry as OrderbookEntryProto


class OrderbookEntry:
    def __init__(self, orderbook_entry_proto: OrderbookEntryProto) -> None:
        self.price: float = orderbook_entry_proto.Price
        self.size: float = orderbook_entry_proto.Size
        self.source: str = orderbook_entry_proto.Source

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entry = OrderbookEntryProto()
        entry.ParseFromString(proto)
        return OrderbookEntry(entry)

    @classmethod
    def list_to_dataframe(cls, entities: list["OrderbookEntry"]):
        data = [entity.__dict__ for entity in entities]
        if len(data) == 0:
            return pd.DataFrame()
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        return df


class Orderbook:
    def __init__(self, orderbook_proto: OrderbookProto) -> None:
        self.symbol: str = orderbook_proto.Symbol
        self.exchange: str = orderbook_proto.Exchange
        self.timestamp: int = orderbook_proto.Timestamp
        self.asks: list[OrderbookEntry] = [OrderbookEntry(entry) for entry in orderbook_proto.Asks]
        self.bids: list[OrderbookEntry] = [OrderbookEntry(entry) for entry in orderbook_proto.Bids]
        self.reset: bool = orderbook_proto.Reset
        self.fingerprint: str = orderbook_proto.Fingerprint
        self.source: str = orderbook_proto.Source
        self.asset_class: str = orderbook_proto.AssetClass

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = OrderbookProto()
        entity.ParseFromString(proto)
        return Orderbook(entity)

    @classmethod
    def list_to_dataframe(cls, entities: list["Orderbook"]):
        data = [entity.__dict__ for entity in entities]

        for d in data:
            d["asks"] = OrderbookEntry.list_to_dataframe(d["asks"])
            d["bids"] = OrderbookEntry.list_to_dataframe(d["bids"])

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        # Convert timestamp to datetime and set it as the index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # Drop the original "timestamp" column
        df.drop(columns=['timestamp'], inplace=True, errors="ignore")

        return df

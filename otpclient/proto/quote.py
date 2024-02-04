from typing import Any

from otpclient.proto.Base import Base
from otpclient.proto.quote_pb2 import Quote as QuoteProto


class Quote(Base):
    def __init__(self, proto_bar: QuoteProto) -> None:
        self.symbol: str = proto_bar.Symbol
        self.bid_exchange: str = proto_bar.BidExchange
        self.exchange: str = proto_bar.Exchange
        self.bid_price: float = proto_bar.BidPrice
        self.bid_size: float = proto_bar.BidSize
        self.ask_exchange: str = proto_bar.AskExchange
        self.ask_price: float = proto_bar.AskPrice
        self.ask_size: float = proto_bar.AskSize
        self.timestamp: int = proto_bar.Timestamp
        self.conditions: list[str] = proto_bar.Conditions
        self.tape: str = proto_bar.Tape
        self.fingerprint: str = proto_bar.Fingerprint
        self.source: str = proto_bar.Source
        self.asset_class: str = proto_bar.AssetClass

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = QuoteProto()
        entity.ParseFromString(proto)
        return Quote(entity)

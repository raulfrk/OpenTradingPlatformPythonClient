from typing import Any

from otpclient.proto.Base import Base
from otpclient.proto.trade_pb2 import Trade as TradeProto


class Trade(Base):
    def __init__(self, trade_proto: TradeProto):
        self.id: int = trade_proto.ID
        self.symbol: str = trade_proto.Symbol
        self.exchange: str = trade_proto.Exchange
        self.price: float = trade_proto.Price
        self.size: float = trade_proto.Size
        self.timestamp: int = trade_proto.Timestamp
        self.taker_side: str = trade_proto.TakerSide
        self.conditions: list[str] = trade_proto.Conditions
        self.tape: str = trade_proto.Tape
        self.fingerprint: str = trade_proto.Fingerprint
        self.update: str = trade_proto.Update
        self.source: str = trade_proto.Source
        self.asset_class: str = trade_proto.AssetClass

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = TradeProto()
        entity.ParseFromString(proto)
        return Trade(entity)

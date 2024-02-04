from typing import Any

from otpclient.proto.Base import Base
from otpclient.proto.bar_pb2 import Bar as BarProto


class Bar(Base):
    def __init__(self, proto_bar: BarProto) -> None:
        self.symbol: str = proto_bar.Symbol
        self.exchange: str = proto_bar.Exchange
        self.open: float = proto_bar.Open
        self.high: float = proto_bar.High
        self.low: float = proto_bar.Low
        self.close: float = proto_bar.Close
        self.volume: float = proto_bar.Volume
        self.vwap: float = proto_bar.VWAP
        self.timestamp: int = proto_bar.Timestamp
        self.trade_count: int = proto_bar.TradeCount
        self.fingerprint: str = proto_bar.Fingerprint
        self.source: str = proto_bar.Source
        self.asset_class: str = proto_bar.AssetClass
        self.timeframe: str = proto_bar.Timeframe

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = BarProto()
        entity.ParseFromString(proto)
        return Bar(entity)


class DailyBars(Bar):

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = BarProto()
        entity.ParseFromString(proto)
        return DailyBars(entity)


class UpdatedBars(Bar):

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = BarProto()
        entity.ParseFromString(proto)
        return UpdatedBars(entity)

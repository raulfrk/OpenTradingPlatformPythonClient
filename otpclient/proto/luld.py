from typing import Any

from otpclient.proto.Base import Base
from otpclient.proto.LULD_pb2 import LULD as LULDProto


class LULD(Base):
    def __init__(self, luld_proto: LULDProto) -> None:
        self.symbol: str = luld_proto.Symbol
        self.limit_up_price: float = luld_proto.LimitUpPrice
        self.limit_down_price: float = luld_proto.LimitDownPrice
        self.indicator: str = luld_proto.Indicator
        self.timestamp: int = luld_proto.Timestamp
        self.tape: str = luld_proto.Tape
        self.fingerprint: str = luld_proto.Fingerprint
        self.source: str = luld_proto.Source
        self.asset_class: str = luld_proto.AssetClass

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = LULDProto()
        entity.ParseFromString(proto)
        return LULD(entity)

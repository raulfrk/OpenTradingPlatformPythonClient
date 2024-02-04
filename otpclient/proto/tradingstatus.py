from typing import Any

import pandas as pd

from otpclient.proto.Base import Base
from otpclient.proto.tradingstatus_pb2 import TradingStatus as TradingStatusProto


class TradingStatus(Base):
    def __init__(self, trading_status_proto: TradingStatusProto) -> None:
        self.symbol: str = trading_status_proto.Symbol
        self.status_code: str = trading_status_proto.StatusCode
        self.status_msg: str = trading_status_proto.StatusMsg
        self.reason_code: str = trading_status_proto.ReasonCode
        self.reason_msg: str = trading_status_proto.ReasonMsg
        self.timestamp: int = trading_status_proto.Timestamp
        self.tape: str = trading_status_proto.Tape
        self.fingerprint: str = trading_status_proto.Fingerprint
        self.source: str = trading_status_proto.Source
        self.asset_class: str = trading_status_proto.AssetClass

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = TradingStatusProto()
        entity.ParseFromString(proto)
        return TradingStatus(entity)

    @classmethod
    def list_to_dataframe(cls, entities: list["TradingStatus"]):
        data = [entity.__dict__ for entity in entities]

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        # Convert timestamp to datetime and set it as the index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # Drop the original "timestamp" column
        df.drop(columns=['timestamp'], inplace=True, errors="ignore")

        return df

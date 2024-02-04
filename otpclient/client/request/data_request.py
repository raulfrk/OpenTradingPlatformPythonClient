from marshmallow import fields, Schema, post_load

from otpclient.client.enums import AccountEnum
from otpclient.client.enums import AssetClassEnum
from otpclient.client.enums import DataRequestOPEnum, JSONOperationEnum, TimeFrameEnum
from otpclient.client.enums import DatatypeEnum
from otpclient.client.enums import SourceEnum
from otpclient.client.request.request import JSONCommand


class DataRequestSchema(Schema):
    fingerprint = fields.Str()
    source = fields.Enum(SourceEnum, by_value=True)
    assetClass = fields.Enum(AssetClassEnum, by_value=True)
    symbol = fields.Str()
    operation = fields.Enum(DataRequestOPEnum, by_value=True)
    dataType = fields.Enum(DatatypeEnum, by_value=True)
    account = fields.Enum(AccountEnum, by_value=True)
    startTime = fields.Int()
    endTime = fields.Int()
    timeFrame = fields.Enum(TimeFrameEnum, by_value=True)
    noConfirm = fields.Bool()

    @post_load()
    def make_object(self, data, **kwargs):
        return DataRequest(**data)


class DataRequest:
    def __init__(
            self,
            fingerprint: str,
            source: SourceEnum,
            assetClass: AssetClassEnum,
            symbol: str,
            operation: DataRequestOPEnum,
            dataType: DatatypeEnum,
            account: AccountEnum,
            startTime: int,
            endTime: int,
            timeFrame: TimeFrameEnum,
            noConfirm: bool,
    ):
        self.fingerprint = fingerprint
        self.source = source
        self.assetClass = assetClass
        self.symbol = symbol
        self.operation = operation
        self.dataType = dataType
        self.account = account
        self.startTime = startTime
        self.endTime = endTime
        self.timeFrame = timeFrame
        self.noConfirm = noConfirm

    def wrap(self) -> "JSONCommand":
        dumpedDR = DataRequestSchema().dumps(self)
        return JSONCommand(JSONOperationEnum.DATA, dumpedDR, "")

    @classmethod
    def unwrap(cls, command: "JSONCommand") -> "DataRequest":
        if command.request is None:
            raise ValueError(f"Invalid request type in command: {command.request}")
        return DataRequestSchema().loads(command.request)

    @classmethod
    def from_raw_command(cls, command: str) -> "DataRequest":
        return cls.unwrap(JSONCommand.load(command))

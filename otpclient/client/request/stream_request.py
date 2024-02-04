from marshmallow import fields, Schema, post_load

from otpclient.client.enums import AccountEnum
from otpclient.client.enums import AssetClassEnum
from otpclient.client.enums import DatatypeEnum
from otpclient.client.enums import JSONOperationEnum
from otpclient.client.enums import SourceEnum
from otpclient.client.enums import StreamRequestOPEnum
from otpclient.client.request.request import JSONCommand


class StreamRequestSchema(Schema):
    source = fields.Enum(SourceEnum, by_value=True)
    assetClass = fields.Enum(AssetClassEnum, by_value=True)
    symbols = fields.List(fields.Str())
    operation = fields.Enum(StreamRequestOPEnum, by_value=True)
    dataTypes = fields.List(fields.Enum(DatatypeEnum, by_value=True))
    account = fields.Enum(AccountEnum, by_value=True)

    @post_load()
    def make_object(self, data, **kwargs):
        return StreamRequest(**data)


class StreamRequest:
    def __init__(
            self,
            source: SourceEnum,
            assetClass: AssetClassEnum,
            symbols: list[str],
            operation: StreamRequestOPEnum,
            dataTypes: list[DatatypeEnum],
            account: AccountEnum,
    ):
        self.source = source
        self.assetClass = assetClass
        self.symbols = symbols
        self.operation = operation
        self.dataTypes = dataTypes
        self.account = account

    def wrap(self) -> "JSONCommand":
        dumpedSR = StreamRequestSchema().dumps(self)
        return JSONCommand(JSONOperationEnum.STREAM, dumpedSR, "")

    @classmethod
    def unwrap(cls, command: "JSONCommand") -> "StreamRequest":
        if command.request is None:
            raise ValueError(f"Invalid request type in command: {command.request}")
        return StreamRequestSchema().loads(command.request)

    @classmethod
    def from_raw_command(cls, command: str) -> "StreamRequest":
        return cls.unwrap(JSONCommand.load(command))

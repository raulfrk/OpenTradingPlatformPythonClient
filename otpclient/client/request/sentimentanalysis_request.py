from marshmallow import fields, Schema, post_load

from otpclient.client.enums import DataRequestOPEnum, JSONOperationEnum, LLMProviderEnum, SentimentAnalysisProcessEnum
from otpclient.client.enums import SourceEnum
from otpclient.client.request.request import JSONCommand, CancelRemote


class SentimentAnalysisRequestSchema(Schema):
    Source = fields.Enum(SourceEnum, by_value=True)
    Symbol = fields.Str()
    Operation = fields.Enum(DataRequestOPEnum, by_value=True)
    StartTime = fields.Int()
    EndTime = fields.Int()
    NoConfirm = fields.Bool()

    SentimentAnalysisProcess = fields.Enum(SentimentAnalysisProcessEnum, by_value=True)
    Model = fields.Str()
    ModelProvider = fields.Enum(LLMProviderEnum, by_value=True)
    SystemPrompt = fields.Str()
    FailFastOnBadSentiment = fields.Bool()
    RetryFailed = fields.Bool()

    @post_load()
    def make_object(self, data, **kwargs):
        return SentimentAnalysisRequest(**data)


class SentimentAnalysisRequest:
    def __init__(
            self,
            Source: SourceEnum,
            Symbol: str,
            Operation: DataRequestOPEnum,
            StartTime: int,
            EndTime: int,
            NoConfirm: bool,
            SentimentAnalysisProcess: SentimentAnalysisProcessEnum,
            Model: str,
            ModelProvider: LLMProviderEnum,
            SystemPrompt: str,
            FailFastOnBadSentiment: bool,
            RetryFailed: bool,
            CancelRemote: CancelRemote = None
    ):
        self.Source = Source
        self.Symbol = Symbol
        self.Operation = Operation
        self.StartTime = StartTime
        self.EndTime = EndTime
        self.NoConfirm = NoConfirm
        self.SentimentAnalysisProcess = SentimentAnalysisProcess
        self.Model = Model
        self.ModelProvider = ModelProvider
        self.SystemPrompt = SystemPrompt
        self.FailFastOnBadSentiment = FailFastOnBadSentiment
        self.RetryFailed = RetryFailed
        self.CancelRemote: CancelRemote = CancelRemote

    def wrap(self) -> "JSONCommand":
        dumpedSR = SentimentAnalysisRequestSchema().dumps(self)
        # Hash the request to create a unique cancel key
        return JSONCommand(JSONOperationEnum.DATA, dumpedSR, self.CancelRemote.cancel_key if self.CancelRemote else "")

    @classmethod
    def unwrap(cls, command: "JSONCommand") -> "SentimentAnalysisRequest":
        if command.request is None:
            raise ValueError(f"Invalid request type in command: {command.request}")
        return SentimentAnalysisRequestSchema().loads(command.request)

    @classmethod
    def from_raw_command(cls, command: str) -> "SentimentAnalysisRequest":
        return cls.unwrap(JSONCommand.load(command))

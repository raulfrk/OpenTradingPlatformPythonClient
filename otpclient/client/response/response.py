from marshmallow import Schema, fields, post_load

from otpclient.client.enums import OPStatusEnum


class ResponseSchema(Schema):
    Err = fields.Str()
    Message = fields.Str()
    Status = fields.Enum(OPStatusEnum, by_value=True)

    @post_load()
    def make_object(self, data, **kwargs):
        return Response(**data)


class Response():
    def __init__(self, Err, Message, Status):
        self.Err: str = Err
        self.Message: str = Message
        self.Status: OPStatusEnum = Status

    def dump(self) -> str:
        return ResponseSchema().dumps(self)

    @classmethod
    def load(cls, json: str) -> "Response":
        return ResponseSchema().loads(json)


class DataResponseSchema(ResponseSchema):
    Err = fields.Str()
    Message = fields.Str()
    Status = fields.Enum(OPStatusEnum, by_value=True)
    ResponseTopic = fields.Str()

    @post_load()
    def make_object(self, data, **kwargs):
        return DataResponse(**data)


class DataResponse(Response):
    def __init__(self, Err, Message, Status, ResponseTopic=""):
        super().__init__(Err, Message, Status)
        self.ResponseTopic: str = ResponseTopic

    def dump(self) -> str:
        return DataResponseSchema().dumps(self)

    @classmethod
    def load(cls, json: str) -> "DataResponse":
        return DataResponseSchema().loads(json)


class StreamResponseSchema(ResponseSchema):
    Err = fields.Str()
    Message = fields.Str()
    Status = fields.Enum(OPStatusEnum, by_value=True)
    Streams = fields.Str()
    Topics = fields.Str()

    @post_load()
    def make_object(self, data, **kwargs):
        return StreamResponse(**data)


class StreamResponse(Response):
    def __init__(self, Err, Message, Status, Streams="", Topics=""):
        super().__init__(Err, Message, Status)
        self.Streams: str = Streams
        self.Topics: str = Topics

    def dump(self) -> str:
        return StreamResponseSchema().dumps(self)

    @classmethod
    def load(cls, json: str) -> "StreamResponse":
        return StreamResponseSchema().loads(json)

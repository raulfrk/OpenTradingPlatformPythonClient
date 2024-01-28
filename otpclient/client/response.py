from marshmallow import Schema, fields, post_load
from enum import Enum

class StatusEnum(Enum):
    SUCCESS = "success"
    FAILURE = "failure"

class ResponseSchema(Schema):
    Err = fields.Str()
    Message = fields.Str()
    Status = fields.Enum(StatusEnum, by_value=True)

    @post_load()
    def make_object(self, data, **kwargs):
        return Response(**data)
    
class JSONCommandSchema(Schema):
    operation = fields.Str()
    request = fields.Str()
    cancelKey = fields.Str()

class JSONCommand():
    def __init__(self, operation, request, cancelKey):
        self.operation = operation
        self.request = request
        self.cancelKey = cancelKey

def add_json_preamble(json: str) -> str:
    return f"json{json}"



class Response():
    def __init__(self, Err, Message, Status):
        self.Err = Err
        self.Message = Message
        self.Status = Status
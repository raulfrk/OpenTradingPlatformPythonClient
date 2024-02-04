import uuid

from marshmallow import Schema, fields, post_load

from otpclient.client.enums import JSONOperationEnum


class JSONCommandSchema(Schema):
    operation = fields.Enum(JSONOperationEnum, by_value=True)
    request = fields.Str()
    cancelKey = fields.Str()

    @post_load()
    def make_object(self, data, **kwargs):
        return JSONCommand(**data)


class JSONCommand:
    def __init__(self, operation: JSONOperationEnum, request: str, cancelKey):
        self.operation: JSONOperationEnum = operation
        self.cancelKey = cancelKey
        self.request: str | None = request

    def dump(self, no_preamble: bool = False) -> str:
        dump = JSONCommandSchema().dumps(self).replace("\"{", "{").replace("}\"", "}").replace("\\", "")
        if no_preamble:
            return dump
        return add_json_preamble(dump)

    @classmethod
    def load(cls, json: str) -> "JSONCommand":
        if has_json_preamble(json):
            json = remove_json_preamble(json)
        return JSONCommandSchema().loads(json)


class CancelRemote:
    def __init__(self, cancel_key: str):
        self.cancel_key = cancel_key

    def dump(self, no_preamble: bool = False) -> str:
        return JSONCommand(JSONOperationEnum.CANCEL, "", self.cancel_key).dump(no_preamble)

    @classmethod
    def load(cls, json: str) -> "CancelRemote":
        if has_json_preamble(json):
            json = remove_json_preamble(json)
        command = JSONCommandSchema().loads(json)
        return cls(command.cancelKey)

    @classmethod
    def generate(cls) -> "CancelRemote":
        return cls(uuid.uuid4().hex)


def add_json_preamble(json: str) -> str:
    return f"json{json}"


def has_json_preamble(json: str) -> bool:
    return json.startswith("json")


def remove_json_preamble(json: str) -> str:
    return json[4:]

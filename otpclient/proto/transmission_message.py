import otpclient.proto.transmission_message_pb2 as transmission_message_pb2


class TransmissionMessage:
    def __init__(self, proto_bar) -> None:
        self.topic: str = proto_bar.Topic
        self.payload: bytes = proto_bar.Payload
        self.data_type: str = proto_bar.DataType

    @classmethod
    def load(cls, proto: bytes) -> "TransmissionMessage":
        message = transmission_message_pb2.Message()  # type: ignore
        message.ParseFromString(proto)
        return TransmissionMessage(message)

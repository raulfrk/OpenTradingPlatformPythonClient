from enum import Enum


class TimeFrameEnum(Enum):
    ONE_MINUTE = "1min"
    ONE_HOUR = "1hour"
    ONE_DAY = "1day"
    ONE_WEEK = "1week"
    ONE_MONTH = "1month"
    NO_TIMEFRAME = "none"


class ComponentEnum(Enum):
    DATAPROVIDER = "dataprovider"
    DATASTORAGE = "datastorage"
    SENTIMENT_ANALYZER = "sentiment-analyzer"


class JSONOperationEnum(Enum):
    STREAM = "stream"
    DATA = "data"
    STREAM_SUBSCRIBE = "stream-subscribe"
    CANCEL = "cancel"
    QUIT = "quit"


class FunctionalityEnum(Enum):
    COMMAND = "command"


class SourceEnum(Enum):
    ALPACA = "alpaca"
    INTERNAL = "internal"


class AssetClassEnum(Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    NEWS = "news"


class DatatypeEnum(Enum):
    LOG = "log"
    BAR = "bar"
    LULD = "luld"
    STATUS = "status"
    ORDERBOOK = "orderbook"
    DAILY_BARS = "daily-bars"
    QUOTES = "quotes"
    TRADES = "trades"
    UPDATED_BARS = "updated-bars"
    RAW_TEXT = "raw-text"
    SENTIMENT = "sentiment"
    NEWS_WITH_SENTIMENT = "news-with-sentiment"


class OPStatusEnum(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class LLMProviderEnum(Enum):
    OLLAMA = "ollama"
    GPT4ALL = "gpt4all"


class SentimentAnalysisProcessEnum(Enum):
    PLAIN = "plain"
    SEMANTIC = "semantic"


class DataRequestOPEnum(Enum):
    GET = "get"


class StreamRequestOPEnum(Enum):
    ADD = "add"
    REMOVE = "remove"
    GET = "get"


class AccountEnum(Enum):
    DEFAULT = "default"

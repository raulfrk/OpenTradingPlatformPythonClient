from typing import Any

import pandas as pd

from otpclient.proto.news_pb2 import News as NewsProto
from otpclient.proto.news_pb2 import NewsSentiment as NewsSentimentProto


class NewsSentiment:
    def __init__(self, news_proto: NewsSentimentProto) -> None:
        self.timestamp: int = news_proto.Timestamp
        self.news: News = news_proto.News
        self.sentiment: str = news_proto.Sentiment
        self.sentiment_analysis_process: str = news_proto.SentimentAnalysisProcess
        self.fingerprint: str = news_proto.Fingerprint
        self.llm: str = news_proto.LLM
        self.symbol: str = news_proto.Symbol
        self.system_prompt: str = news_proto.SystemPrompt
        self.failed: bool = news_proto.Failed
        self.raw_sentiment: str = news_proto.RawSentiment

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = NewsSentimentProto()
        entity.ParseFromString(proto)
        return NewsSentiment(entity)

    @classmethod
    def list_to_dataframe(cls, entities: list["LULD"]):
        data = [entity.__dict__ for entity in entities]
        if len(data) == 0:
            return pd.DataFrame()
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        # Convert timestamp to datetime and set it as the index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)

        # Drop the original "timestamp" column
        df.drop(columns=['timestamp'], inplace=True, errors="ignore")

        # df = df.astype(dtypes)
        return df


class News:
    def __init__(self, news_proto: NewsProto) -> None:
        self.id: int = news_proto.id
        self.author: str = news_proto.Author
        self.created_at: int = news_proto.CreatedAt
        self.updated_at: int = news_proto.UpdatedAt
        self.headline: str = news_proto.Headline
        self.summary: str = news_proto.Summary
        self.content: str = news_proto.Content
        self.url: str = news_proto.URL
        self.symbols: list[str] = news_proto.Symbols
        self.fingerprint: str = news_proto.Fingerprint
        self.source: str = news_proto.Source
        self.sentiments: list[NewsSentiment] = [NewsSentiment(sentiment) for sentiment in news_proto.Sentiments]

    @classmethod
    def load(cls, proto: bytes) -> Any:
        entity = NewsProto()
        entity.ParseFromString(proto)
        return News(entity)

    @classmethod
    def list_to_dataframe(cls, entities: list["News"]):
        data = [entity.__dict__ for entity in entities]

        for d in data:
            d["sentiments"] = NewsSentiment.list_to_dataframe(d["sentiments"])
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame.from_records(data)

        df['created_at'] = pd.to_datetime(df['created_at'], unit='s')
        df['updated_at'] = pd.to_datetime(df['updated_at'], unit='s')
        df.set_index('created_at', inplace=True)

        df.drop(columns=['created_at'], inplace=True, errors="ignore")

        return df

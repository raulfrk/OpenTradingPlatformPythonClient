import asyncio
from datetime import datetime, timedelta

import pandas as pd

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, OPStatusEnum, TimeFrameEnum, \
    SentimentAnalysisProcessEnum, LLMProviderEnum
from otpclient.client.request.request import CancelRemote
from otpclient.client.user_client import UserClient
from otpclient.proto.news import News


async def main():
    # GOAL: Perform plain sentiment analysis on the news related to AAPL of the last 3 days.
    # Also perform aspect based sentiment analysis on the same news

    # 1. Create a new client
    client: UserClient = await UserClient.new()

    # 2. Request data from OTP platform (news data for AAPL)
    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA,
        AssetClassEnum.NEWS,
        "AAPL",
        DatatypeEnum.RAW_TEXT,
        AccountEnum.DEFAULT,
        start_time=datetime.now() - timedelta(days=3),
        end_time=datetime.now(),
        time_frame=TimeFrameEnum.ONE_MINUTE,
        no_confirm=True
    )

    if response.Status != OPStatusEnum.SUCCESS:
        print(f"Failed to get news data: {response.message}")
        return
    print("Wait for database to populate")
    await asyncio.sleep(5)
    # 3. Perform sentiment analysis on the news data
    # Create a cancel remote, in case you want to cancel the request prematurely
    cancel = CancelRemote.generate()
    response = await client.sentimentanalyzer.data_get(
        SourceEnum.ALPACA,
        "AAPL",
        start_time=datetime.now() - timedelta(days=3),
        end_time=datetime.now(),
        sentiment_analysis_process=SentimentAnalysisProcessEnum.PLAIN,
        model="orca2",
        model_provider=LLMProviderEnum.OLLAMA,
        system_prompt="You are a markets expert. Analyze the sentiment of this financial news related to the given "
                      "symbol and respond with one of the following words about the sentiment [positive, negative, "
                      "neutral]. Respond with only one word.",
        timeout_sec=60 * 5,
        cancel_remote=cancel
    )

    if response.Status != OPStatusEnum.SUCCESS:
        print(f"Failed to perform sentiment analysis: {response.message}")
        return

    # 4. Resolve the data
    data: list[News] = await client.resolve_data(response)
    print("Sentiment analysis results (plain analysis):")
    print(News.list_to_dataframe(data))

    await asyncio.sleep(1)

    # A similar process can be followed for aspect based sentiment analysis
    cancel = CancelRemote.generate()
    response = await client.sentimentanalyzer.data_get(
        SourceEnum.ALPACA,
        "AAPL",
        start_time=datetime.now() - timedelta(days=3),
        end_time=datetime.now(),
        sentiment_analysis_process=SentimentAnalysisProcessEnum.SEMANTIC,  # Note the change in process
        model="orca2",
        model_provider=LLMProviderEnum.OLLAMA,
        system_prompt="Perform aspect base sentiment analysis of the given news in relation with the given symbols. "
                      "Reply with a single well formed, correct json object where each key is the name of the symbol "
                      "and the value is the sentiment of the news in relation to the symbol. The sentiment can be one "
                      "of the following: positive, negative, neutral. (e.g. {'AAPL': 'positive'}). Your response "
                      "should be directly parsable by a json parser.",  # The prompt was also changed
        timeout_sec=60 * 5,
        cancel_remote=cancel,
    )

    if response.Status != OPStatusEnum.SUCCESS:
        print(f"Failed to perform sentiment analysis: {response.message}")
        return

    data: list[News] = await client.resolve_data(response)
    df = News.list_to_dataframe(data)
    print("Sentiment analysis results (aspect based analysis):")
    print(df)

    print("Example of filtering sentiment analysis results:")
    # Get first news
    news = df.head(1)
    sent_first_row = news["sentiments"].values[0]

    # Get all sentiments that did not fail for that news and are from semantic analysis
    filtered_sent: pd.DataFrame = \
        sent_first_row[~sent_first_row["failed"] & (sent_first_row["sentiment_analysis_process"] == "semantic")][
            ["sentiment", "symbol"]]
    # Add the headline to the DataFrame
    filtered_sent["headline"] = news["headline"].values[0]

    # Print a csv dump of the data
    print(filtered_sent.to_csv(index=False))

    # Alternatively, you can request data and resolve it in one go
    news: list[News] = await client.sentimentanalyzer.data_get_autoresolve(
        SourceEnum.ALPACA,
        "AAPL",
        start_time=datetime.now() - timedelta(days=3),
        end_time=datetime.now(),
        sentiment_analysis_process=SentimentAnalysisProcessEnum.PLAIN,
        model="orca2",
        model_provider=LLMProviderEnum.OLLAMA,
        system_prompt="You are a markets expert. Analyze the sentiment of this financial news related to the given "
                      "symbol and respond with one of the following words about the sentiment [positive, negative, "
                      "neutral]. Respond with only one word.",
        timeout_sec=60 * 5,
        cancel_remote=cancel
    )
    print("Received data:", len(news))



    # 6. Close client
    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

import asyncio
from datetime import datetime, timedelta

import pandas as pd

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum
from otpclient.client.user_client import UserClient
from otpclient.proto.quote import Quote


async def main():
    # GOAL: Request Bar data for BTC/USD, subscribe to BTC/USD data feed, update the data dataframe with new data for 5 datapoints
    # This is a typical usage in a trading strategy where you want to fetch historical data and then subscribe to the data feed

    # 1. Create a new client
    client: UserClient = await UserClient.new()

    # 2. Request data from OTP platform (last week's Quote data for BTC/USD)
    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA,
        AssetClassEnum.CRYPTO,
        "BTC/USD",
        DatatypeEnum.QUOTES,
        AccountEnum.DEFAULT,
        start_time=datetime.now() - timedelta(weeks=1),
        end_time=datetime.now() - timedelta(minutes=15),
        time_frame=TimeFrameEnum.ONE_MINUTE
    )

    # 3. Retrieve the data
    data: list[Quote] = await client.resolve_data(response)

    # 4. Convert the data to a pandas DataFrame
    df = Quote.list_to_dataframe(data)

    print("Current dataframe size (after data fetch): ", df.shape)

    # 5. Subscribe to the data feed
    response, _, _ = await client.dataprovider.stream_add(
        source=SourceEnum.ALPACA,
        asset_class=AssetClassEnum.CRYPTO,
        symbols=["BTC/USD"],
        data_types=[DatatypeEnum.QUOTES],
        account=AccountEnum.DEFAULT
    )

    collection = client.dataprovider.get_subscription_collection()
    if collection is None:
        raise Exception("Subscription collection is None")
    q = asyncio.Queue()

    # Subscribe to streams that match criteria and store the data in a queue
    await collection.subscribe_queue(q, data_types=[DatatypeEnum.QUOTES], symbols=["BTC/USD"])

    # 6. Wait to receive 4 data points. Update the dataframe with each new data point
    for _ in range(4):
        data = await q.get()
        df = pd.concat([df, Quote.list_to_dataframe([data])])
        print("Updated dataframe size (after adding a new row): ", df.shape)

    # 7. Print dataframe
    print("Data as a pandas DataFrame:")
    print(df)
    # 8. Close client
    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

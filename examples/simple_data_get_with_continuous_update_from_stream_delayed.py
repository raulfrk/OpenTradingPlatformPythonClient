import asyncio
from datetime import datetime, timedelta

import pandas as pd

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum
from otpclient.client.user_client import UserClient
from otpclient.proto.bar import Bar


async def main():
    # GOAL: Request Bar data for BTC/USD, subscribe to BTC/USD data feed. Handle Alpaca restrictions: * You cannot
    # get historical data that is more recent than 15 minutes To get around this issue, we will first request
    # historical data that is 15 minutes old, and then subscribe to the data feed, after 15 minutes have passed
    # update with the missing 15 minutes of data

    # 1. Create a new client
    client: UserClient = await UserClient.new()

    # 2. Request data from OTP platform (this week's Bar data for BTC/USD)
    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA,
        AssetClassEnum.CRYPTO,
        "BTC/USD",
        DatatypeEnum.BAR,
        AccountEnum.DEFAULT,
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now() - timedelta(minutes=15),
        time_frame=TimeFrameEnum.ONE_MINUTE
    )

    # 3. Retrieve the data
    data: list[Bar] = await client.resolve_data(response)

    # 4. Convert the data to a pandas DataFrame
    df = Bar.list_to_dataframe(data)
    df_lock = asyncio.Lock()
    print("Received initial data")
    print("Current dataframe size (after data fetch): ", df.shape)
    print(df.tail(1).index.values[0])

    # 5. Subscribe to the data feed
    response, _, _ = await client.dataprovider.stream_add(
        source=SourceEnum.ALPACA,
        asset_class=AssetClassEnum.CRYPTO,
        symbols=["BTC/USD"],
        data_types=[DatatypeEnum.BAR],
        account=AccountEnum.DEFAULT
    )

    collection = client.dataprovider.get_subscription_collection()
    if collection is None:
        raise Exception("Subscription collection is None")
    q = asyncio.Queue()

    # Subscribe to streams that match criteria and store the data in a queue
    await collection.subscribe_queue(q, data_types=[DatatypeEnum.BAR], symbols=["BTC/USD"])

    # 7. Start a task that will update the dataframe with new data points
    async def update_df():
        nonlocal df
        while True:
            dt: Bar | None = await q.get()
            if dt is None:
                break
            async with df_lock:
                df = pd.concat([df, Bar.list_to_dataframe([dt])])
                print("Updated dataframe size (after adding a new row): ", df.shape)
                print(datetime.utcfromtimestamp(dt.timestamp))

    t = asyncio.create_task(update_df())
    print("Subscribed to BTC/USD data feed")

    # 8. Wait for 15 minutes
    print("Waiting for 15 minutes...")
    await asyncio.sleep(15 * 60)

    # 9. Fetch the missing 15 minutes of data
    print("Fetching missing 15 minutes of data")
    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA,
        AssetClassEnum.CRYPTO,
        "BTC/USD",
        DatatypeEnum.BAR,
        AccountEnum.DEFAULT,
        start_time=datetime.now() - timedelta(minutes=30),
        end_time=datetime.now() - timedelta(minutes=14),
        time_frame=TimeFrameEnum.ONE_MINUTE
    )

    data: list[Bar] = await client.resolve_data(response)
    async with df_lock:
        df = pd.concat([df, Bar.list_to_dataframe(data)])
        print("Updated dataframe size (after adding missing 15 minutes of data): ", df.shape)

    q.put_nowait(None)
    t.cancel()

    # 10. Print dataframe
    # Note: this dataframe does not have the 15 minutes gap
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

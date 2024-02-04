import asyncio
from datetime import datetime, timedelta

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum
from otpclient.client.user_client import UserClient
from otpclient.proto.bar import Bar


async def main():
    # GOAL: Request Bar data for BTC/USD, print the first 5 data points, and convert the data to a pandas DataFrame

    # 1. Create a new client
    client: UserClient = await UserClient.new()

    # 2. Request data from OTP platform (last week's Bar data for BTC/USD)
    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA,
        AssetClassEnum.CRYPTO,
        "BTC/USD",
        DatatypeEnum.BAR,
        AccountEnum.DEFAULT,
        start_time=datetime.now() - timedelta(weeks=1),
        end_time=datetime.now() - timedelta(minutes=15),
        time_frame=TimeFrameEnum.ONE_MINUTE
    )

    # 3. Retrieve the data
    data: list[Bar] = await client.resolve_data(response)

    # 4. Print the first 5 data points
    print(f"First 5 data points for BTC/USD Bar data:")
    for d in data[:5]:
        print(d.__dict__)

    # 5. Convert the data to a pandas DataFrame
    df = Bar.list_to_dataframe(data)
    print("Data as a pandas DataFrame:")
    print(df)

    # 6. Close client
    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

import asyncio

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, OPStatusEnum
from otpclient.client.user_client import UserClient


async def main():
    # GOAL: Subscribe to Quote data for BTC/USD, store it in a queue and print it as it comes in

    # 1. Create a new client
    client: UserClient = await UserClient.new()

    # 2. Instruct OTP platform to start streaming Quotes for BTC/USD, ETH/USD
    response, sub_potentials, _ = await client.dataprovider.stream_add(
        source=SourceEnum.ALPACA,
        asset_class=AssetClassEnum.CRYPTO,
        symbols=["BTC/USD", "ETH/USD"],
        data_types=[DatatypeEnum.QUOTES],
        account=AccountEnum.DEFAULT
    )

    # 3. Check if the subscription was successful
    if response.Status != OPStatusEnum.SUCCESS:
        print(f"Failed to subscribe to BTC/USD Quote data: {response.message}")
        return

    # With the above code, we have instructed OTP platform to start streaming Quote data for BTC/USD.

    # We will define a queue to receive the data
    q = asyncio.Queue()
    # Get the collection of subscription potentials
    collection = client.dataprovider.get_subscription_collection()
    if collection is None:
        raise Exception("Subscription collection is None")
    # Subscribe to streams that match criteria
    await collection.subscribe_queue(q, data_types=[DatatypeEnum.QUOTES])

    # 4. Wait to receive 4 data points

    print("Waiting for 4 data points...")
    for _ in range(4):
        data = await q.get()
        # Print the data
        print(data.__dict__)

    # 8. Clean up
    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

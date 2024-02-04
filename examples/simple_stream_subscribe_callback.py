import asyncio

from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, OPStatusEnum
from otpclient.client.user_client import UserClient
from otpclient.proto.quote import Quote


async def main():
    # GOAL: Subscribe to Quote data for BTC/USD and print the data as it comes in

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
    # We have not yet subscribed to this data on the client side. To do that we can use the subscription potentials

    # We will define a queue to wait for the data to come in
    q = asyncio.Queue()

    async def print_data(data: Quote):
        print(data.__dict__)
        await q.put(None)

    # 4. Client-side subscribe through the subscription potentials
    for sub_potential in sub_potentials:
        await sub_potential.subscribe(print_data)

    # 5. Wait to receive the signal that two Quote data points have been received
    print("Waiting for 2 data points...")
    for _ in range(2):
        await q.get()

    # 6. Stop client-side subscription (OTP will continue to stream data)
    for sub_potential in sub_potentials:
        await sub_potential.unsubscribe()

    # clean up the queue
    while not q.empty():
        try:
            q.get_nowait()
        except:
            break

    # 7. Instruct OTP platform to stop streaming Quote for BTC/USD (Note: all active subsciprionts on client-side for
    # those symbols will be automatically unsubscribed)
    response, _ = await client.dataprovider.stream_remove(
        source=SourceEnum.ALPACA,
        asset_class=AssetClassEnum.CRYPTO,
        symbols=["BTC/USD"],
        data_types=[DatatypeEnum.QUOTES],
        account=AccountEnum.DEFAULT
    )

    # Alternative way to subscribe to data
    # Each client keeps track of the client-side subscriptions with the SubscriptionCollection
    # This can be used to get all subscriptions, filter them, and even subscribe in batches

    collection = client.dataprovider.get_subscription_collection()
    # To filter subscriptions, simply pass the criteria that need to be met. If no criteria is passed,
    # all subscription potentials are returned
    sp = await collection.subscribe_callback(print_data,
                                             asset_class=[AssetClassEnum.CRYPTO],
                                             symbols=["ETH/USD"],
                                             data_types=[DatatypeEnum.QUOTES])

    # Print current active subscriptions
    print("Currently subscribed to", [x.topic for x in sp if await x.is_subscribed()])

    # In this case we are saying to assign the print_data callback to all ETH/USD Quote data
    # Wait for one data point to come in
    print("Waiting for 1 data point...")
    await q.get()

    # 8. Clean up
    await client.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

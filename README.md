# OpenTradingPlatformPythonClient

OpenTradingPlatformPythonClient is a Python client for the Open Trading Platform (OTP) API.
The client is designed to be easy to use and to provide a simple interface to the OTP API.

The client matches closely the subdivision of the OTP server in components and provides a sub-client with tailored
functionalities for each component.

The components that the client supports are:

- Dataprovider
    - Used to fetch data from a broker
    - Used to subscribe to data streams from a broker
- Datastorage
    - Used to store data in a database
    - Used to retrieve data from a database
- SentimentAnlyzer
    - Used to analyze the sentiment of a given news stored in the database

**You can find more advanced examples of client use cases in the `examples` directory.**

## Clients

The Python Client library is made of two main clients:

### SystemClient

The system client is used to perform operations on the OTP system level. Currently the only operation that is supported
is `quit` which can be used in the following way:

```python
import asyncio
from otpclient.client.system_client import SystemClient
from otpclient.client.enums import ComponentEnum


async def main():
    client = await SystemClient.new()

    await client.quit(ComponentEnum.DATAPROVIDER)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

```

The parameter `ComponentEnum.DATAPROVIDER` is used to specify the component that should be stopped.
Once this is run, the component will quit gracefully.

**IMPORTANT:** The use of `enums` is quite common with this client, since it allows to be very specific with the options
passed to a given function. The enums are defined in the `otpclient.client.enums` module. Have a look when you are not
sure what parameters to pass to a function.

## UserClient

The user client is used to group 3 sub-clients, one for each component. The sub-clients are:

- DataproviderClient
- DatastorageClient
- SentimentAnalyzerClient

**A quick but important note on thread safety:** All the methods that "public" are thread safe. This means that you do
not
need to worry about running into race conditions when using the client in a multi-threaded environment. The client
handles
all the concurrency for you. **However:** Some classes have private methods that start with `_unsafe` prefix (
e.g. `_unsafe_sync`).
This methods are not meant to be called directly since they are not thread safe. They are used internally by the client
and should
not be used by the user.

Accessing any of those clients can be done using an instance of the `UserClient` class. As can be seen in the following
example:

```python
import asyncio
from otpclient.client.user_client import UserClient


async def main():
    client = await UserClient.new()

    print("Dataprovider Client: ", client.dataprovider)
    print("Datastorage Client: ", client.datastorage)
    print("Sentiment Analyzer Client: ", client.sentimentanalyzer)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

**IMPORTANT:** When calling `await UserClient.new()` the client will try to connect to NATS using the default ip and
port:
`nats://localhost:4222` if OTP runs on a different host, simply change the hostname and port (
e.g. `await UserClient.new("nats://someip:1234")`)

### DataproviderClient

The `DataproviderClient` is used to fetch data from a broker and to subscribe to data streams from a broker. The client
provides the following functionalities:

- Fetch data from a broker
- Request OTP to subscribe to a data stream from a broker
- Request OTP to unsubscribe from a data stream from a broker

#### Fetch data from a broker

To fetch data from a broker, the `data_get` method can be used. Here is an example of how to use it:

```python
import asyncio
from otpclient.client.user_client import UserClient
from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum, OPStatusEnum
from otpclient.proto.bar import Bar
from datetime import datetime, timedelta


async def main():
    client = await UserClient.new()

    response = await client.dataprovider.data_get(
        SourceEnum.ALPACA, AssetClassEnum.STOCK, "AAPL", DatatypeEnum.BAR, AccountEnum.DEFAULT,
        datetime.now() - timedelta(days=1), datetime.now() - timedelta(minutes=15), TimeFrameEnum.ONE_MINUTE
    )

    if response.Status == OPStatusEnum.SUCCESS:
        raise Exception("Failed to request data")

    data: list[Bar] = await client.resolve_data(response)

    print(data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

First we request data to OTP using the `dataprovider.data_get` method. The parameters are mostly ENUM values that
can be found in the `otpclient.client.enums` module. The `data_get` method returns a `DataResponse` object that contains
the confirmation of whether the request was successful or not.
**IMPORTANT:** The response does not contain the actual data! The data must be resolved using the `resolve_data` method
which actually fetches data from the platform and returns it. There is a timeout for how long the data can be resolved,
if the data is not resolved within the timeout, the cached data is dropped by OTP and a new request will need to be
made.
It is good practice to always resolve the data as soon as the response is received.

#### Subscribe and unsubscribe to a data stream from a broker

To subscribe to a data stream from a broker, the `stream_add` method can be used. Here is an example of how to use it:

```python
import asyncio
from otpclient.client.user_client import UserClient
from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum, OPStatusEnum
from otpclient.proto.bar import Bar


async def main():
    client = await UserClient.new()

    response, potential_sub, updates = await client.dataprovider.stream_add(
        SourceEnum.ALPACA, AssetClassEnum.STOCK, ["AAPL"], [DatatypeEnum.BAR], AccountEnum.DEFAULT,
    )

    if response.Status == OPStatusEnum.SUCCESS:
        raise Exception("Failed to request data subscription")

    async def handle_data(data: Bar):
        print(data)

    for sub in potential_sub:
        await sub.subscribe(handle_data)

    await asyncio.sleep(120)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

In this example, first we ask the OTP to subscribe to a data stream from a broker using the `dataprovider.stream_add`
method.
This method has an effect only on the OTP, the client will not receive data unless it actively subscribes to the data
stream.
The `stream_add` method returns three values:

- The response from OTP
- A list of potential subscriptions
    - These can be used to ask the client to subscribe to the data stream
- A list of updates (we will ignore these for now)

Each potential subscription object is used with the `subscribe` method to assign a callback (that indicates what to do
with the data when received)
and to actually subscribe to the data stream.

If you would like the client to unsubscribe from the data stream simply call the `unsubscribe` method on the
subscription potential object.

```python
import asyncio
from otpclient.client.user_client import UserClient
from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum, OPStatusEnum
from otpclient.proto.bar import Bar


async def main():
    client = await UserClient.new()

    response, potential_sub, updates = await client.dataprovider.stream_add(
        SourceEnum.ALPACA, AssetClassEnum.STOCK, ["AAPL"], [DatatypeEnum.BAR], AccountEnum.DEFAULT,
    )

    if response.Status == OPStatusEnum.SUCCESS:
        raise Exception("Failed to request data subscription")

    async def handle_data(data: Bar):
        print(data)

    for sub in potential_sub:
        await sub.subscribe(handle_data)

    await asyncio.sleep(120)

    # Unsubscribe from the data stream
    for sub in potential_sub:
        await sub.unsubscribe()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

If on the other hand you would like the OTP to completely remove the subscription, you can use the `stream_remove`
method.

```python
import asyncio
from otpclient.client.user_client import UserClient
from otpclient.client.enums import SourceEnum, AssetClassEnum, DatatypeEnum, AccountEnum, TimeFrameEnum, OPStatusEnum
from otpclient.proto.bar import Bar


async def main():
    client = await UserClient.new()

    response, potential_sub, updates = await client.dataprovider.stream_add(
        SourceEnum.ALPACA, AssetClassEnum.STOCK, ["AAPL"], [DatatypeEnum.BAR], AccountEnum.DEFAULT,
    )

    if response.Status == OPStatusEnum.SUCCESS:
        raise Exception("Failed to request data subscription")

    async def handle_data(data: Bar):
        print(data)

    for sub in potential_sub:
        await sub.subscribe(handle_data)

    await asyncio.sleep(120)

    # OTP will remove the subscription
    response, potential_sub, updates = await client.dataprovider.stream_remove(
        SourceEnum.ALPACA, AssetClassEnum.STOCK, ["AAPL"], [DatatypeEnum.BAR], AccountEnum.DEFAULT,
    )

    if response.Status == OPStatusEnum.SUCCESS:
        raise Exception("Failed to stop data subscription")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

With this method, the OTP will remove the subscription form the broker completely.

**IMPORTANT**: This means that other clients will stop receiving the data stream you stopped as well.

**NOTE:** Using this method also stops the message handling of the client. Next time you add that stream
with `stream_add`
you will need to reassign the callback and subscribe to the data stream again using the resulting stream potentials.

### DatastorageClient

The `DatastorageClient` is used to get data from the database. It exposes the `data_get` that takes the same parameters
as
the one in the `DataproviderClient` and the resulting response needs to be resolved using `data_resolve`.

**Note:** All data that is fetched or subscribed to through the dataprovider is stored in the database. The datastorage
component can be used as a cache to avoid retrieving the same data multiple times from the dataprovider (which takes
time).
If in doubt whether the data is in the database, just fetch the data from the dataprovider first, and then use the
database
the other times when making the same request.

### SentimentAnalyzerClient

The `SentimentAnalyzerClient` is used to analyze the sentiment of a given news stored in the database. It exposes the
`data_get` method with a slight difference in the parameters compared to other parameters. The approach to resolve data
once ready
is the same as with the `DataproviderClient` and the `DatastorageClient`.

```python
import asyncio
from otpclient.client.user_client import UserClient
from otpclient.client.enums import SourceEnum, OPStatusEnum
from datetime import datetime, timedelta
from otpclient.proto.news import News
from otpclient.client.enums import SentimentAnalysisProcessEnum, LLMProviderEnum
from otpclient.client.request.sentimentanalysis_request import CancelRemote


async def main():
    client = await UserClient.new()
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

    data: list[News] = await client.resolve_data(response)
    print(data)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
```

In this example, we request the sentiment of a news related to the symbol "AAPL" using the `sentimentanalyzer.data_get`
method.
For this to work, the news must be stored in the database, if unsure, use the `DataproviderClient` to fetch the news
first.
Once the response is received, the data can be resolved using the `resolve_data` method.

One of the parameters that can be passed to the `data_get` method is the `cancel_remote` parameter. This parameter is
used to
cancel the sentiment analysis process prematurely if needed. To cancel it just call `client.cancel(cancel)`
where `cancel` is the
object returned by the `CancelRemote.generate()` method and passed to the `data_get` method. Calling the cancel method
will
stop the sentiment analysis process and generation by the LLM will stop. If cancelled the `data_get` method will raise
a `CancelledError` exception.
from datetime import datetime

from nats.aio.client import Client

from otpclient.client.client import OtpClient
from otpclient.client.enums import SourceEnum, DataRequestOPEnum, SentimentAnalysisProcessEnum, LLMProviderEnum, \
    OPStatusEnum, ComponentEnum, FunctionalityEnum
from otpclient.client.exception import ServerError, CancelledError
from otpclient.client.request.request import CancelRemote
from otpclient.client.request.sentimentanalysis_request import SentimentAnalysisRequest
from otpclient.client.response.response import DataResponse, Response


class SentimentAnalyzerClient(OtpClient):
    """Client for interacting with the SentimentAnalyzer component of the OTP system.
        This client is used to request data and subscribe to data streams."""

    def __init__(self, nats_client: Client):
        super().__init__(nats_client)
        self.command_topic = (
            f"{ComponentEnum.SENTIMENT_ANALYZER.value}.{FunctionalityEnum.COMMAND.value}"
        )
        self.logger = self.logger.bind(
            command_topic=self.command_topic,
        )

    async def cancel(self, remote: CancelRemote):
        """Cancel a remote request."""
        logger = self.logger.bind(cancel_key=remote)
        response = await self.nc.request(self.command_topic, remote.dump().encode())
        print(response.data)
        obj_response = Response.load(response.data.decode())
        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Cancel operation failed", response=obj_response.Err)
            raise ServerError(obj_response.Err)
        logger.info("Cancel operation was successful", response=obj_response.Message)

        return obj_response

    async def data_get(self,
                       source: SourceEnum,
                       symbol: str,
                       start_time: datetime,
                       end_time: datetime,
                       sentiment_analysis_process: SentimentAnalysisProcessEnum,
                       model: str,
                       model_provider: LLMProviderEnum,
                       system_prompt: str,
                       retry_failed: bool = False,
                       fail_fast_on_bad_sentiment: bool = False,
                       no_confirm: bool = False,
                       timeout_sec: int = 60,
                       cancel_remote: CancelRemote = None
                       ) -> DataResponse:
        """Request OTP component to get data for the given parameters. Setting no_confirm to True will tell the OTP server to
        start streaming the data without waiting for a confirmation from the client that it is listening."""
        start_time_unix = int(start_time.timestamp())
        end_time_unix = int(end_time.timestamp())
        logger = self.logger.bind(source=source, symbol=symbol,
                                  start_time=start_time, end_time=end_time,
                                  sentiment_analysis_process=sentiment_analysis_process,
                                  model=model, model_provider=model_provider, system_prompt=system_prompt,
                                  fail_fast_on_bad_sentiment=fail_fast_on_bad_sentiment, retry_failed=retry_failed,
                                  no_confirm=no_confirm, timeout_sec=timeout_sec)
        logger.info("Requesting data get")

        req = SentimentAnalysisRequest(
            source,
            symbol,
            DataRequestOPEnum.GET,
            start_time_unix,
            end_time_unix,
            no_confirm,
            sentiment_analysis_process,
            model,
            model_provider,
            system_prompt,
            fail_fast_on_bad_sentiment,
            retry_failed,
            cancel_remote
        ).wrap().dump()
        response = await self.nc.request(
            self.command_topic,
            req.encode(),
            timeout=timeout_sec,
        )

        obj_response = DataResponse.load(response.data.decode())
        if obj_response.Status != OPStatusEnum.SUCCESS:
            logger.error("Data get failed", response=obj_response.Err)
            if "canceled" in obj_response.Err.lower():
                raise CancelledError(obj_response.Err)
            raise ServerError(obj_response.Err)
        logger.info("Data get successful", response=obj_response.Message)

        return obj_response

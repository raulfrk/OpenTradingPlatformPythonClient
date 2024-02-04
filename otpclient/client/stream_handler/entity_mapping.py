from otpclient.client.enums import DatatypeEnum
from otpclient.proto.bar import Bar, DailyBars, UpdatedBars
from otpclient.proto.luld import LULD
from otpclient.proto.news import News
from otpclient.proto.orderbook import Orderbook
from otpclient.proto.proto_loadable import ProtoLoadable
from otpclient.proto.quote import Quote
from otpclient.proto.trade import Trade
from otpclient.proto.tradingstatus import TradingStatus

# Mapping of DatatypeEnum to ProtoLoadable classes
loadable_map: dict[DatatypeEnum, ProtoLoadable] = {
    DatatypeEnum.BAR: Bar,
    DatatypeEnum.QUOTES: Quote,
    DatatypeEnum.ORDERBOOK: Orderbook,
    DatatypeEnum.LULD: LULD,
    DatatypeEnum.TRADES: Trade,
    DatatypeEnum.RAW_TEXT: News,
    DatatypeEnum.NEWS_WITH_SENTIMENT: News,
    DatatypeEnum.STATUS: TradingStatus,
    DatatypeEnum.DAILY_BARS: DailyBars,
    DatatypeEnum.UPDATED_BARS: UpdatedBars,
}

import json
import pytz
import asyncio
import datetime
import pandas as pd
import os
from tda import auth, client
from tda.streaming import StreamClient
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

from broker_config import (
    tda_token_path,
    tda_api_key,
    tda_redirect_uri,
    tda_account_id,
)

class TDAClient:
    def __init__(self):
        """
        Initialize the TDAClient class.
        """
        self.class_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_path = os.path.join(self.class_dir, 'token')
        self.client = self.authentication()

    def authentication(self):
        """
        Authenticate the TD Ameritrade client.

        :return: An authenticated client.
        """
        try:
            c = auth.client_from_token_file(self.token_path, tda_api_key)
        except FileNotFoundError:
            print(
                "No Available Token File. Starting Chrome authentication process to generate token file"
            )
            driver = webdriver.Chrome(ChromeDriverManager().install())
            c = auth.client_from_login_flow(driver, tda_api_key, tda_redirect_uri, tda_token_path)
        return c

    @staticmethod
    def is_trading_hour(dt):
        """
        Check if the given datetime is within trading hours.

        :param dt: A datetime object.
        :return: A boolean indicating if it is within trading hours.
        """
        dt_pacific = dt.tz_convert("US/Pacific")
        hour = dt_pacific.hour
        minute = dt_pacific.minute
        weekday = dt_pacific.weekday()

        return (6, 30) <= (hour, minute) < (13, 0) and weekday < 5

    def get_historical_daily_bar(self, ticker, start_date, end_date):
        """
        Get historical daily bars for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :param start_date: The start date as a string in the format "%Y-%m-%d".
        :param end_date: The end date as a string in the format "%Y-%m-%d".
        :return: A DataFrame with historical daily bars.
        """
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        base = client.Client.PriceHistory
        r = (
            self.client.get_price_history(
                ticker.upper(),
                period_type=base.PeriodType.YEAR,
                start_datetime=start_date,
                end_datetime=end_date,
                frequency_type=base.FrequencyType.DAILY,
                need_extended_hours_data=None,
            )
            .json()["candles"]
        )
        df = pd.DataFrame(r)
        df["datetime"] = (
            pd.to_datetime(df["datetime"], utc=True, unit="ms")
            .dt.date
        )
        df = df.rename(
            columns={
                "datetime": "Date",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume",
            }
        )
        return df[["Date", "Open", "High", "Low", "Close", "Volume"]].set_index("Date")

    def get_stock_quote(self, ticker):
        """
        Get the stock quote for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A dictionary containing stock quote data.
        """
       
        quote = self.client.get_quote(ticker.upper()).json()
        first_item = next(iter(quote.items()))[1]
        return first_item

    def get_latest_price(self, ticker):
        """
        Get the latest price for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A float representing the latest price.
        """
        return self.get_stock_quote(ticker)["lastPrice"]

    def get_minute_bars(
        self,
        ticker,
        frequency_window="1m",
        num_bars=None,
        lookback_days=10,
        keep_non_trading_hours=True,
        from_market_open=False,
    ):
        """
        Get minute bars for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :param frequency_window: The frequency window as a string (default "1m").
        :param num_bars: The number of bars to retrieve (default None).
        :param lookback_days: The number of days to look back (default 10).
        :param keep_non_trading_hours: Whether to keep non-trading hours data (default True).
        :param from_market_open: Whether to retrieve data from the market open (default False).
        :return: A DataFrame with minute bars.
        """
        pacific = pytz.timezone("US/Pacific")
        end_date = datetime.datetime.now(pacific)

        if from_market_open:
            now = datetime.datetime.now(pytz.timezone("US/Pacific"))
            if now.weekday() >= 5:
                days_ahead = 7 - now.weekday()
                now = now + datetime.timedelta(days=days_ahead)
            stock_market_open = now.replace(hour=6, minute=30, second=0, microsecond=0)
            start_date = stock_market_open
        else:
            start_date = end_date - datetime.timedelta(lookback_days)

        period_type = self.client.PriceHistory.PeriodType.DAY
        frequency_type = self.client.PriceHistory.FrequencyType.MINUTE

        if frequency_window == "1m":
            frequency = self.client.PriceHistory.Frequency.EVERY_MINUTE
        elif frequency_window == "5m":
            frequency = self.client.PriceHistory.Frequency.EVERY_FIVE_MINUTES
        elif frequency_window == "10m":
            frequency = self.client.PriceHistory.Frequency.EVERY_TEN_MINUTES
        elif frequency_window == "15m":
            frequency = self.client.PriceHistory.Frequency.EVERY_FIFTEEN_MINUTES
        elif frequency_window == "30m":
            frequency = self.client.PriceHistory.Frequency.EVERY_THIRTY_MINUTES
        else:
            raise ValueError("Please select from 1m, 5m, 10m, 15m, 30m")

        history_response = self.client.get_price_history(
            ticker.upper(),
            period_type=period_type,
            frequency_type=frequency_type,
            frequency=frequency,
            start_datetime=start_date,
            end_datetime=end_date,
            need_extended_hours_data=keep_non_trading_hours,
        )

        if history_response.status_code == 200:
            history_data = history_response.json()["candles"]
            df = pd.DataFrame(history_data)
            df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
            df["datetime"] = df["datetime"].dt.tz_localize("UTC").dt.tz_convert(pacific)
            df["datetime"] = df["datetime"].dt.tz_localize(None)
            if num_bars is not None:
                latest_bars = df.tail(num_bars)
            latest_bars = df.rename(
                columns={
                    "datetime": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )
            return latest_bars[["Date", "Open", "High", "Low", "Close", "Volume"]].set_index("Date")
        else:
            print(f"Error retrieving data for {ticker}: {history_response.status_code}")
            return None

    def get_open_price(self, ticker):
        """
        Get the open price for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A float representing the open price.
        """
        return self.get_stock_quote(ticker)["openPrice"]

    def get_stock_fundamental(self, ticker):
        """
        Get the stock fundamental data for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A JSON-formatted string containing fundamental data.
        """
        response = self.client.search_instruments(
            [ticker], self.client.Instrument.Projection.FUNDAMENTAL
        )
        return json.dumps(response.json(), indent=4)

    def get_option_chain(self, ticker):
        """
        Get the option chain for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A JSON-formatted string containing the option chain data.
        """
        response = self.client.get_option_chain(ticker.upper())
        return json.dumps(response.json(), indent=4)

    def get_option_dates(self, ticker):
        """
        Get the option expiration dates for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A list of option expiration dates as strings.
        """
        response = self.client.get_option_chain(
            ticker.upper(), contract_type=self.client.Options.ContractType.ALL
        )
        response.raise_for_status()
        option_data = response.json()
        options_dates = []

        for date_type in ["callExpDateMap", "putExpDateMap"]:
            for date in option_data[date_type]:
                date = date.split(":")[0]
                options_dates.append(date)
        return options_dates

    def get_options_data(
        self, symbol, strike_date, strike_price=None, call_or_put=None, in_or_out=None):
        """
        Get options data for a given symbol and strike date.

        :param symbol: The stock ticker symbol as a string.
        :param strike_date: The strike date as a string in the format "YYYY-MM-DD".
        :param strike_price: The strike price as a float (default None).
        :param call_or_put: The option type as a string, either "call" or "put" (default None).
        :param in_or_out: The option moneyness as a string, either "in" or "out" (default None).
        :return: A DataFrame containing options data.
        """
        expiry_date = datetime.datetime.strptime(strike_date, "%Y-%m-%d").date()
        response = self.client.get_option_chain(
            symbol.upper(),
            strike=strike_price,
            contract_type=self.client.Options.ContractType.ALL,
            from_date=expiry_date,
            to_date=expiry_date)

        response.raise_for_status()
        option_data = response.json()
        options_list = []

        for date_type in ["callExpDateMap", "putExpDateMap"]:
            for date in option_data[date_type]:
                for strike in option_data[date_type][date]:
                    for option in option_data[date_type][date][strike]:
                        if float(strike) == option["strikePrice"]:
                            options_list.append(option)

        result = pd.DataFrame(options_list)
        if call_or_put is None:
            result = result
        elif call_or_put == "call":
            result = result.loc[result["putCall"] == "CALL"]
        elif call_or_put == "put":
            result = result.loc[result["putCall"] == "PUT"]
        else:
            return "please input call or put"

        result = result.loc[result['inTheMoney'] == True] if in_or_out == 'in' else result.loc[result['inTheMoney'] == False] if in_or_out == 'out' else result
        result = result.rename(columns={"strikePrice": "strike", "last": "lastPrice"})
        return result[["strike", "bid", "ask", "lastPrice"]]

class TdaStream:
    def __init__(self, tda_client):
        """
        Initialize the TdaStream class.

        :param tda_client: An instance of the TDAClient class.
        """
        self._client = tda_client
        self._stream_client = StreamClient(self._client, account_id=tda_account_id)

    def order_book_handler(self, msg):
        """
        Handle order book messages.

        :param msg: A message containing order book data.
        """
        print(json.dumps(msg, indent=4))

    async def read_stream(self):
        """
        Read and process messages from the data stream.
        """
        await self._stream_client.login()
        await self._stream_client.quality_of_service(StreamClient.QOSLevel.EXPRESS)
        await self._stream_client.nasdaq_book_subs(['SPY'])

        self._stream_client.add_nasdaq_book_handler(self.order_book_handler)

        while True:
            await self._stream_client.handle_message()

    def start_data_stream(self):
        """
        Start the data stream.
        """
        asyncio.get_event_loop().run_until_complete(self.read_stream())



if __name__ == '__main__':
    client_id = '<YOUR_CLIENT_ID>'
    refresh_token = '<YOUR_REFRESH_TOKEN>'
    account_id = '<YOUR_ACCOUNT_ID>'

    # tda_token_path,
    # tda_api_key,
    # tda_redirect_uri,
    # tda_account_id,
    
    td_client = TDAClient(client_id, refresh_token)

    # Get stock quote for AAPL
    quote = td_client.get_stock_quote('AAPL')
    print("Stock Quote:", quote)

    # Get historical daily bar data for AAPL
    historical_data = td_client.get_historical_daily_bar('AAPL', '2020-01-01', '2021-12-31')
    print("Historical Daily Bar:", historical_data)

    # Get stock fundamental data for AAPL
    fundamental_data = td_client.get_stock_fundamental('AAPL')
    print("Stock Fundamental:", fundamental_data)

    # Get option chain for AAPL
    option_chain = td_client.get_option_chain('AAPL', '2022-06-16', 'call')
    print("Option Chain:", option_chain)

    # Get multiple stock quotes for AAPL, MSFT, and TSLA
    multi_quotes = td_client.get_multiple_stock_quotes(['AAPL', 'MSFT', 'TSLA'])
    print("Multiple Stock Quotes:", multi_quotes)

    # Get account information
    account_info = td_client.get_account_info(account_id)
    print("Account Information:", account_info)

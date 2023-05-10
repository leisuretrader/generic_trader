import yfinance as yf
import pandas as pd

class YFinanceApi:
    def __init__(self):
        """
        Initialize the YFinanceApi class.
        """
        pass

    def get_historical_daily_bar(self, ticker, start_date, end_date):
        """
        Get historical daily bar data for a specific ticker.

        :param ticker: The stock ticker symbol.
        :param start_date: The start date for the data.
        :param end_date: The end date for the data.
        :return: A DataFrame containing historical daily bar data.
        """
        stock = yf.Ticker(ticker.upper())
        df = stock.history(start=start_date, end=end_date)
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        return df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].set_index('Date')

    def yf_data_multi(self, tickers, horizon):
        """
        Get historical data for multiple tickers.

        :param tickers: A list of stock ticker symbols.
        :param horizon: The horizon for the data (e.g., '1y', '1m', '1d').
        :return: A DataFrame containing historical data for multiple tickers.
        """
        data = yf.download(
                tickers = str(tickers).replace("[","").replace("]","").replace("'","").replace(",",""),
                period = horizon,
                interval = "1d",
                group_by = 'ticker',
                auto_adjust = False,
                prepost = True,
                threads = True,
                proxy = None
            )
        data = data.filter(regex='Close',axis=1)
        data = data.droplevel(1, axis=1).copy().dropna()
        data = data.loc[:,~data.columns.duplicated()].copy()
        return data.reset_index()

    def get_stock_quote(self, ticker):
        """
        Get stock quote information for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: A dictionary containing stock quote information.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.info

    def get_latest_price(self, ticker):
        """
        Get the latest price for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: The latest price of the stock.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.info['regularMarketPreviousClose']

    def get_minute_bars(self, ticker, interval='1m', period='7d'):
        """
        Get minute bar data for a specific ticker.

        :param ticker: The stock ticker symbol.
        :param interval: The interval for the data (default is '1m').
        :param period: The period for the data (default is '7d').
        :return: A DataFrame containing minute bar data.
        """
        stock = yf.Ticker(ticker.upper())
        df = stock.history(interval=interval, period=period)
        df.reset_index(inplace=True)
        return df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']].set_index('Datetime')

    def get_open_price(self, ticker):
        """
        Get the opening price for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: The opening price of the stock.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.info['regularMarketOpen']

    def get_stock_fundamental(self, ticker):
        """
        Get fundamental information for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: A dictionary containing stock fundamental information.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.info

    def get_option_chain(self, ticker):
        """
        Get the option chain for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: An option chain object.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.option_chain()

    def get_option_dates(self, ticker):
        """
        Get the option expiration dates for a specific ticker.

        :param ticker: The stock ticker symbol.
        :return: A tuple containing option expiration dates.
        """
        stock = yf.Ticker(ticker.upper())
        return stock.options

    def get_options_data(self, ticker, date, call_or_put=None):
        """
        Get option data for a specific ticker and expiration date.

        :param ticker: The stock ticker symbol.
        :param date: The option expiration date.
        :param call_or_put: The option type ('call' or 'put', optional).
        :return: A DataFrame containing option data.
        """
        stock = yf.Ticker(ticker.upper())
        option_chain = stock.option_chain(date)
        if call_or_put == 'call':
            options_df = option_chain.calls
        elif call_or_put == 'put':
            options_df = option_chain.puts
        else:
            options_df = pd.concat([option_chain.calls, option_chain.puts])
        return options_df[['strike', 'bid', 'ask', 'lastPrice']]
    
if __name__ == '__main__':
    yf_api = YFinanceApi()
    historical_daily_bar = yf_api.get_historical_daily_bar('AAPL', "2020-01-01", "2021-12-31")
    stock_quote = yf_api.get_stock_quote('AAPL')
    latest_price = yf_api.get_latest_price('AAPL')
    minute_bars = yf_api.get_minute_bars('AAPL', interval='1m', period='7d')
    open_price = yf_api.get_open_price('AAPL')
    stock_fundamental = yf_api.get_stock_fundamental('AAPL')
    option_chain = yf_api.get_option_chain('AAPL')
    option_dates = yf_api.get_option_dates('AAPL')
    options_data = yf_api.get_options_data('AAPL', date=option_dates[0], call_or_put='call')

    print("Historical Daily Bar:", historical_daily_bar)
    print("Stock Quote:", stock_quote)
    print("Latest Price:", latest_price)
    print("Minute Bars:", minute_bars)
    print("Open Price:", open_price)
    print("Stock Fundamental:", stock_fundamental)
    print("Option Chain:", option_chain)
    print("Option Dates:", option_dates)
    print("Options Data:", options_data)
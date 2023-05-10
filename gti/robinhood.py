import robin_stocks.robinhood.authentication as ra
import robin_stocks.robinhood.stocks as rs
import robin_stocks.robinhood.options as ro
import robin_stocks.robinhood.markets as rm
import pandas as pd
import pyotp
from broker_config import rob_username, rob_password, rob_pyotp

class RobinhoodStocks:
    def __init__(self):
        totp = pyotp.TOTP(rob_pyotp).now()
        self.login = ra.login(username=rob_username,
                              password=rob_password,
                              store_session=True,
                              mfa_code=totp)

    def stock_info(self, ticker):
        """
        Get stock information for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Stock information as a dictionary.
        """
        return rs.find_instrument_data(ticker)

    def get_fundamental(self, ticker):
        """
        Get fundamental data for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Fundamental data as a dictionary.
        """
        return rs.get_fundamentals(ticker, info=None)

    def get_latest_price(self, ticker):
        """
        Get the latest price of the given stock ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: The latest stock price as a float.
        """
        return float(rs.get_latest_price(ticker)[0])

    def get_open_price(self,ticker):
        """
        Get the opening price of the given stock ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: The opening stock price as a float.
        """
        return float(rs.get_fundamentals(ticker, info='open')[0])

    def get_news(self, ticker):
        """
        Get news articles for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A list of news articles.
        """
        return rs.get_news(ticker)

    def get_quotes(self, ticker):
        """
        Get stock quotes for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Stock quotes as a dictionary.
        """
        return rs.get_quotes(ticker)[0]

    def get_option_dates(self,ticker):
        """
        Get option expiration dates for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: A list of option expiration dates.
        """
        return ro.get_chains(ticker)['expiration_dates']

    def get_robinhood_top100_symbols(self):
        """
        Get the top 100 symbols on Robinhood.

        :return: A list of the top 100 symbols.
        """
        r = rm.get_top_100(info='symbol')
        return [i.lower() for i in r]

    def get_earnings(self, ticker):
        """
        Get earnings data for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Earnings data as a DataFrame.
        """
        earnings_json = rs.get_earnings(ticker, info=None)
        if len(earnings_json) == 0:
            raise Exception("No Data Available")
        else:
            final = []
            for i in earnings_json:
                r = {}
                r['year'] = i['year']
                r['quarter'] = i['quarter']
                r['date'] = i['report']['date']
                r['actual_eps'] = i['eps']['actual']
                r['estimate_eps'] = i['eps']['estimate']
            final.append(r)

        df = pd.DataFrame(final).dropna()
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['actual_eps'] = df['actual_eps'].astype(float)
        df['estimate_eps'] = df['estimate_eps'].astype(float)
        df['annual_eps'] = df['actual_eps'].rolling(4).sum()
        return df

    def get_eps(self, ticker):
        """
        Get earnings per share (EPS) for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: The EPS as a float.
        """
        latest = self.get_earnings(ticker).tail(4)['actual_eps'].to_list()
        result = sum(latest)
        return result

    def get_daily_close(self, 
                        ticker, 
                        interval='day', 
                        span='5year', 
                        bounds='regular', 
                        info=None):
        """
        Get daily closing prices for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Daily closing prices as a DataFrame.
        """
        daily = rs.get_stock_historicals(ticker,
                                        interval=interval,
                                        span=span,
                                        bounds=bounds,
                                        info=info)
        df = pd.DataFrame(daily)[['begins_at', 'close_price']]
        df = df.rename(columns={'begins_at': 'date', 'close_price': 'close'})
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['close'] = df['close'].astype(float)
        return df

    def get_pe_history(self, ticker, avg_window=90):
        """
        Get P/E history for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :param avg_window: The rolling window size for average calculation.
        :return: P/E history as a DataFrame.
        """
        eps = self.get_earnings(ticker).drop(['year', 'quarter'], axis=1)
        daily_close = self.get_daily_close(ticker)
        daily_close['close_avg'] = daily_close['close'].rolling(avg_window).mean()
        latest_daily = daily_close.tail(1)
        result = pd.merge(left=eps,
                        right=daily_close,
                        how='left',
                        on='date')
        add_latest = pd.concat([result, latest_daily], ignore_index=True).fillna(method='ffill')
        add_latest['pe'] = add_latest['close'] / add_latest['annual_eps']
        add_latest['pe_close_avg'] = add_latest['close_avg'] / add_latest['annual_eps']
        r = add_latest.dropna().copy()
        r['pe_pct_change'] = r['pe'].pct_change()
        return r

    def get_pe_rolling(self, ticker):
        """
        Get rolling P/E for a given ticker.

        :param ticker: The stock ticker symbol as a string.
        :return: Rolling P/E as a DataFrame.
        """
        eps = self.get_earnings(ticker)
        daily_close = self.get_daily_close(ticker)
        result = pd.merge(left=daily_close,
                        right=eps,
                        how='left',
                        on='date').fillna(method='ffill')
        result['pe_ratio'] = result['close'] / result['annual_eps']
        return result.dropna()


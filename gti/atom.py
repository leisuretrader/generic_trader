from td_ameritrade import TDAClient
from yahoo import YFinanceApi
from robinhood import RobinhoodStocks

tda = TDAClient()
rob = RobinhoodStocks()
yf = YFinanceApi()

def get_multi_historical_daily_bars(tickers, horizon, source='yf'):
    if source == 'yf':
        return yf.yf_data_multi(tickers, horizon)
    else:
        raise NotImplementedError("This data source is not supported.")

def get_latest_price(ticker,source='td'):
    if source == 'td':
        return tda.get_latest_price(ticker)
    if source =='rob':
        return rob.get_latest_price(ticker)
    if source == 'yf':
        return yf.get_latest_price(ticker)

def get_open_price(ticker,source='td'):
    if source == 'td':
        return tda.get_open_price(ticker)
    if source =='rob':
        return rob.get_open_price(ticker)
    if source == 'yf':
        return yf.get_open_price(ticker)

def get_historical_daily_bars(ticker, start_date,end_date, source='td'):
    if source == 'td':
        return tda.get_historical_daily_bar(ticker, start_date, end_date)
    if source =='rob':  #still trying to workout
        pass
    if source == 'yf':
        return yf.get_historical_daily_bar(ticker,start_date,end_date)
# print(get_historical_daily_bars('spy','2021-01-01','2023-04-22',source='yf'))
def get_minute_bars(ticker, frequency_window="1m", num_bars=None, lookback_days=5, keep_non_trading_hours=True, from_market_open=False, source='td'):
    if source == 'td':
        return tda.get_minute_bars(ticker, frequency_window=frequency_window, num_bars=num_bars, lookback_days=lookback_days, keep_non_trading_hours=keep_non_trading_hours, from_market_open=from_market_open)
    else:
        raise NotImplementedError("This data source is not supported.")

def get_option_dates(ticker,source='td'): # returns list
    if source == 'td':
        return tda.get_option_dates(ticker)
    if source =='rob':
        return rob.get_option_dates(ticker)
    if source == 'yf':
        return yf.get_option_dates(ticker)
# print (get_option_dates('spy',source='td'))

def get_option_chain(ticker, expiry_date, call_or_put=None, in_or_out=None, source='td'):
    if source == 'td':
        return tda.get_options_data(ticker, expiry_date, call_or_put=call_or_put, in_or_out=in_or_out)
    elif source == 'rob' or source == 'yfinance':
        raise NotImplementedError("This data source is not supported.")
# print(get_option_chain('spy','2023-05-05',source='td'))

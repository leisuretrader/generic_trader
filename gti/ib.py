from ib_insync import *
import pandas as pd

class InteractiveBrokersClient:

    def __init__(self, ip='127.0.0.1', port=7496, client_id=1):
        util.startLoop()
        self.ib = IB()
        self.ib.connect(ip, port, clientId=client_id)

    def get_stock_contract(self, symbol):
        return Stock(symbol, 'SMART', 'USD')

    def get_historical_data(self, contract, duration_str, bar_size_setting, end_date_time='', what_to_show='TRADES', use_rth=True, format_date=1):
        bars = self.ib.reqHistoricalData(contract, endDateTime=end_date_time, durationStr=duration_str, barSizeSetting=bar_size_setting, whatToShow=what_to_show, useRTH=use_rth, formatDate=format_date)
        df = util.df(bars)
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        return df

    def get_stock_quote(self, symbol):
        contract = self.get_stock_contract(symbol)
        ticker = self.ib.reqMktData(contract)
        return ticker

    def get_historical_daily_bar(self, symbol, start_date, end_date):
        contract = self.get_stock_contract(symbol)
        duration_str = f"{(end_date - start_date).days} D"
        return self.get_historical_data(contract, duration_str, '1 day')

if __name__ == '__main__':
    ib_client = InteractiveBrokersClient()

    # Get stock quote for AAPL
    quote = ib_client.get_stock_quote('AAPL')
    print("Stock Quote:", quote)

    # Get historical daily bar data for AAPL
    start_date = date(2020, 1, 1)
    end_date = date(2021, 12, 31)
    historical_daily_bar = ib_client.get_historical_daily_bar('AAPL', start_date, end_date)
    print("Historical Daily Bar:", historical_daily_bar.tail(10))

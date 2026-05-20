# ibapi
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

import threading
from time import sleep
from threading import Thread
import pandas as pd

class TradeApp(EWrapper, EClient):
    '''
    EWrapper: EWrapper class is used to receive all messages/responses/events from TWS (accountSummary(), position(), etc.)
    EClient: EClient class is used to send requests to TWS. This class contains all the methods to communicate with TWS (reqPositions, placeOrder, etc.)
    '''
    def __init__(self):
        EClient.__init__(self, self)

        # account data
        self.gross_position_value = None
        self.net_liquidation_value = None
        self.cash_balance = None
        self.acc_done_event = threading.Event()

        # portfolio data
        self.positions_data = []
        self.portfolio_positions = {} # tickers as keys and quantity of stocks as values
        self.pos_done_event = threading.Event()

        # market data
        self.reqIDtoTicker = {} # mapping the reqID to ticker
        self.marketdata = {} # tickers as keys and the values are the price bars
        self.last_1min_price_data = {} # tickers as keys and the values are the last price bar

        # tracking which historical requests i expect and which are done
        self.hist_expected = set()
        self.hist_done = set()
        self.hist_done_event = threading.Event() # waits until all requests expected are done

        # target portfolio
        self.selected_stocks = [] # selected stocks are the "desired universe" from my factor model (top longs)
        self.target_shares = {} # target shares stores the trade deltas in shares (negative to reduce the weight, positive to increase the weight)

        # orders
        self.limit_prices = {} # limit_prices[ticker] = {'buy_limit': x, 'sell_limit': y}
        self.order_status = {} #stores the latest known status of every order placed
        self.order_event = threading.Event() # starts unset and is only set once all orders are finished
        self.active_orders = set() #contains the orderIds that are not finished yet (by finished i mean: filled, submitted or cancelled)

    # Order ID management
    def get_next_valid_id(self):
        '''
        Simple local incrementer for order IDs. IB sends the valid ID with nextValidId() and then each time get_next_valid_id()
        is called it returns the next valid ID.
        '''
        valid_order_id = self.next_order_id
        self.next_order_id += 1
        return valid_order_id
    
    def nextValidId(self, orderId):
        '''
        IB calls this once after connection. This is the starting point for orderIds that are allowed to use.
        '''
        self.next_order_id = orderId
    
    # Error handling
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        """
        IB sends a bunch of informational messages via error(). error() will hide the noisy ones, but keep everything else.
        """
        # 2176: harmless fractional-size rules warning
        # 2104/2106/2158: data farm connection OK status messages
        if errorCode in (2176, 2104, 2106, 2158):
            return
        print(f"[IB ERROR] reqId={reqId} code={errorCode} msg={errorString}")

    # Account Summary Callbacks
    def accountSummary(self, reqId: int, account: str, tag: str, value: str,currency: str):
        if currency == 'USD':
            if tag == 'GrossPositionValue':
                self.gross_position_value = float(value)
            elif tag == 'NetLiquidation':
                self.net_liquidation_value = float(value)
            elif tag == 'TotalCashValue':
                self.cash_balance = float(value)
    
    def accountSummaryEnd(self, reqId: int): #signals that accountSummary is done
        self.acc_done_event.set()

    # Positions callbacks
    def position(self, account, contract, position, avgCost): # called once per position
        self.positions_data.append({
            # contract fields
            "symbol": contract.symbol,
            "secType": contract.secType,
            "currency": contract.currency,
            "exchange": contract.exchange,
            "quantity": float(position)})
        
        #self.portfolio_positions[contract.symbol] = float(position)
        if position != 0:
            self.portfolio_positions[contract.symbol] = float(position)
    
    def positionEnd(self): #signals that position is done
        self.pos_done_event.set()
    
    # Historical Data callbacks
    def historicalData(self, reqId, bar):
        # reqId is your ticker_id
        ticker = self.reqIDtoTicker[reqId]
        self.marketdata.setdefault(ticker, []).append(bar)
    
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        self.hist_done.add(reqId)
        if self.hist_done == self.hist_expected:
            self.hist_done_event.set()
    
    def get_last_prices(self, selected_stocks, portfolio_positions={}):
        '''
        selected_stocks should be a list with tickers, portfolio_positions should be a dictionary with keys as tickers
        '''
        # extracts symbols from portfolio positions
        held_symbols = list(portfolio_positions.keys())

        # creates universe; sets are used to avoid
        univ = sorted(set(held_symbols) | set(selected_stocks)) # combines both sets with | and then sorted() for stable ordering

        # Reset state
        self.reqIDtoTicker.clear()
        self.marketdata.clear()
        self.last_1min_price_data.clear()

        self.hist_expected.clear()
        self.hist_done.clear()
        self.hist_done_event.clear()

        # REQUESTING MARKET DATA for univ
        req_id = 0
        for symbol in univ:
            req_id += 1

            self.hist_expected.add(req_id)
            self.reqIDtoTicker[req_id] = symbol

            contract = Contract()
            contract.symbol = symbol
            contract.exchange = 'SMART'
            contract.currency = 'USD'
            contract.secType = 'STK'
            self.reqHistoricalData(req_id, contract, "", "1 D", "1 min", "TRADES", 1, 1, False, []) #endDateTime is now, duration 1 D and bar size 1 min

        ok = self.hist_done_event.wait(timeout=30)
        if not ok:
            print("Timed out waiting for historical data.")

        for symbol, bars in self.marketdata.items():
            if bars: #ensure at least 1 bar
                self.last_1min_price_data[symbol] = bars[-1].close
            else:
                print(f'No bars returned for {symbol}')

        return dict(self.last_1min_price_data)

    # Portfolio math
    def compute_equalw_target_shares(self, selected_stocks, net_liq_value, cash_buffer=.02):
        '''
        selected_stocks should be a list with tickers, net_liq_value should be a number
        '''
        alloc = float(net_liq_value) * (1 - cash_buffer)# cash cushion
        money_pos = alloc / len(selected_stocks)
        for stock in selected_stocks:
            current_shares = self.portfolio_positions.get(stock, 0) #if stock exists in portfolio_position get the value, else 0
            last_1min_price = self.last_1min_price_data[stock]
            target_shares = (money_pos / last_1min_price) - current_shares
            self.target_shares[stock] = round(target_shares)
    
    def compute_limit_prices(self, selected_stocks, portfolio_positions, last_prices, epsilon=.0035):
        '''
        selected_stocks should be a list with tickers, portfolio_positions should be a dictionary with keys as tickers and last_prices 
        should be a dictionary with keys as tickers and values as the price
        '''
        # extracts symbols from portfolio positions
        held_symbols = list(portfolio_positions.keys())

        # creates universe; sets are used to avoid
        univ = sorted(set(held_symbols) | set(selected_stocks)) # combines both sets with | and then sorted() for stable ordering

        # for selected stocks
        for symbol in univ:
            last_price = last_prices[symbol]
            buy_limit = round(last_price * (1 + epsilon), 2)
            sell_limit = round(last_price * (1 - epsilon), 2)
            self.limit_prices[symbol] = {'buy_limit': buy_limit, 'sell_limit': sell_limit}

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        self.order_status[orderId] = status #updates the latest know status to the specific orderId

        print(f"[orderStatus] orderId={orderId} status={status} filled={filled} remaining={remaining}")

        if status in ("Filled", "Cancelled", "Inactive", 'ApiCancelled', 'Rejected'): # these status are terminal
            self.active_orders.discard(orderId) # once the status is terminal the orderId is removed from active orders

        if len(self.active_orders) == 0: #when the last order is finished the event is triggered
            self.order_event.set() # the code waiting on .wait() is released
    
    # Placing orders
    def liquidate_positions_not_in(self, selected_stocks, portfolio_positions, limit_prices, timeout=300):
        '''
        selected_stocks should be a list with tickers, portfolio_positions should be a dictionary with keys as tickers and values as the
        target shares and limit_prices should be a dictionary with keys as tickers and values as a dictionary with with keys 'buy_limit' and
        'sell_limit' and the values as those values.
        '''
        selected_set = set(selected_stocks)

        # reset order tracking state
        self.active_orders.clear()
        self.order_event.clear()

        order_ids = []
        #create orders for position (in this case we are closing the positions for the tickers that arent in selected stocks)
        for symbol, quantity in portfolio_positions.items():

            if quantity == 0:
                continue

            if symbol in selected_set: # if symbol is in selected set, then the rebalancing will be made with target shares
                continue

            # guard in case there are no prices for the symbol
            if symbol not in limit_prices:
                print(f'No limit prices data for {symbol}')
                continue
            
            order_id = self.get_next_valid_id()
            order_ids.append(order_id)

            c = Contract()
            c.symbol = symbol
            c.exchange = 'SMART'
            c.currency = 'USD'
            c.secType = 'STK'

            o = Order()
            o.action = "SELL"
            o.orderType = 'LMT'
            o.totalQuantity = quantity
            o.lmtPrice = limit_prices[symbol]['sell_limit']
            o.eTradeOnly = False
            o.firmQuoteOnly = False

            self.active_orders.add(order_id) #the orderId is added to self.active_orders
            print(f'Placing order for {symbol} with orderId {order_id}') #to see the progress in the terminal
            self.placeOrder(order_id, c, o) # order placed

        # if nothing to sell
        if len(self.active_orders) == 0:
            self.order_event.set()
            ok = True
            return order_ids, ok
        
        # waiting until all orders above are complete before continuing with the next part of the code
        ok = self.order_event.wait(timeout=timeout)
        if not ok:
            print("Liquidation orders did not finish before timeout.")

        return order_ids, ok
    
    def place_orders_for(self, selected_stocks, target_shares, limit_prices): 
        '''
        selected_stocks should be a list with tickers, target_shares should be a dictionary with keys as tickers and values as the
        target shares and limit_prices should be a dictionary with keys as tickers and values as a dictionary with with keys 'buy_limit' and
        'sell_limit' and the values as those values.
        '''
        # CREATE ORDERS FOR SELECTED STOCKS
        order_ids = []
        for stock in selected_stocks:
            # guard to ensure stock exists target_shares and limit_prices
            if stock not in target_shares:
                print(f'Missing target shares for {stock}')
                continue
            if stock not in limit_prices:
                print(f'Missing limit prices for {stock}')
                continue

            delta = target_shares[stock] #target_shares are the trade sizes not the final holdings

            # no trade needed (but I should later code it so if the delta represents a small change in the weight of the position, to just continue)
            if delta == 0:
                continue

            order_id = self.get_next_valid_id()
            order_ids.append(order_id)

            c = Contract()
            c.symbol = stock
            c.exchange = 'SMART'
            c.currency = 'USD'
            c.secType = 'STK'

            o = Order()
            o.orderType = 'LMT'
            o.eTradeOnly = False
            o.firmQuoteOnly = False

            if target_shares[stock] > 0:
                o.action = "BUY"
                o.totalQuantity = target_shares[stock]
                o.lmtPrice = limit_prices[stock]['buy_limit']

            elif target_shares[stock] < 0:
                o.action = "SELL"
                o.totalQuantity = (target_shares[stock] * -1) # target shares negative means reducing the position, but has to be positive for o.totalQuantity
                o.lmtPrice = limit_prices[stock]['sell_limit']

            print(f'Placing order for {stock} with orderId {order_id}') #to see the progress in the terminal
            self.placeOrder(order_id, c, o)

        return order_ids
        
if __name__ == '__main__':

    #connection parameters
    host = '127.0.0.1'
    port = 7497 #7496 or 7497
    client_id = 1

    #initializing client connection to TWS
    trade_app = TradeApp()

    #connecting to tws
    trade_app.connect(host, port, client_id)
    sleep(1)

    #running client in a separate thread
    app_thread = Thread(target=trade_app.run, daemon=True)
    app_thread.start()

    # SELECTED STOCKS FROM MODEL
    # loading database
    selected_stocks = pd.read_csv( r"C:\Users\Ramon\Desktop\data laptop\QUANT PROJECTS\model_stocks_selected.csv")['Instrument'].tolist()
    # passing list of stocks
    trade_app.selected_stocks = selected_stocks

    # REQUESTING POSITIONS
    trade_app.reqPositions()
    
    ok = trade_app.pos_done_event.wait(timeout=10)
    if not ok:
        raise TimeoutError('Timed out waiting for account summary')
    
    print('----\n')
    print(f'Positions {trade_app.portfolio_positions}')
    print('----\n')
    
    # REQUESTING MARKET DATA and getting last prices
    trade_app.get_last_prices(trade_app.selected_stocks, trade_app.portfolio_positions)

    print(f'Last price data {trade_app.last_1min_price_data}')
    print('----\n')

    # COMPUTE LIMIT PRICES
    trade_app.compute_limit_prices(trade_app.selected_stocks, trade_app.portfolio_positions, trade_app.last_1min_price_data)
    print(f'Limit prices {trade_app.limit_prices}')
    print('----\n')

    # LIQUIDITING POSITIONS THAT AREN'T IN SELECTED STOCKS
    oid_of_lp, ok = trade_app.liquidate_positions_not_in(trade_app.selected_stocks, trade_app.portfolio_positions, trade_app.limit_prices)
    if not ok:
        raise RuntimeError("Liquidation did not finish before timeout; aborting sizing.")
    print(f'Order Ids of Liquidating Positions {oid_of_lp}')
    print('----\n')
    
    # REQUESTING ACCOUNT DATA SUMMARY
    tags = ",".join(["NetLiquidation", "TotalCashValue","GrossPositionValue",]) #takes the list and concatenates them into a single string with "," in between
    trade_app.reqAccountSummary(9001, 'All', tags) #this function expects tags to be a single string separated by commas
    
    ok = trade_app.acc_done_event.wait(timeout=10)
    if not ok:
        raise TimeoutError('Timed out waiting for account summary') 
    
    print('----\n')
    print(f'Net Liquidation Value: {trade_app.net_liquidation_value}')
    print(f'Gross Value: {trade_app.gross_position_value}')
    print(f'Total Cash: {trade_app.cash_balance}')
    print('----\n')

    # COMPUTE TARGET SHARES
    trade_app.compute_equalw_target_shares(trade_app.selected_stocks, trade_app.net_liquidation_value)
    print(f'Target shares: {trade_app.target_shares}')
    print('----\n')
    
    # CREATE ORDERS FOR SELECTED STOCKS
    oid_of_ss = trade_app.place_orders_for(trade_app.selected_stocks, trade_app.target_shares, trade_app.limit_prices)
    print(f'Order Ids of Selected Stocks {oid_of_ss}')
    print('----\n')

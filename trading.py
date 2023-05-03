# from binance.enums import KLINE_INTERVAL_1MINUTE
import decimal
from datetime import datetime, timedelta
from binance import Client, AsyncClient, BinanceSocketManager  # noqa
# from binance.depthcache import DepthCacheManager, OptionsDepthCacheManager, ThreadedDepthCacheManager  # noqa
from main import *


def get_wallet_value_from_2am(client: Client):
    account_info = client.get_account()
    balances = account_info['balances']
    # Get wallet balance at 2AM today
    now = datetime.utcnow()
    today = datetime(now.year, now.month, now.day)
    timestamp_2am = int((today + timedelta(hours=2)).timestamp() * 1000)
    klines = client.get_historical_klines('BTCUSDT', Client.KLINE_INTERVAL_1HOUR, f"{timestamp_2am}ms",
                                          f"{timestamp_2am + 1}ms")
    close_price_2am = float(klines[0][4])
    btc_balance_2am = float(next((b['free'] for b in balances if b['asset'] == 'BTC'), 0)) + float(
        next((b['locked'] for b in balances if b['asset'] == 'BTC'), 0))
    wallet_value_2am = btc_balance_2am * close_price_2am
    return wallet_value_2am


def get_wallet_value_difference(client, wallet_value_2am):
    # Get current wallet balance
    account_info = client.get_account()
    balances = account_info['balances']
    wallet_value_now = sum(float(b['free']) + float(b['locked']) for b in balances)
    # Calculate difference and return result
    difference = wallet_value_now - wallet_value_2am
    return difference


def close_all_positions(client):
    # get all open orders
    orders = client.futures_get_all_orders()

    # loop through all orders and close them
    for order in orders:
        if order['side'] == 'BUY':
            # if the order is a buy order, create a corresponding sell order with the same quantity
            symbol = order['symbol']
            quantity = order['origQty']
            client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )
        elif order['side'] == 'SELL':
            # if the order is a sell order, skip it
            continue


async def trading_loop(client):
    bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    ts = bm.symbol_ticker_futures_socket('BTCUSDT')
    # then start receiving messages
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            price = res['data']['b']
            print(price)
            if float(price) < 27150.0:
                client.futures_create_order(
                    symbol='BTCUSDT',
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=0.001
                )
                print("doing transaction")
                break

    await client.close_connection()

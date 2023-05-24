# from binance_bot.enums import KLINE_INTERVAL_1MINUTE
import asyncio
from binance import Client, AsyncClient, BinanceSocketManager  # noqa
# from binance_bot.depthcache import DepthCacheManager, OptionsDepthCacheManager, ThreadedDepthCacheManager  # noqa
from datetime import datetime, timedelta


with open('../keys.txt', 'r') as file:
    # Read the entire contents of the file into a variable
    file_contents = file.read()
    keys = file_contents.split('\n')


# Set up the Binance API client
api_key = keys[2]
api_secret = keys[3]


# get market depth
# depth = client.get_order_book(symbol='BNBBTC')

# place a test market buy order, to place an actual order use the create_order function
# order = client.create_test_order(
#    symbol='BNBBTC',
#    side=Client.SIDE_BUY,
#    type=Client.ORDER_TYPE_MARKET,
#    quantity=100)

# get all symbol prices
# prices = client.get_all_tickers()

# withdraw 100 ETH
# check docs for assumptions around withdrawals
# from binance_bot.exceptions import BinanceAPIException

# try:
#    result = client.withdraw(
#        asset='ETH',
#        address='<eth_address>',
#        amount=100)
# except BinanceAPIException as e:
#    print(e)
# else:
#    print("Success")

# fetch list of withdrawals
# withdraws = client.get_withdraw_history()

# fetch list of ETH withdrawals
# eth_withdraws = client.get_withdraw_history(coin='ETH')

# get a deposit address for BTC
# address = client.get_deposit_address(coin='BTC')

async def get_whole_pnl(client):
    position_info = client.futures_position_information()
    total_pnl = 0.0

    for position in position_info:
        pnl = float(position['unRealizedProfit'])
        total_pnl += pnl

    return total_pnl


async def get_futures_balance_at_2am(client):
    # Calculate the timestamp for 2am today
    current_time = datetime.now()
    today_2am = datetime(current_time.year, current_time.month, current_time.day, 2, 0, 0)
    if current_time < today_2am:
        # If the current time is before 2am, subtract one day to get the previous day's 2am
        yesterday_2am = today_2am - timedelta(days=1)
        timestamp_2am = int(yesterday_2am.timestamp() * 1000)
    else:
        timestamp_2am = int(today_2am.timestamp() * 1000)

    # Get the account information at 2am
    account_info = client.futures_account_balance(timestamp=timestamp_2am)

    # Calculate the sum of asset balances in USDT
    total_balance_usdt = 0.0
    for asset in account_info:
        if 'balance' in asset and float(asset['balance']) > 0:
            # Get the balance at 2am for the specified asset
            asset_balance = float(asset['balance'])
            # Convert balance to USDT
            if asset['asset'] != 'USDT':
                usdt_ticker = asset['asset']
                usdt_price = client.get_avg_price(symbol=usdt_ticker)['price']
                asset_balance *= float(usdt_price)
            total_balance_usdt += asset_balance

    # Add the PNL from all positions to the total balance
    positions = client.futures_position_information()
    for position in positions:
        if float(position['positionAmt']) != 0.0:
            symbol = position['symbol']
            pnl = float(position['unRealizedProfit'])
            if symbol != 'USDT':
                usdt_ticker = symbol
                usdt_price = client.get_avg_price(symbol=usdt_ticker)['price']
                pnl *= float(usdt_price)
            total_balance_usdt += pnl

    return total_balance_usdt


async def get_current_futures_balance(client):
    # Get the account information
    account_info = client.futures_account()

    # Calculate the sum of asset balances in USDT
    total_balance_usdt = 0.0
    for asset in account_info['assets']:
        if float(asset['marginBalance']) > 0:
            # Get the current balance for the specified asset
            asset_balance = float(asset['marginBalance'])
            # Convert balance to USDT
            if asset['asset'] != 'USDT':
                usdt_ticker = asset['asset'] + 'USDT'
                usdt_price = client.get_avg_price(symbol=usdt_ticker)['price']
                asset_balance *= float(usdt_price)
            total_balance_usdt += asset_balance

    # Add the PNL of open orders to the total balance
    total_balance_usdt += await get_whole_pnl(client)

    return total_balance_usdt


async def get_wallet_value_difference(wallet_value_2am, client):
    return get_current_futures_balance(client) - wallet_value_2am


async def cancel_all_orders(client):
    # Get all open orders
    open_orders = client.futures_get_open_orders()

    # Cancel each open order
    for order in open_orders:
        symbol = order['symbol']
        order_id = order['orderId']
        client.futures_cancel_order(symbol=symbol, orderId=order_id)
        print(f"Canceled order: {symbol} - Order ID: {order_id}")


async def close_all_positions(client):
    # Get open positions
    open_positions = client.futures_position_information()

    # Close each open position
    for position in open_positions:
        symbol = position['symbol']
        quantity = float(position['positionAmt'])
        if quantity > 0:
            # Close long position
            client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=abs(quantity)
            )
        # elif quantity < 0:
        #     # Close short position
        #     client.futures_create_order(
        #         symbol=symbol,
        #         side=Client.SIDE_BUY,
        #         type=Client.ORDER_TYPE_MARKET,
        #         quantity=abs(quantity)
        #     )

    print("All open positions have been closed.")


async def main():
    client = Client(api_key=api_key, api_secret=api_secret)
    wallet_value_2am = await get_futures_balance_at_2am(client)
    print("Balance at 2AM: ", wallet_value_2am)
    print("Balance now: ", await get_current_futures_balance(client))
    await cancel_all_orders(client)
    await close_all_positions(client)
    # bm = BinanceSocketManager(client)
    # # start any sockets here, i.e a trade socket
    # ts = bm.symbol_ticker_futures_socket('BTCUSDT')
    # # then start receiving messages
    # async with ts as tscm:
    #     while True:
    #         res = await tscm.recv()
    #         price = res['data']['b']
    #         print(price)
    #         if float(price) < 27150.0:
    #             await client.futures_create_order(
    #                 symbol='BTCUSDT',
    #                 side=Client.SIDE_SELL,
    #                 type=Client.ORDER_TYPE_MARKET,
    #                 quantity=0.001
    #             )
    #             print("doing transaction")
    #             break

    # await client.close_connection()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

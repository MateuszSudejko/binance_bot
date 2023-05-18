# from binance_bot.enums import KLINE_INTERVAL_1MINUTE
from binance import Client, AsyncClient, BinanceSocketManager  # noqa
# from binance_bot.depthcache import DepthCacheManager, OptionsDepthCacheManager, ThreadedDepthCacheManager  # noqa
import asyncio
from datetime import datetime, timedelta


with open('../keys.txt', 'r') as file:
    # Read the entire contents of the file into a variable
    file_contents = file.read()
    keys = file_contents.split('\n')


# Set up the Binance API client
api_key = keys[2]
api_secret = keys[3]
client = AsyncClient(api_key=api_key, api_secret=api_secret)


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


def get_futures_balance_at_2am(api_key: str, api_secret: str):
    # Create a Binance API client
    client = Client(api_key=api_key, api_secret=api_secret)

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
    for asset in account_info['balances']:
        if float(asset['balance']) > 0:
            # Get the balance at 2am for the specified asset
            asset_balance = float(asset['balance'])
            # Convert balance to USDT
            if asset['asset'] != 'USDT':
                usdt_ticker = asset['asset'] + 'USDT'
                usdt_price = client.get_avg_price(symbol=usdt_ticker)['price']
                asset_balance *= float(usdt_price)
            total_balance_usdt += asset_balance

    # Add the PNL of open orders to the total balance
    open_orders = client.futures_get_open_orders()
    for order in open_orders:
        if order['side'] == 'BUY':
            pnl = float(order['realizedProfit']) + float(order['unrealizedProfit'])
        else:  # order['side'] == 'SELL'
            pnl = -float(order['realizedProfit']) + float(order['unrealizedProfit'])
        total_balance_usdt += pnl

    return total_balance_usdt


def get_current_futures_balance(api_key: str, api_secret: str):
    # Create a Binance API client
    client = Client(api_key=api_key, api_secret=api_secret)

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
    open_orders = client.futures_get_open_orders()
    for order in open_orders:
        if order['side'] == 'BUY':
            pnl = float(order['realizedProfit']) + float(order['unrealizedProfit'])
        else:  # order['side'] == 'SELL'
            pnl = -float(order['realizedProfit']) + float(order['unrealizedProfit'])
        total_balance_usdt += pnl

    return total_balance_usdt


def get_wallet_value_difference(wallet_value_2am):
    return get_current_futures_balance(api_key, api_secret) - wallet_value_2am


def close_all_positions(api_key: str, api_secret: str, symbol: str):
    # Create a Binance API client
    client = Client(api_key=api_key, api_secret=api_secret)

    # Get open positions for the specified symbol
    open_positions = client.futures_position_information(symbol=symbol)

    # Close each open position
    for position in open_positions:
        quantity = float(position['positionAmt'])
        if quantity > 0:
            # Close long position
            client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=abs(quantity)
            )
        elif quantity < 0:
            # Close short position
            client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=abs(quantity)
            )

    print("All open positions have been closed.")


wallet_value_2am = get_futures_balance_at_2am(api_key, api_secret)


async def main():
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
                await client.futures_create_order(
                    symbol='BTCUSDT',
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=0.001
                )
                print("doing transaction")
                break

    await client.close_connection()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

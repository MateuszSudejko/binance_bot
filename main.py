import asyncio
import json
from binance import AsyncClient, DepthCacheManager, BinanceSocketManager, OptionsDepthCacheManager
from binance import ThreadedWebsocketManager, ThreadedDepthCacheManager
from trading import *
from binance import Client
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


with open('keys.txt', 'r') as file:
    # Read the entire contents of the file into a variable
    file_contents = file.read()
    keys = file_contents.split('\n')

# Set up telegram bot api client
TOKEN: Final = keys[0]
BOT_USERNAME: Final = keys[1]
app = Application.builder().token(TOKEN).build()
user_name = keys[4]

# Set up the Binance API client
api_key = keys[2]
api_secret = keys[3]
client = Client(api_key=api_key, api_secret=api_secret)
#wallet_value_2am = get_wallet_value_from_2am(client)

# get market depth
#depth = client.get_order_book(symbol='BNBBTC')

# place a test market buy order, to place an actual order use the create_order function
#order = client.create_test_order(
#    symbol='BNBBTC',
#    side=Client.SIDE_BUY,
#    type=Client.ORDER_TYPE_MARKET,
#    quantity=100)

# get all symbol prices
#prices = client.get_all_tickers()

# withdraw 100 ETH
# check docs for assumptions around withdrawals
#from binance.exceptions import BinanceAPIException

#try:
#    result = client.withdraw(
#        asset='ETH',
#        address='<eth_address>',
#        amount=100)
#except BinanceAPIException as e:
#    print(e)
#else:
#    print("Success")

# fetch list of withdrawals
#withdraws = client.get_withdraw_history()

# fetch list of ETH withdrawals
#eth_withdraws = client.get_withdraw_history(coin='ETH')

# get a deposit address for BTC
#address = client.get_deposit_address(coin='BTC')


def handle_socket_message(msg):
    print(f"message type: {msg['e']}")
    print(msg)


async def send_update_on_difference():
    # Get the chat ID of the user/group to send the message to
    chat_id = user_name
    # Send the message
    app.bot.send_message(chat_id=chat_id, text='Trading criterion triggered')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, here is your account update')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I can give no help')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Custom command')


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'You have earned/lost {get_wallet_value_difference(client, 0)}')


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'hello'

    return 'I do not have answer to that'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: handle_response(text)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} cause error {context.error}')


async def main():
    # initialise the client
    client = await AsyncClient.create()

    # initialise websocket factory manager
    bsm = BinanceSocketManager(client)

    # create listener using async with
    # this will exit and close the connection after 5 messages
    async with bsm.trade_socket('BTCUSDT') as ts:
        for _ in range(5):
            res = await ts.recv()
            print(f'recv {res}')

    await client.close_connection()


if __name__ == "__main__":
    print('Bot starting...')
    # Set up the command and message handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('result', result_command))
    app.add_handler(MessageHandler(filters.Text, handle_message))
    app.add_error_handler(error)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

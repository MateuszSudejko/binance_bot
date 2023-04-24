from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from trading import *
import asyncio
# from binance.enums import KLINE_INTERVAL_1MINUTE
from datetime import datetime, timedelta
from binance import Client, AsyncClient, BinanceSocketManager  # noqa
# from binance.depthcache import DepthCacheManager, OptionsDepthCacheManager, ThreadedDepthCacheManager  # noqa

# Set up the Binance API client
api_key = ""
api_secret = ""
sync_client = Client(api_key=api_key, api_secret=api_secret)

# Set up telegram bot api client
TOKEN: Final = ''
BOT_USERNAME: Final = ''


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, here is your account update')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I can give no help')


async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Custom command')


async def result_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'You have earned/lost {get_wallet_value_difference(sync_client)}')


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
    print('Should I start trading? (Y/n)')
    if input() == 'Y':
        await trading_loop()


if __name__ == '__main__':
    print('Starting bot...')
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('result', result_command))

    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    app.add_error_handler(error)

    print('Polling...')

    asyncio.run(main())

    app.run_polling(poll_interval=1)


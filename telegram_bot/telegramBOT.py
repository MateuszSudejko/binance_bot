from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import time


with open('../keys.txt', 'r') as file:
    # Read the entire contents of the file into a variable
    file_contents = file.read()
    keys = file_contents.split('\n')

# Set up telegram_bot bot api client
TOKEN: Final = keys[0]
BOT_USERNAME: Final = keys[1]
app = Application.builder().token(TOKEN).build()
user_name = keys[4]
file_path = '/home/mateusz/PycharmProjects/binance_bot/send_to_telegram.txt'


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


async def check_file_and_send_message():
    while True:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'w+') as file:
                file_contents = file.read().strip()
            if file_contents:
                await app.bot.send_message(chat_id=user_name, text=file_contents)
                file.truncate()
        time.sleep(5)  # Check every 5 seconds


def handle_response(text: str) -> str:
    processed: str = text.lower()

    if 'hello' in processed:
        return 'hello'

    return 'I do not have an answer to that'


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
    print(f'Update {update} caused an error: {context.error}')


if __name__ == "__main__":
    print('Bot starting...')
    # Set up the command and message handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    # app.add_handler(MessageHandler(filters.Text, handle_message))
    app.add_error_handler(error)

    app.run_polling(1)

    # Start the file checking loop in the background
    app.loop.create_task(check_file_and_send_message())

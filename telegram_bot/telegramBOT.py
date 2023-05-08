from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


with open('../keys.txt', 'r') as file:
    # Read the entire contents of the file into a variable
    file_contents = file.read()
    keys = file_contents.split('\n')

# Set up telegram_bot bot api client
TOKEN: Final = keys[0]
BOT_USERNAME: Final = keys[1]
app = Application.builder().token(TOKEN).build()
user_name = keys[4]


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
    with open('../trade_results.txt', 'r') as file2:
        # Read the entire contents of the file into a variable
        file_contents = file2.read()
    await update.message.reply_text(f'You have earned/lost {file_contents}')


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


if __name__ == "__main__":
    print('Bot starting...')
    # Set up the command and message handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('custom', custom_command))
    app.add_handler(CommandHandler('result', result_command))
    app.add_handler(MessageHandler(filters.Text, handle_message))
    app.add_error_handler(error)

    app.run_polling(1)

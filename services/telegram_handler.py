import os 
import re
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from services import helper


CHAT_ID_PATH =".chatids"
token_key    = os.getenv("TELEGRAM_BOT_KEY")
bot          = Bot(token_key)

async def set_webhook():
    await bot.set_webhook(os.getenv('TELEGRAM_BOT_WEBHOOK'))
    print(f"Webhook set to {os.getenv('TELEGRAM_BOT_WEBHOOK')}")


async def updater(data: dict):
    chat_id  = data.get("message", {}).get("from", {}).get("id")
    username = data.get("message", {}).get("from", {}).get("username")
    message  = data.get("message", {}).get("text", "")

    await join_bot(
        chat_id=chat_id,
        username=username,
        message=message
    )

async def join_bot(chat_id: int, username: str, message: str) -> None:
    pattern = r'^/join \d+$'
    if re.match(pattern, message):
        project_id = message.split(" ")[1]

        config = helper.get_config_project(project_id)
        telegram_usernames = [item["telegram_username"] for item in config["members"]]
        
        if username in telegram_usernames:
            directory = f"{CHAT_ID_PATH}/{project_id}"

            if not os.path.exists(directory):
                os.makedirs(directory)

            file = open(f"{directory}/{username}.txt", "w")
            file.write(f"{chat_id}:{username}")

            await bot.send_message(chat_id, f"You have joined project ID {project_id}")
            return

        await bot.send_message(chat_id, f"You are not member of project ID {project_id}")

    else:
        await bot.send_message(chat_id, "Sorry, I don't know.")
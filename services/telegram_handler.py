import os 
import re
import json

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from telegram.constants import ParseMode
from telegram import Update, Bot
from services import helper
from configs import config


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

    if message == "/start":
        await send_text(chat_id, "Welcome to DevDsi \n\n You can join the project with this command : `/join gitlab_project_id:gitlab_username`")

    await join_bot(
        chat_id=chat_id,
        username=username,
        message=message
    )

    return data


async def join_bot(chat_id: int, username: str, message: str) -> None:
    pattern = r'^/join .+$'
    if re.match(pattern, message):
        pattern = r'^/join \d+:[a-zA-Z0-9]+$'
        if re.match(pattern, message):

            project_id = message.replace("/join ", "").split(":")[0]
            gitlab_username = message.replace("/join ", "").split(":")[1]
            if not config.get(project_id=project_id):
                await bot.send_message(chat_id, f"Invalid project ID {project_id}")
                return
            
            telegram_usernames = config.get_telegram_usernames(project_id=project_id)
            gitlab_usernames = config.get_gitlab_usernames(project_id=project_id)
            
            if username in telegram_usernames and gitlab_username in gitlab_usernames:
                directory = f"{CHAT_ID_PATH}/{project_id}"

                if not os.path.exists(directory):
                    os.makedirs(directory)

                file = open(f"{directory}/{gitlab_username}.txt", "w")
                file.write(f"{chat_id}:{username}:{gitlab_username}")

                await bot.send_message(chat_id, f"You have joined to project ID {project_id}")
                return

            await bot.send_message(chat_id, f"You are not member of project ID {project_id}")
        
        else:
            await bot.send_message(chat_id, "Format join must be : /join gitlab_project_id:gitlab_username")

    else:
        await bot.send_message(chat_id, "Sorry, I don't know.")


async def send_text(chat_id, text: str):
    await bot.send_message(
        chat_id=chat_id,
        parse_mode=ParseMode.MARKDOWN,
        text=text
    )
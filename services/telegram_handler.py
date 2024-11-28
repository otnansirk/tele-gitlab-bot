import os 
import re
import json

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from telegram.constants import ParseMode
from services import gitlab_handler
from telegram import Update, Bot
from services import helper
from configs import config
from consts import label
import datetime

CHAT_ID_PATH =".chatids"
token_key    = os.getenv("TELEGRAM_BOT_KEY")
bot          = Bot(token_key)

async def set_webhook():
    await bot.set_webhook(os.getenv("TELEGRAM_BOT_WEBHOOK"))
    print(f"Webhook set to {os.getenv('TELEGRAM_BOT_WEBHOOK')}")


async def updater(data: dict):
    chat_id  = data.get("message", {}).get("from", {}).get("id")
    username = data.get("message", {}).get("from", {}).get("username")
    message  = data.get("message", {}).get("text", "")

    join_pattern = r'^/join .+$'
    task_detail_pattern = r'^/taskd .+$'

    if message == "/start":
        await send_text(chat_id, "Welcome to DevDsi \n\n You can join the project with this command : `/join gitlab_project_id:gitlab_username`")
    elif re.match(join_pattern, message):
        await join_bot(
            chat_id=chat_id,
            username=username,
            message=message
        )
    elif re.match(task_detail_pattern, message):
        return await task_detail(
            chat_id=chat_id,
            username=username,
            message=message
        )
    else:
        await bot.send_message(chat_id, "Sorry, I don't know.")

    return data


async def join_bot(chat_id: int, username: str, message: str) -> None:
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



async def task_detail(chat_id: int, username: str, message: str):
    
    pattern = r'^/taskd \d+:[a-zA-Z0-9]+$'
    if re.match(pattern, message):
        project_id = message.replace("/taskd ", "").split(":")[0]
        issue_id = message.replace("/taskd ", "").split(":")[1]
            
        issue = gitlab_handler.get_issue(project_id, issue_id)
        issue_title = issue.title
        issue_url = issue.web_url
        issue_id = issue.iid

        issue_dict = json.loads(issue.to_json())
        closed_by = issue_dict["closed_by"]
        closed_at = issue_dict["closed_at"]

        events = issue.resourcelabelevents.list(all=True)
        tester_teams = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        dev_teams = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        
        reopen_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == label.REOPEN
            and item.__dict__['_attrs']["user"]["username"] in tester_teams
        ]
        inprogress_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == label.IN_PROGRESS
            and item.__dict__['_attrs']["user"]["username"] in dev_teams
        ]
        dev_done_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == label.DEV_DONE
            and item.__dict__['_attrs']["user"]["username"] in dev_teams
        ]

        date_format = "%A, %d %b %Y %H:%M"

        first_inprogress_date = "-"
        ordered_inprogress_events = sorted(inprogress_events, key=lambda item: item["created_at"])
        if len(ordered_inprogress_events):
            first_inprogress = ordered_inprogress_events[0]
            first_inprogress_date = datetime.datetime.fromisoformat(first_inprogress.get("created_at", "")).strftime(date_format)

        first_dev_done_date = "-"
        ordered_dev_done_events = sorted(dev_done_events, key=lambda item: item["created_at"])
        if len(ordered_dev_done_events):
            first_dev_done = ordered_dev_done_events[0]
            first_dev_done_date = datetime.datetime.fromisoformat(first_dev_done.get("created_at", "")).strftime(date_format)

        close_message = "-"
        if closed_by:
            closed_date = datetime.datetime.fromisoformat(closed_at).strftime(date_format)
            close_message = f"{closed_by.get('name', '')} \n*{closed_date}*"

        total_reopen = len(reopen_events)

        msg_first_inprogress = f"\n\nFirst IN PROGRESS \n*{first_inprogress_date}*"
        msg_first_dev_done = f"\n\nFirst DEV DONE \n*{first_dev_done_date}*"
        msg_total_reopen = f"\n\nTotal REOPEN \n*{total_reopen}*"
        msg_closed = f"\n\nCLOSED by {close_message}"
        msg_title = f"---\n*{issue_title}*"
        
        msg = f"[Task #{issue_id}]({issue_url}) {msg_first_inprogress} {msg_first_dev_done} {msg_closed} {msg_total_reopen} \n\n{msg_title}"
        
        await send_text(chat_id=chat_id, text=msg)

    else:
        await bot.send_message(chat_id, "Format taskd must be : /taskd gitlab_project_id:gitlab_issue_id")


async def send_text(chat_id, text: str):
    await bot.send_message(
        chat_id=chat_id,
        parse_mode=ParseMode.MARKDOWN,
        text=text
    )
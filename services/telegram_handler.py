import os 
import re
import json

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Updater
from consts import label as const_label, message as const_message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from core.db.database import Database
from services import gitlab_handler
from telegram import Update, Bot
from services import helper
from configs import config
import datetime


CHAT_ID_PATH =".chatids"
token_key    = os.getenv("TELEGRAM_BOT_KEY")
bot          = Bot(token_key)

async def set_webhook():
    await bot.set_webhook(os.getenv("TELEGRAM_BOT_WEBHOOK"))
    print(f"Webhook set to {os.getenv('TELEGRAM_BOT_WEBHOOK')}")

def _inline_keyboard_on_start():
    keyboard = [
        [
            InlineKeyboardButton("🆘 Help me", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def updater(data: dict):

    if "callback_query" in data:
        await callback_query_hanlder(data)

    if "message" in data:
        chat_id  = data.get("message", {}).get("from", {}).get("id")
        username = data.get("message", {}).get("from", {}).get("username")
        message  = data.get("message", {}).get("text", "")

        join_pattern = r'^/join .+$'
        task_detail_pattern = r'^/taskd .+$'

        if message == "/start":
            await bot.send_message(chat_id=chat_id, text=const_message.WELCOME_MESSAGE, reply_markup=_inline_keyboard_on_start(), parse_mode=ParseMode.MARKDOWN)
        elif message == "/help":
            return await send_text(
                chat_id=chat_id,
                text=const_message.HELP_MESSAGE
            )
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
            db = Database()
            tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).eq("gitlab_project_id", project_id).execute()
            if not (len(tele_account.data)):
                print(tele_account.count == None)
                tele_account_data = {
                    "chat_id": chat_id,
                    "username": username,
                    "gitlab_username": gitlab_username,
                    "gitlab_project_id": project_id,
                }
                db.insert("telegram_account", tele_account_data)

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
        current_state = issue.state

        issue_dict = json.loads(issue.to_json())
        closed_by = issue_dict["closed_by"]
        closed_at = issue_dict["closed_at"]

        events = issue.resourcelabelevents.list(all=True)
        tester_teams = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        tester_leads = config.get_gitlab_username_by_role(project_id=project_id, role="tester_lead")
        dev_teams = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        
        assignee_dev_msg = ""
        assignee_tester_msg = ""
        current_assignee_usernames = [assign["username"] for assign in issue.assignees]
        for username in current_assignee_usernames:
            if username in dev_teams:
                assignee_dev_msg = assignee_dev_msg+ username + ", "
            if username in tester_teams:
                assignee_tester_msg = assignee_tester_msg+ username + ", "
            if username in tester_leads:
                assignee_tester_msg = assignee_tester_msg+ username + ", "
            

        reopen_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == const_label.REOPEN
            and (
                item.__dict__['_attrs']["user"]["username"] in tester_teams
                or 
                item.__dict__['_attrs']["user"]["username"] in tester_leads
            )
        ]
        inprogress_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == const_label.IN_PROGRESS
            and item.__dict__['_attrs']["user"]["username"] in dev_teams
        ]
        dev_done_events = [
            item.__dict__['_attrs'] for item in events 
            if item.__dict__['_attrs']["action"] == "add" 
            and item.__dict__['_attrs']["label"]["name"] == const_label.DEV_DONE
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

        msg = helper.get_taskd_message(
            issue_id=issue_id,
            issue_url=issue_url,
            current_state=current_state,
            assignee_dev_msg=assignee_dev_msg,
            assignee_tester_msg=assignee_tester_msg,
            msg_first_inprogress=first_inprogress_date,
            msg_first_dev_done=first_dev_done_date,
            msg_closed=close_message,
            msg_total_reopen=total_reopen,
            task_title=issue_title
        )
        await send_text(chat_id=chat_id, text=msg)

    else:
        await bot.send_message(chat_id, "Format taskd must be : /taskd gitlab_project_id:gitlab_issue_id")


async def send_text(chat_id, text: str):
    await bot.send_message(
        chat_id=chat_id,
        parse_mode=ParseMode.MARKDOWN,
        text=text
    )

async def callback_query_hanlder(data: dict):
    query = data.get("callback_query", {})
    callback_data = data.get("callback_query", {}).get("data", "")
    message_id = query.get("message", {}).get("message_id", "")
    chat_id = query.get("message", {}).get("chat", {}).get("id", "")
    if callback_data == "home":
        msg = const_message.WELCOME_MESSAGE
        markup = [
            [InlineKeyboardButton("🆘 Help me", callback_data="help")]
        ]
        await bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=msg, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(markup)
        )

    if callback_data == "help":
        msg = const_message.HELP_MESSAGE
        markup = [
            [InlineKeyboardButton("⬅️ Back to home", callback_data="home")]
        ]
        await bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=msg, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(markup)
        )
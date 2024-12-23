import os 
import re
import json
import requests

import gitlab
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


def bot():
    token_key = os.getenv("TELEGRAM_BOT_KEY")
    return Bot(token_key)


async def set_webhook():
    await bot().set_webhook(os.getenv("TELEGRAM_BOT_WEBHOOK"))
    print(f"Webhook set to {os.getenv('TELEGRAM_BOT_WEBHOOK')}")

def _inline_keyboard_on_start():
    keyboard = [
        [
            InlineKeyboardButton("🆘 Guide Me", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_text(chat_id, text: str):
    await bot().send_message(
        chat_id=chat_id,
        parse_mode=ParseMode.MARKDOWN,
        text=text
    )

async def updater(data: dict):
    if "callback_query" in data:
        await callback_query_hanlder(data)

    if "message" in data:
        chat_id  = data.get("message", {}).get("from", {}).get("id")
        username = data.get("message", {}).get("from", {}).get("username")
        message  = data.get("message", {}).get("text", "")

        join_pattern = r'^/join .+$'
        task_detail_pattern = r'^/taskd .+$'
        my_task_pattern = '/mytask'
        surprise_me_pattern = '/surpriseme'
        meme_pattern = r'^meme .+$'

        if message == "/start":
            await bot().send_message(chat_id=chat_id, text=const_message.WELCOME_MESSAGE, reply_markup=_inline_keyboard_on_start(), parse_mode=ParseMode.MARKDOWN)
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
        elif my_task_pattern == message:
            return await my_task(
                chat_id=chat_id,
                username=username
            )
        elif surprise_me_pattern == message:
            return await tenor(
                chat_id=chat_id
            )
        elif re.match(meme_pattern, message, re.IGNORECASE):
            return await tenor(
                chat_id=chat_id,
                q=message
            )
        else:
            await send_text(chat_id, "Sorry, I don't know.")

        return data


async def join_bot(chat_id: int, username: str, message: str) -> None:
    pattern = r'^/join \d+:.*$'
    if re.match(pattern, message):

        project_id = message.replace("/join ", "").split(":")[0]
        gitlab_username = message.replace("/join ", "").split(":")[1]
        if not config.get(project_id=project_id):
            await bot().send_message(chat_id, f"Invalid project ID {project_id}")
            return
        
        telegram_usernames = config.get_telegram_usernames(project_id=project_id)
        gitlab_usernames = config.get_gitlab_usernames(project_id=project_id)
        
        if username in telegram_usernames and gitlab_username in gitlab_usernames:
            db = Database()
            tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).eq("gitlab_project_id", project_id).execute()
            if not (len(tele_account.data)):
                tele_account_data = {
                    "chat_id": chat_id,
                    "username": username,
                    "gitlab_username": gitlab_username,
                    "gitlab_project_id": project_id,
                }
                db.insert("telegram_account", tele_account_data)

            await bot().send_message(chat_id, f"You have joined to project ID {project_id}")
            return

        await bot().send_message(chat_id, f"You are not member of project ID {project_id}")
    
    else:
        await bot().send_message(chat_id, "Format join must be : /join gitlab_project_id:gitlab_username")

async def task_detail(chat_id: int, username: str, message: str):
    date_format = "%A, %d %b %Y %H:%M"

    pattern = r'^/taskd \d+$'
    if re.match(pattern, message):
        db = Database()
        tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).execute()
        if not len(tele_account.data):
            await send_text(chat_id=chat_id, text="You are not member")
            return {"NO"}
        
        await send_text(chat_id=chat_id, text="Calculating...")

        for user in tele_account.data:
            username = user.get("gitlab_username", "")
            project_id = user.get("gitlab_project_id", "")
            issue_id = message.replace("/taskd ", "").split(":")[0]
            
            try:
                issue        = gitlab_handler.get_issue(project_id=project_id, id=issue_id)
                issue_title  = issue.title
                issue_id     = issue.iid
                issue_weight = issue.weight if issue.weight else 0
                issue_dict = json.loads(issue.to_json())

                closed_by = issue_dict["closed_by"]
                closed_at = issue_dict["closed_at"]

                events = issue.resourcelabelevents.list(all=True)
                tester_teams = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
                tester_leads = config.get_gitlab_username_by_role(project_id=project_id, role="tester_lead")
                dev_teams = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
                
                assignee_devs = []
                assignee_testers = []
                current_assignee_usernames = [assign["username"] for assign in issue.assignees]
                for username in current_assignee_usernames:
                    if username in dev_teams:
                        assignee_devs.append(username)
                    if (username in tester_teams) or (username in tester_leads):
                        assignee_testers.append(username)

                assignee_dev_msg = ",".join(assignee_devs)
                assignee_tester_msg = ",".join(assignee_testers)

                last_event = sorted([item.__dict__['_attrs'] for item in events],  key=lambda item: item["created_at"])
                last_update_by = ""
                last_update_at = "-"
                if len(last_event):
                    last_event_dict = last_event.pop()
                    last_update_by  = last_event_dict.get("user", {}).get("username")
                    last_update_label_name = last_event_dict.get("label", {}).get("name", "-")
                    last_update_at = last_update_label_name+"\n"+datetime.datetime.fromisoformat(last_event_dict.get("created_at", "")).strftime(date_format)

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
                internal_testing_events = [
                    item.__dict__.get("_attrs") for item in events 
                    if item.__dict__.get("_attrs", {}).get("action", "") == "add"
                    and item.__dict__.get("_attrs", {}).get("label", {}).get("name", "") == const_label.INTERNAL_TESTING
                    and item.__dict__.get("_attrs", {}).get("user", {})
                    and item.__dict__.get('_attrs', {}).get("user", {}).get("username", "") in tester_teams
                ]
                dev_done_events = [
                    item.__dict__['_attrs'] for item in events 
                    if item.__dict__['_attrs']["action"] == "add" 
                    and item.__dict__['_attrs']["label"]["name"] == const_label.DEV_DONE
                    and item.__dict__.get("_attrs", {}).get("user", {})
                    and item.__dict__['_attrs']["user"]["username"] in dev_teams
                ]

                first_inprogress_date = "-"
                ordered_inprogress_events = sorted(inprogress_events, key=lambda item: item["created_at"])
                if len(ordered_inprogress_events):
                    first_inprogress = ordered_inprogress_events[0]
                    first_inprogress_date = datetime.datetime.fromisoformat(first_inprogress.get("created_at", "")).strftime(date_format)

                first_internal_testing_date = "-"
                ordered_internal_testing_events = sorted(internal_testing_events, key=lambda item: item["created_at"])
                if len(ordered_internal_testing_events):
                    first_internal_testing = ordered_internal_testing_events.pop(0)
                    first_internal_testing_date = datetime.datetime.fromisoformat(first_internal_testing.get("created_at", "")).strftime(date_format)

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

                work_suration = ""
                hours_given = ""
                reward = ""
                if len(ordered_inprogress_events) and len(ordered_dev_done_events):
                    work_duration_in_second = helper.calculate_working_hours(ordered_inprogress_events[0].get("created_at", ""), ordered_dev_done_events[0].get("created_at", ""))
                    hours_given   = issue_weight * 4
                    seconds_given = hours_given * 3600

                    work_suration = helper.second_2_time(work_duration_in_second)

                    if work_duration_in_second < seconds_given:
                        reward = "Amazing Job 🤩"
                    elif work_duration_in_second > seconds_given:
                        reward = "Better Next Time 😡"
                    else:
                        reward = "Good Job 😊"


                project = gitlab_handler.get_project(project_id=project_id)
                msg = helper.get_taskd_message(
                    project=project,
                    issue=issue,
                    assignee_dev_msg=assignee_dev_msg,
                    assignee_tester_msg=assignee_tester_msg,
                    msg_first_inprogress=first_inprogress_date,
                    msg_first_dev_done=first_dev_done_date,
                    msg_first_internal_testing=first_internal_testing_date,
                    msg_last_update_by=last_update_by,
                    msg_last_update_at=last_update_at,
                    msg_closed=close_message,
                    msg_total_reopen=total_reopen,
                    msg_work_duration=work_suration,
                    msg_weight=hours_given,
                    reward=reward,
                    task_title=issue_title
                )
                await send_text(chat_id=chat_id, text=msg)

            except Exception as e:
                print("task_detail", e)
                await send_text(chat_id, f"Failed to calculate task detail {issue_id}")
                return {"issue not found"}

    else:
        await send_text(chat_id, "Format taskd must be : `/taskd GITLAB_ISSUE_ID`")

async def callback_query_hanlder(data: dict):
    query = data.get("callback_query", {})
    callback_data = data.get("callback_query", {}).get("data", "")
    message_id = query.get("message", {}).get("message_id", "")
    chat_id = query.get("message", {}).get("chat", {}).get("id", "")
    if callback_data == "home":
        msg = const_message.WELCOME_MESSAGE
        markup = [
            [InlineKeyboardButton("🆘 Guide Me", callback_data="help")]
        ]
        await bot().edit_message_text(
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
        await bot().edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=msg, 
            parse_mode=ParseMode.MARKDOWN, 
            reply_markup=InlineKeyboardMarkup(markup)
        )

async def my_task(chat_id: int, username: str):
    db = Database()
    tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).execute()
    if not len(tele_account.data):
        await send_text(chat_id=chat_id, text="You are not member")
        return {"NO"}

    await send_text(chat_id=chat_id, text="Calculating...")
    for user in tele_account.data:
        username = user.get("gitlab_username", "")
        project_id = user.get("gitlab_project_id", "")
        project = gitlab_handler.get_project(project_id)

        if project:
            roles = config.get_role_by_gitlab_username(project_id=project_id, username=username)
            msg_inprogress = ""
            msg_todo = ""
            msg_merge_request = ""
            msg_devdone = ""
            msg_reopen = ""
            msg_internal_testing = ""

            
            if "dev_team" in roles:
                todo_issues = project.issues.list(assignee_username=username, state=const_label.OPENED, labels=[])
                todo_issues = [
                    issue.__dict__['_attrs']
                    for issue in todo_issues
                    if not any(label in const_label.LABELS for label in issue.labels)
                ]
                if len(todo_issues):
                    msg_todo = get_format_issue("TODO", todo_issues)

                inprogress_issues = project.issues.list(assignee_username=username, state=const_label.OPENED, labels=[const_label.IN_PROGRESS])
                inprogress_issues = [issue.__dict__['_attrs'] for issue in inprogress_issues]
                if len(inprogress_issues):
                    msg_inprogress = get_format_issue(const_label.IN_PROGRESS, inprogress_issues)

                reopen_issues = project.issues.list(assignee_username=username, state=const_label.OPENED, labels=[const_label.REOPEN])
                reopen_issues = [issue.__dict__['_attrs'] for issue in reopen_issues]
                if len(reopen_issues):
                    msg_reopen = get_format_issue(const_label.REOPEN, reopen_issues)


            if ("tester_team" in roles) and ("tester_lead" in roles):
                devdone_issues = project.issues.list(assignee_username=username, state=const_label.OPENED, labels=[const_label.DEV_DONE])
                devdone_issues = [issue.__dict__['_attrs'] for issue in devdone_issues]
                if len(devdone_issues):
                    msg_devdone = get_format_issue(const_label.DEV_DONE, devdone_issues)

                internal_testing_issues = project.issues.list(assignee_username=username, state=const_label.OPENED, labels=[const_label.INTERNAL_TESTING])
                internal_testing_issues = [issue.__dict__['_attrs'] for issue in internal_testing_issues]
                if len(internal_testing_issues):
                    msg_internal_testing = get_format_issue(const_label.INTERNAL_TESTING, internal_testing_issues)


            if "dev_lead" in roles:
                opened_mr = project.mergerequests.list(reviewer_username=username, state=const_label.OPENED)
                opened_mr =  [item.__dict__['_attrs'] for item in opened_mr]
                msg_merge_request = get_format_mr(project_id=project_id, merge_requests=opened_mr)


            msg_detail = helper.get_mytask_message(
                project=project,
                reopen=msg_reopen,
                todo=msg_todo,
                inprogress=msg_inprogress,
                devdone=msg_devdone,
                internal_testing=msg_internal_testing,
                merge_request=msg_merge_request
            )
            await send_text(chat_id, f"{msg_detail}")
    return msg_todo


def get_format_issue(label, issues):
    msg_todos = [f"*{label}* :"]
    for issue in issues:
        iid    = issue.get("iid", "")
        title  = issue.get("title", "")
        url    = issue.get("web_url", "")
        labels  = ",".join([label for label in issue.get("labels", [])])
        msg    = f"""
- [Task #{iid}]({url}) {title} 
   Labels : _{labels}_
"""
        msg_todos.append(msg)
    msg_todo = "".join(msg_todos)+"\n"
    return msg_todo

def get_format_mr(project_id, merge_requests):
    msg_mr = ["*Merge Request* :"]
    for mr in merge_requests:
        iid    = mr.get("iid", "")
        title  = mr.get("title", "")
        url    = mr.get("web_url", "")
        issue_title_split = title.split("#")
        if len(issue_title_split) > 1:
            mr_title  = issue_title_split[0]
            issue_id  = issue_title_split[1]
            issue     = gitlab_handler.get_issue(project_id, id=issue_id)
            issue_url = issue.web_url
            issue_state = issue.state
            issue_title = issue.state

            issue_detail = f"{issue_title} [Task#{issue_id}]({issue_url}) | {issue_state.upper()}"
            
            msg = f"""- [MR #{iid}]({url}) {mr_title} {issue_detail}"""
            msg_mr.append(msg)

    msg_mr = "\n".join(msg_mr)+"\n"
    return msg_mr


async def tenor(chat_id, q= "Sarcastic%20Meme"):
    api_key = os.getenv("TENOR_API")
    base_url = os.getenv("TENOR_URL")
    try:
        api_url = f"{base_url}/search?q={q}&key={api_key}&limit=1&locale=id_ID&random=true"
        memes   = requests.get(api_url).json()
        data    = memes.get("results", [])[0].get("media_formats", {}).get("gif")

        await bot().send_document(chat_id=chat_id, document=data.get("url"))
    except Exception:
        await send_text(chat_id=chat_id, text="Kenapa kamu melotot ?")
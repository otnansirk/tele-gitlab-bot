import json
from core.db.database import Database
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.responses import JSONResponse


def get_telegram_chat(project_id: str, gitlab_username: str):
    try:
        db = Database()
        tele_account = db.fetch(table_name="telegram_account").select("*").eq("gitlab_username", gitlab_username).eq("gitlab_project_id", project_id).execute()
        if len(tele_account.data):
            chat = tele_account.data[0]
            return {
                "id": chat.get("chat_id", ""),
                "username": chat.get("username", ""),
                "gitlab_username": chat.get("gitlab_username", ""),
                "project_id": chat.get("gitlab_project_id", ""),
            }
        return {}
    except FileNotFoundError:
        return None

def get_user_by_telegram_chat(project_id: str, telegram_username: str):
    try:
        db = Database()
        tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", telegram_username).eq("gitlab_project_id", project_id).execute()
        if len(tele_account.data):
            chat = tele_account.data[0]
            return {
                "id": chat.get("chat_id", ""),
                "username": chat.get("username", ""),
                "gitlab_username": chat.get("gitlab_username", ""),
                "project_id": chat.get("gitlab_project_id", ""),
            }
        return {}
    except FileNotFoundError:
        return None

def get_project_member_by_gitlab_username(project, username: str):
    all_members = project.members_all.list(get_all=True)
    all_members = [member.__dict__["_attrs"] for member in all_members]

    for member in all_members:
        if member["username"] == username:
            return member
    
    return {}

def get_global_message(author_name, to, issue_id, issue_url, title, label):
    return f"Hi {to}, [Task #{issue_id}]({issue_url}) updated to *{label.upper()}* by {author_name}. \n\n---\n _{title}_"

def get_assignee_task_message(author_name, to, issue_id, issue_url, title):
    return f"Hi {to}, {author_name} has assigned you [Task #{issue_id}]({issue_url}). We’re believe in your ability to complete it. Let us know if you need support. Thanks! \n\n---\n _{title}_"

def get_self_assignee_task_message(to, issue_id, issue_url, title):
    return f"Hi {to}, Thank you for taking on this assignment [Task #{issue_id}]({issue_url}). We’re believe in your ability to complete it. Let us know if you need support. Thanks! \n\n---\n _{title}_"

def get_update_desc_task_message(to, issue_id, issue_url, title):
    return f"Hi {to}, There is an update to the issue description regarding [Task #{issue_id}]({issue_url}). Please double check to ensure it is in accordance with the latest updates.Thank you for taking on this assignment \n\n---\n _{title}_"

def get_reopen_message(author_name, to, issue_id, issue_url, title):
    return f"Hi {to}, [Task #{issue_id}]({issue_url}) didn't pass the test, updated to *REOPEN* by {author_name}. Please check immediately \n\n---\n _{title}_"

def get_after_reopen_message(author_name, to, issue_id, issue_url, title):
    return f"Hi {to}, [Task #{issue_id}]({issue_url}) you *REOPEN*, is updated to *DEV DONE* by {author_name}. Please check immediately \n\n---\n _{title}_"

def get_closed_message(author_name, to, issue_id, issue_url, title, mr_msg: list):
    if mr_msg:
        mr_msg = f"*Detail MR :* \n {mr_msg}"

    return f"Hi {to}, [Task #{issue_id}]({issue_url}) updated to *CLOSED* by {author_name}. Please check immediately \n\n {mr_msg} \n\n ---\n _{title}_"
    
def get_taskd_message(
    project,
    issue,
    assignee_dev_msg: str,
    assignee_tester_msg: str,
    msg_first_inprogress: str,
    msg_first_dev_done: str,
    msg_first_internal_testing: str,
    msg_last_update_by: str,
    msg_last_update_at: str,
    msg_closed: str,
    msg_total_reopen: str,
    msg_work_duration: str,
    msg_weight: str,
    reward: str,
    task_title: str
):
    labels = ", ".join(issue.labels)

    return f"""
_{project.name} :_ [ID#{project.id}]({project.web_url})

[Task #{issue.iid}]({issue.web_url}) : *{issue.state.upper()}*
_{labels.capitalize()}_

Assign to :
*Dev :*
{assignee_dev_msg}
*Tester :* 
{assignee_tester_msg}

*Last Update* by {msg_last_update_by}
{msg_last_update_at}

*First In Progress*
{msg_first_inprogress}        

*First Dev Done*
{msg_first_dev_done}

*First Internal Testing*
{msg_first_internal_testing}

*Closed* by {msg_closed}

Weight
*{issue.weight} - {msg_weight}h*

Time spent
*{msg_work_duration}* - {reward}

Total Reopen
*{msg_total_reopen}*


---
_{task_title}_
"""

def get_mytask_message(project, reopen, todo, inprogress, devdone, internal_testing, merge_request):
    return f"""
_{project.name} :_ [ID#{project.id}]({project.web_url})

The following are the details of the assignments that have been handed over to you:

{reopen}{todo}{inprogress}{devdone}{internal_testing}{merge_request}
    """

def get_monthly_holiday_message(holiday):
    return f"""Hi team,
Bulan ini ada hari libur, lho! 
Kalau kalian mau, kalian bisa ambil cuti supaya liburnya lebih panjang dan lebih santai ✨.

Berikut detail hari liburnya, ya:

{holiday}

_Confirmasikan ke Lead ya apakah kantor kita juga mengikuti libur ini_

Semoga kalian bisa memanfaatkannya untuk istirahat atau melakukan hal-hal yang kalian sukai. 

Kalau ada rencana cuti, jangan lupa diskusikan dulu, ya, supaya semuanya tetap lancar!
    """

def get_holiday_message(holiday):
    return f"""Berikut detail hari libur untuk 30 hari kedepan, ya:

{holiday}

_Confirmasikan ke Lead ya apakah kantor kita juga mengikuti libur ini_

    """

def is_working_day(date):
    return date.weekday() < 5  # Senin (0) sampai Jumat (4)

def calculate_working_hours(start_date, end_date, work_start_hour=9, work_end_hour=17, break_start_hour=12, break_end_hour=13):
    
    start_date = datetime.fromisoformat(start_date).astimezone(ZoneInfo("UTC"))
    end_date = datetime.fromisoformat(end_date).astimezone(ZoneInfo("UTC"))

    total_working_seconds = 0
    current_date = start_date
    while current_date < end_date:
        if is_working_day(current_date):
            work_start  = datetime(current_date.year, current_date.month, current_date.day, work_start_hour, 0, 0, tzinfo=ZoneInfo("UTC"))
            work_end    = datetime(current_date.year, current_date.month, current_date.day, work_end_hour, 0, 0, tzinfo=ZoneInfo("UTC"))
            break_start = datetime(current_date.year, current_date.month, current_date.day, break_start_hour, 0, 0, tzinfo=ZoneInfo("UTC"))
            break_end   = datetime(current_date.year, current_date.month, current_date.day, break_end_hour, 0, 0, tzinfo=ZoneInfo("UTC"))

            if end_date < work_start:
                break 
            elif end_date <= work_end:
                if end_date > break_start and end_date < break_end:
                    total_working_seconds += (end_date - work_start).total_seconds() - 3600  # Mengurangi 1 jam untuk waktu istirahat
                else:
                    total_working_seconds += (end_date - work_start).total_seconds()
                break  
            else:
                if break_end > work_start and break_end < work_end:
                    total_working_seconds += (break_start - work_start).total_seconds() + (work_end - break_end).total_seconds()
                else:
                    total_working_seconds += (work_end - work_start).total_seconds()
        
        current_date += timedelta(days=1)

    return total_working_seconds


def get_external_webhook_message(method, url, params, body, headers):
    return f"""
*External Webhook*

*URL*
`[{method}] {url}`

*HEADER*
```{headers}```

*PARAM*
```{params}```

*BODY*
```{body}```
"""

def second_2_time(seconds):
    seconds = seconds % (24 * 3600)
    hour    = seconds // 3600
    
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
     
    return "%d:%02d:%02d" % (hour, minutes, seconds)


def res_success(data= {}):
    return JSONResponse(
        status_code=200, 
        content={
            "data": data,
            "meta": {
                "code": "success",
                "message": "Success"
            }
        }
    )

def res_error(data: dict = {}):
    return JSONResponse(
        status_code=400, 
        content={
            "data": data,
            "meta": {
                "code": "error",
                "message": "Error"
            }
        }
    )
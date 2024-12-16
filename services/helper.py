import json
from core.db.database import Database

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
    return f"Hi {to}, {author_name} has assigned you [Task #{issue_id}]({issue_url}). We’re confident in your ability to complete it. Let us know if you need support. Thanks! \n\n---\n _{title}_"

def get_self_assignee_task_message(to, issue_id, issue_url, title):
    return f"Hi {to}, Thank you for taking on this assignment [Task #{issue_id}]({issue_url}). We’re confident in your ability to complete it. Let us know if you need support. Thanks! \n\n---\n _{title}_"

def get_reopen_message(author_name, to, issue_id, issue_url, title):
    return f"Hi {to}, [Task #{issue_id}]({issue_url}) didn't pass the test, updated to *REOPEN* by {author_name}. Please check immediately \n\n---\n _{title}_"

def get_after_reopen_message(author_name, to, issue_id, issue_url, title):
    return f"Hi {to}, [Task #{issue_id}]({issue_url}) you *REOPEN*, is updated to *DEV DONE* by {author_name}. Please check immediately \n\n---\n _{title}_"

def get_closed_message(author_name, to, issue_id, issue_url, title, mr_msg: list):
    if mr_msg:
        mr_msg = f"*Detail MR :* \n {mr_msg}"

    return f"Hi {to}, [Task #{issue_id}]({issue_url}) updated to *CLOSED* by {author_name}. Please check immediately \n\n {mr_msg} \n\n ---\n _{title}_"
    
def get_taskd_message(
    issue_id: str,
    issue_url: str,
    current_state: str,
    assignee_dev_msg: str,
    assignee_tester_msg: str,
    msg_first_inprogress: str,
    msg_first_dev_done: str,
    msg_last_update_by: str,
    msg_last_update_at: str,
    msg_closed: str,
    msg_total_reopen: str,
    task_title: str
):
    return f"""
[Task #{issue_id}]({issue_url}) : *{current_state.upper()}*

Assign to :
Dev     = {assignee_dev_msg}
Tester = {assignee_tester_msg}

*Last Update* by {msg_last_update_by}
{msg_last_update_at}

*First In Progress*
{msg_first_inprogress}        

*First Dev Done*
{msg_first_dev_done}

*Closed* by {msg_closed}

Total Reopen
*{msg_total_reopen}*


---
_{task_title}_
"""

def get_mytask_message(reopen, todo, inprogress, devdone, internal_testing):
    return f"""
The following is a detailed assignment that has been handed over to you:

{reopen}{todo}{inprogress}{devdone}{internal_testing}
    """
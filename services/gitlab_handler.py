import gitlab
import os
import json
from services import helper
from services import telegram_handler
from telegram.constants import ParseMode
from configs import config


async def updater(data: dict):
    url         = os.getenv("GITLAB_BASEURL")
    token       = os.getenv("GITLAB_TOKEN")
    project_id  = data.get('project', {}).get('id')
    issue_id    = data.get('object_attributes', {}).get('iid')
    changes     = data.get('changes', {})

    gl = gitlab.Gitlab(url=url, private_token=token)
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_id)
    
    if issue.type == "ISSUE":
        await issue_handler(
            project=project,
            issue=issue,
            changes=changes
        )

    return json.loads(issue.to_json())


# assignee member to issue
async def issue_handler(**params):

    project = params.get("project")
    issue   = params.get("issue")
    changes = params.get("changes")
    project_id = issue.project_id

    notify_to = config.get_gitlab_member_by_label(project_id=project_id, labels=issue.labels)
    
    if not issue.labels and issue.state == "opened":
        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        await notify_to_dev(notify_to, issue, changes)

    if "Dev Done" in issue.labels:
        await dev_done(project, notify_to, issue, changes)
    


async def notify_to_dev(notify_to, issue, changes):
    title      = issue.title
    project_id = issue.project_id
    issue_url  = issue.web_url
    issue_id   = issue.iid

    if "assignees" in changes:
        username = changes.get("assignees", {}).get("current", []).pop().get("username", "")
        if username in notify_to:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            tele_user = chat.get("username")
            
            text = f"Hi {tele_user}, Selamat kamu dapat tugas baru, [Task #{issue_id}]({issue_url}). Mohon segera *dikerjakan* \n\n---\n {title}"
            await telegram_handler.send_text(chat.get("id"), text=text)



async def dev_done(project, notify_to, issue, changes):
    title      = issue.title
    project_id = issue.project_id
    issue_url  = issue.web_url
    issue_id   = issue.iid
    current_assignee_ids = [assign["id"] for assign in issue.assignees]


    if "labels" in changes:
        tester_lead_gitlab_ids = []
        for username in notify_to:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            tele_user = chat.get("username")
            text = f"Hi {tele_user}, [Task #{issue_id}]({issue_url}) sudah *DEV-DONE*. Mohon segera dilakukan *pengujian* \n\n---\n {title}"
            member_on_project = helper.get_project_member_by_gitlab_username(project=project, username=username)
            tester_lead_gitlab_ids.append(member_on_project.get("id", ""))
            await telegram_handler.send_text(chat.get("id"), text=text)

        issue.assignee_ids = current_assignee_ids + dev_lead_ids
        issue.save()

    if "assignees" in changes:
        for assignee in issue.assignees:
            username = assignee.get("username", "")

            registered_gitlab_usernames = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
            if username in registered_gitlab_usernames:
                chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
                tele_user = chat.get("username")

                text = f"Hi {tele_user}, Selamat kamu dapat tugas baru, [Task #{issue_id}]({issue_url}). Mohon segera dilakukan *pengujian* \n\n---\n {title}"
                await telegram_handler.send_text(chat.get("id"), text=text)
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
            payload=data,
            project=project,
            issue=issue,
            changes=changes
        )

    return json.loads(issue.to_json())


# assignee member to issue
async def issue_handler(**params):

    payload = params.get("payload")
    project = params.get("project")
    issue   = params.get("issue")
    changes = params.get("changes")
    action  = payload.get('object_attributes', {}).get('action')

    project_id = str(issue.project_id)
    title      = issue.title
    issue_url  = issue.web_url
    issue_id   = issue.iid

    notify_to = config.get_gitlab_usernames_by_label(project_id=project_id, labels=issue.labels)
    if not issue.labels and issue.state == "opened":
        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        msg = f"Selamat kamu dapat tugas baru, [Task #{issue_id}]({issue_url}). Mohon segera *dikerjakan* \n\n---\n {title}"
        await notify_to_dev(notify_to, issue, message=msg)

    if "Dev Done" in issue.labels:
        await dev_done(project, notify_to, issue, changes)
    
    if "Internal Testing" in issue.labels:
        await internal_testing(issue)
    
    if "Reopen" in issue.labels and issue.state == "opened":
        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        tester_teams = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        
        author_username = issue.author.get("username", "")
        
        if author_username in tester_teams:
            await reopen(notify_to, issue)

    if issue.state == "closed" and "close" in action:
        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_lead")
        await closed(notify_to=notify_to, issue=issue)


async def notify_to_dev(notify_to, changes, message):

    if "assignees" in changes:
        username = changes.get("assignees", {}).get("current", []).pop().get("username", "")
        if username in notify_to:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :    
                tele_user = chat.get("username")
                
                text = f"Hi {tele_user}, {message}"
                await telegram_handler.send_text(chat.get("id"), text=text)


async def dev_done(project, notify_to, issue, changes):
    title      = issue.title
    project_id = str(issue.project_id)
    issue_url  = issue.web_url
    issue_id   = issue.iid
    current_assignee_ids = [assign["id"] for assign in issue.assignees]


    if "labels" in changes and "Reopen" not in issue.labels:
        tester_lead_gitlab_ids = []
        for username in notify_to:
            member_on_project = helper.get_project_member_by_gitlab_username(project=project, username=username)
            if member_on_project.get("username"):
                tester_lead_gitlab_ids.append(member_on_project.get("id", ""))
                
                chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=member_on_project.get("username"))
                if chat :    
                    tele_user = chat.get("username")
                    text = f"Hi {tele_user}, [Task #{issue_id}]({issue_url}) sudah *DEV-DONE*. Mohon segera dilakukan *pengujian* \n\n---\n {title}"

                    await telegram_handler.send_text(chat.get("id"), text=text)

        issue.assignee_ids = current_assignee_ids + tester_lead_gitlab_ids
        issue.save()

    if "assignees" in changes:
        msg = f"Selamat kamu dapat tugas baru, [Task #{issue_id}]({issue_url}). Mohon segera dilakukan *pengujian* \n\n---\n {title}"
        await _notify_to_tester_team(assignees=issue.assignees, project_id=project_id, message=msg)

    if "Reopen" in issue.labels:
        msg = f"Reopen [Task #{issue_id}]({issue_url}). Sudah dapat kamu tes kembali. Mohon segera dilakukan *pengujian* ulang \n\n---\n {title}"
        await _notify_to_tester_team(assignees=issue.assignees, project_id=project_id, message=msg)


async def internal_testing(issue):
    issue.labels = [label for label in issue.labels if label != "Reopen"]
    issue.save()
    

async def reopen(notify_to, issue):
    title      = issue.title
    project_id = str(issue.project_id)
    issue_url  = issue.web_url
    issue_id   = issue.iid
    author_username = issue.author.get("username", "")
    current_assignees = [assign["username"] for assign in issue.assignees]

    for username in notify_to:
        if username in current_assignees:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :
                chat_author = helper.get_telegram_chat(project_id=project_id, gitlab_username=author_username)
                tele_user = chat.get("username")
                tele_user_author = chat_author.get("username")

                text = f"Hi {tele_user}, [Task #{issue_id}]({issue_url}) tidak lolos tes, di *RE-OPEN* oleh @{tele_user_author}. Mohon segera *cek* dan *dikerjakan* \n\n---\n {title}"
                await telegram_handler.send_text(chat.get("id"), text=text)


async def _notify_to_tester_team(assignees, project_id, message: str):
    for assignee in assignees:
        username = assignee.get("username", "")

        registered_gitlab_usernames = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        if username in registered_gitlab_usernames:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :    
                tele_user = chat.get("username")

                text = f"Hi {tele_user}, {message}"
                await telegram_handler.send_text(chat.get("id"), text=text)


async def closed(notify_to: list, issue):

    project_id = str(issue.project_id)
    title      = issue.title
    issue_url  = issue.web_url
    issue_id   = issue.iid

    issue.labels = [label for label in issue.labels if label not in config.get_labels(project_id=project_id)]
    issue.save()
    
    mr_messages = []
    merge_requests = [mr for mr in issue.related_merge_requests() if mr.get("state", "") == "opened"]
    for index, mr in enumerate(merge_requests, start=1):
        mr_title = mr.get("title", "")
        mr_url = mr.get("web_url")
        author_name = mr.get("author", {}).get("name")

        msg = f"{index}. [{mr_title}]({mr_url}) permintaan dari {author_name}"
        mr_messages.append(msg)

    mr_message = "\n".join(mr_messages)
    for username in notify_to:
        chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
        if chat :
            tele_user = chat.get("username")
            msg = f"Hi {tele_user}, [Task #{issue_id}]({issue_url}). Sudah *CLOSE*, mohon segera *dilakukan merge* \n\n *Merge Request* : \n {mr_message} \n\n---\n {title}"
            await telegram_handler.send_text(chat.get("id"), text=msg)
import gitlab
import os
import json
from services import helper
from services import telegram_handler
from telegram.constants import ParseMode
from configs import config
import consts.label

def init_project(project_id):
    url         = os.getenv("GITLAB_BASEURL")
    token       = os.getenv("GITLAB_TOKEN")

    gl = gitlab.Gitlab(url=url, private_token=token)
    return gl.projects.get(project_id)

def get_issue(project_id: str, id: str):
    project = init_project(project_id=project_id)
    return project.issues.get(id=id)

async def updater(data: dict):
    project_id  = data.get("project", {}).get("id")
    issue_id    = data.get("object_attributes", {}).get("iid")
    changes     = data.get("changes", {})

    project = init_project(project_id)
    issue = get_issue(project_id, issue_id)
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
    action  = payload.get("object_attributes", {}).get("action")

    project_id = str(issue.project_id)

    if not any(item in config.get_labels(project_id=project_id) for item in issue.labels) and  issue.state == "opened":
        await _notify_to_dev(changes, issue)

    if consts.label.IN_PROGRESS in issue.labels:
        await _notify_to_pm(issue=issue, label=consts.label.IN_PROGRESS)

    if consts.label.DEV_DONE in issue.labels:
        notify_to = config.get_gitlab_username_by_label(project_id=project_id, labels=issue.labels)
        await dev_done(project, notify_to, issue, changes)
        await _notify_to_pm(issue=issue, label=consts.label.DEV_DONE)

    if consts.label.INTERNAL_TESTING in issue.labels:
        await _notify_to_pm(issue=issue, label=consts.label.INTERNAL_TESTING)
        await internal_testing(issue)
    
    if consts.label.REOPEN in issue.labels and issue.state == "opened":
        issue.state_event = 'reopen'
        issue.save()

        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")
        tester_teams = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        author_username = issue.author.get("username", "")

        if author_username in tester_teams:
            await reopen(notify_to, issue)
        await _notify_to_pm(issue=issue, label=consts.label.REOPEN)


    if issue.state == "closed" and "close" in action:
        notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_lead")
        await closed(notify_to=notify_to, issue=issue)
        await _notify_to_pm(issue=issue, label=consts.label.REOPEN)


async def _notify_to_dev(changes, issue):
    title      = issue.title
    issue_url  = issue.web_url
    issue_id   = issue.iid
    author_name = issue.author.get("name", "")
    project_id = str(issue.project_id)
    
    notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="dev_team")

    if "assignees" in changes:
        username = changes.get("assignees", {}).get("current", []).pop().get("username", "")
        if username in notify_to:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :    
                text = helper.get_assignee_task_message(
                    author_name=author_name,
                    to=username,
                    issue_id=issue_id,
                    issue_url=issue_url,
                    title=title
                )
                await telegram_handler.send_text(chat.get("id"), text=text)


async def _notify_to_pm(issue, label):
    title      = issue.title
    issue_url  = issue.web_url
    issue_id   = issue.iid
    author_name = issue.author.get("name", "")
    project_id = str(issue.project_id)

    notify_to = config.get_gitlab_username_by_role(project_id=project_id, role="pm_lead")
    for username in notify_to:
        chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
        if chat :
            text = helper.get_global_message(
                author_name=author_name,
                to=username,
                issue_id=issue_id,
                issue_url=issue_url,
                title=title,
                label=label
            )
            await telegram_handler.send_text(chat.get("id"), text=text)


async def dev_done(project, notify_to, issue, changes):
    title      = issue.title
    project_id = str(issue.project_id)
    issue_url  = issue.web_url
    issue_id   = issue.iid
    author_name = issue.author.get("name", "")
    current_assignee_ids = [assign["id"] for assign in issue.assignees]

    if "labels" in changes and consts.label.REOPEN not in issue.labels:
        tester_lead_gitlab_ids = []
        for username in notify_to:
            member_on_project = helper.get_project_member_by_gitlab_username(project=project, username=username)
            if member_on_project.get("username"):
                tester_lead_gitlab_ids.append(member_on_project.get("id", ""))
                
                chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=member_on_project.get("username"))
                if chat :
                    text = helper.get_global_message(
                        author_name=author_name,
                        to=username,
                        issue_id=issue_id,
                        issue_url=issue_url,
                        title=title,
                        label=consts.label.DEV_DONE
                    )
                    await telegram_handler.send_text(chat.get("id"), text=text)

        issue.assignee_ids = current_assignee_ids + tester_lead_gitlab_ids
        issue.save()

    if "assignees" in changes:
        msg = helper.get_assignee_task_message(
            author_name=author_name,
            to=username,
            issue_id=issue_id,
            issue_url=issue_url,
            title=title
        )

        await _notify_to_tester_team(assignees=issue.assignees, project_id=project_id, message=msg)

    if consts.label.REOPEN in issue.labels:
        msg = helper.get_after_reopen_message(
            author_name=author_name,
            to=username,
            issue_id=issue_id,
            issue_url=issue_url,
            title=title
        )
        await _notify_to_tester_team(assignees=issue.assignees, project_id=project_id, message=msg)


async def internal_testing(issue):
    issue.labels = [label for label in issue.labels if label != consts.label.REOPEN]
    issue.save()
    

async def reopen(notify_to, issue):
    title      = issue.title
    project_id = str(issue.project_id)
    issue_url  = issue.web_url
    issue_id   = issue.iid
    author_name = issue.author.get("name", "")
    current_assignees = [assign["username"] for assign in issue.assignees]
    
    for username in notify_to:
        if username in current_assignees:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :
                msg = helper.get_reopen_message(
                    author_name=author_name,
                    to=username,
                    issue_id=issue_id,
                    issue_url=issue_url,
                    title=title
                )
                await telegram_handler.send_text(chat.get("id"), text=msg)


async def _notify_to_tester_team(assignees, project_id, message: str):
    for assignee in assignees:
        username = assignee.get("username", "")

        registered_gitlab_usernames = config.get_gitlab_username_by_role(project_id=project_id, role="tester_team")
        if username in registered_gitlab_usernames:
            chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
            if chat :
                await telegram_handler.send_text(chat.get("id"), text=message)


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
            msg = helper.get_closed_message(
                author_name=author_name,
                to=username,
                issue_id=issue_id,
                issue_url=issue_url,
                title=title,
                mr_msg=mr_message
            )
            await telegram_handler.send_text(chat.get("id"), text=msg)
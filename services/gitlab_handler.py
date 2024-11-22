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

    gl = gitlab.Gitlab(url=url, private_token=token)
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_id)
    
    if issue.type == "ISSUE":
        await issue_handler(
            issue=issue
        )

    return json.loads(issue.to_json())


# assignee member to issue
async def issue_handler(**params):

    issue  = params.get("issue")
    project_id=issue.project_id

    notify_to = config.get_gitlab_member_by_label(project_id=project_id, labels=issue.labels)
    
    if "Dev Done" in issue.labels:
        await dev_done(notify_to, issue)

async def dev_done(notify_to, issue):
    
    title = issue.title
    project_id = issue.project_id
    issue_url  = issue.web_url
    issue_id   = issue.iid

    for username in notify_to:
        chat = helper.get_telegram_chat(project_id=project_id, gitlab_username=username)
        tele_user = chat.get("username")
        text=f"Hi {tele_user}, [Task #{issue_id}]({issue_url}) sudah *DEV-DONE*. Segera TEST ya \n\n---\n {title} "
        await telegram_handler.send_text(chat.get("id"), text=text)


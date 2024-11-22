import gitlab
import os
import json
from services import helper
from services import telegram_handler

async def updater(data: dict):
    url         = os.getenv("GITLAB_BASEURL")
    token       = os.getenv("GITLAB_TOKEN")
    project_id  = data.get('project', {}).get('id')
    issue_id    = data.get('object_attributes', {}).get('iid')
    labels      = data.get('object_attributes', {}).get('labels')
    author      = data.get('user', {})
    current_state = data.get('object_attributes', {}).get('state')
    current_assignee = data.get('assignees', [])

    config = helper.get_config_project(project_id)
    
    gl = gitlab.Gitlab(url=url, private_token=token)
    project = gl.projects.get(project_id)
    issue = project.issues.get(issue_id)

    all_members = project.members_all.list(get_all=True)
    all_members = [member.__dict__['_attrs'] for member in all_members]

    current_label_titles = [item["title"] for item in labels]
    to_members = [
        member for member in config["members"] 
        if any(label in current_label_titles for label in member["labels"])
    ]

    gitlab_usernames = [item["gitlab_username"] for item in to_members]
    # telegram_usernames = [item["telegram_username"] for item in config["members"]]

    await assignee_handler(
        config=config, 
        gitlab_usernames=gitlab_usernames, 
        all_members=all_members, 
        issue=issue,
        current_assignee=current_assignee,
        current_label_titles=current_label_titles,
        current_state=current_state,
        author= author
    )


# assignee member to issue
async def assignee_handler(**params):

    config           = params.get("config")
    gitlab_usernames = params.get("gitlab_usernames")
    all_members      = params.get("all_members")
    issue            = params.get("issue")
    author           = params.get("author")
    current_assignee = params.get("current_assignee")
    current_state    = params.get("current_state")
    current_label_titles = params.get("current_label_titles")

    assign_to = [
        member for member in all_members
        if member["username"] in gitlab_usernames
    ]
    assign_to_ids = [assign["id"] for assign in assign_to]
    current_assignee_ids = [assign["id"] for assign in current_assignee]

    if current_state == "closed":
        # Remove trigered
        issue = await closed(
            issue=issue, 
            author=author, 
            current_assignee_ids=current_assignee_ids, 
            config=config, 
            all_members=all_members
        )

    elif "Re Open" in current_label_titles :
        issue = await re_open(
            issue=issue, 
            author=author,
            config=config,
            current_assignee_ids=current_assignee_ids
        )

    elif "Dev Done" in current_label_titles :
        issue = await dev_done(
            config=config, 
            issue=issue, 
            author=author, 
            current_assignee_ids=current_assignee_ids,
            all_members=all_members
        )

    else:
        issue.assignee_ids = current_assignee_ids + assign_to_ids
 
    issue.save()
    return current_assignee_ids + assign_to_ids


async def closed(issue, current_assignee_ids, config, all_members, author):
    assignee_ids = [item for item in current_assignee_ids if item != author["id"]]

    gitlab_users   = [member["gitlab_username"] for member in config["members"] if member["role"] == "dev_lead"]
    
    dev_lead_ids = [
        member["id"] for member in all_members
        if member["username"] in gitlab_users
    ]
    issue.assignee_ids = assignee_ids + dev_lead_ids
    issue.labels = []

    for username in gitlab_users:
        chat = helper.get_telegram_chat(config["project_id"], username)
        tele_user = chat.get("username")
        await telegram_handler.bot.send_message(chat.get("id"), f"Hi @{tele_user}, Ada task yang diclose dengan ID 123. Segra lakukan merge ya")

    return issue


async def re_open(issue, author, current_assignee_ids, config):
    current_assignee_ids.remove(author["id"])
    telegram_users   = [member for member in config["members"] if member["role"] == "dev_lead"]

    issue.assignee_ids = current_assignee_ids

    return issue


async def dev_done(issue, author, config, current_assignee_ids, all_members):
    members = [member["gitlab_username"] for member in config["members"] if member["role"] == "tester_lead"]
    tester_lead_ids = [
        member["id"] for member in all_members
        if member["username"] in members
    ]

    current_assignee_ids.remove(author["id"])
    issue.assignee_ids = current_assignee_ids + tester_lead_ids

    return issue

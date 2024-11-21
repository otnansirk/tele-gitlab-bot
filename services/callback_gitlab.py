import gitlab
import os
import json
from services import helper


def callback_gitlab(data: dict):
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

    return {
        "to_members": assignee_handler(
            config=config, 
            gitlab_usernames=gitlab_usernames, 
            all_members=all_members, 
            issue=issue,
            current_assignee=current_assignee,
            current_label_titles=current_label_titles,
            current_state=current_state,
            author= author
        ),
        "defined_members": helper.get_config_project(project_id),
        "members": all_members,
        "data": project.to_json(),
        "meta": {
            "code": "ok",
            "message": "OK"
        }
    }

# assignee member to issue
def assignee_handler(**params):
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
        assignee_ids = [item for item in current_assignee_ids if item != author["id"]]
        
        members = [member["gitlab_username"] for member in config["members"] if member["role"] == "dev_lead"]
        dev_lead_ids = [
            member["id"] for member in all_members
            if member["username"] in members
        ]
        issue.assignee_ids = assignee_ids + dev_lead_ids

    elif "Re Open" in current_label_titles :
        current_assignee_ids.remove(author["id"])
        issue.assignee_ids = current_assignee_ids

    else:
        issue.assignee_ids = current_assignee_ids + assign_to_ids
 
    issue.save()

    return current_assignee_ids + assign_to_ids


def label_handler(issue, current_state):

    if(current_state == "closed"):
        issue.labels = []
        issue.save()

    return issue.labels
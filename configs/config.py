import json


def get(project_id: str):
    file = open(f"configs/projects/{project_id}.json")
    return json.load(file)

def get_gitlab_member_by_label(project_id: str, labels: str):
    config = get(project_id)
    for label in labels:
        role = config.get("notify_to", {}).get(label, "")
        members_gitlab_by_label = config.get("gitlab_role_username_members", {}).get(role, [])
        return members_gitlab_by_label
    
    return []

def get_labels(project_id: str):
    config = get(project_id)
    data = config.get("notify_to", {})
    return [key for key, value in data.items()]

def get_gitlab_username_by_role(project_id: str, role: str):
    config = get(project_id)
    return config.get("gitlab_role_username_members", {}).get(role, [])


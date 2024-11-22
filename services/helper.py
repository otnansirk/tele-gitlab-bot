import json

def get_config_project(id: str):
    file = open(f"configs/projects/{id}.json")
    return json.load(file)

def get_telegram_chat(project_id: str, gitlab_username: str):
    file = open(f".chatids/{project_id}/{gitlab_username}.txt")
    chat = file.read().split(":")

    return {
        "id": chat[0],
        "username": chat[1],
        "gitlab_username": chat[2],
    }

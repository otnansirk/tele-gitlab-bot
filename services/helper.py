import json

def get_config_project(id: str):
    file = open(f"configs/projects/{id}.json")
    return json.load(file)

def get_telegram_chat(project_id: str, username: str):
    file = open(f".chatids/{project_id}/{username}.txt")
    chat = file.read().split(":")

    return {
        "id": chat[0],
        "username": chat[1],
    }

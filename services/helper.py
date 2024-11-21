import json

def get_config_project(id: str):
    file = open(f"configs/projects/{id}.json")
    return json.load(file)

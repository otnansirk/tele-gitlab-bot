import gitlab
import os

def callback_gitlab(data: dict):
    url = os.getenv("GITLAB_BASEURL")
    token = os.getenv("GITLAB_TOKEN")
    project_id = data.get('project', {}).get('id')

    gl = gitlab.Gitlab(url=url, private_token=token)
    project = gl.projects.get(project_id)

    return {
        "data": project.to_json(),
        "meta": {
            "code": "ok",
            "message": "OK"
        }
    }

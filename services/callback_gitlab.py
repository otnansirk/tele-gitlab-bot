import gitlab
import os

def callback_gitlab(request):
    url = os.getenv("GITLAB_BASEURL")
    token = os.getenv("GITLAB_TOKEN")
    projectID = os.getenv("GITLAB_PROJECT_ID")

    gl = gitlab.Gitlab(url=url, private_token=token)
    project = gl.projects.get(projectID)

    return {
        "data": request,
        "meta": {
            "code": "ok",
            "message": "OK"
        }
    }

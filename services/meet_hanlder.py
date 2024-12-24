from services import telegram_handler
from core.db.database import Database

async def generate(chat_id: str, title: str = "Meeting", message: str = "", meeting_name: str = "Urgent-Meeting"):
    base_url = "https://meet.jit.si/"
    meet_url = base_url + meeting_name

    text = f"""
{title}
Link : {meet_url}
"""

    await telegram_handler.send_text(chat_id=chat_id, text=text)

    usernames = message.split(" @")
    db = Database()
    for username in usernames:
        tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).execute()
        if len(tele_account.data):
            chat_id = tele_account.data[0].get("chat_id")
            await telegram_handler.send_text(chat_id=chat_id, text=text)

    return "NO"

async def my_teams(chat_id: str, username: str): 
    db = Database()
    tele_account = db.fetch(table_name="telegram_account").select("*").eq("username", username).execute()
    if len(tele_account.data):
        project_id = tele_account.data[0].get("gitlab_project_id", "")

        teams_account = db.fetch(table_name="telegram_account").select("*").eq("gitlab_project_id", project_id).execute()
        tele_user_teams = ""
        for index, user in enumerate(teams_account.data, start=1):
            username = user.get("username", "")
            gitlab_username = user.get("gitlab_username", "")
            tele_user_teams += f"{index}. @{username} - {gitlab_username} \n"

        text = f"*- Your Team -*\n{tele_user_teams}"
        await telegram_handler.send_text(chat_id=chat_id, text=text)

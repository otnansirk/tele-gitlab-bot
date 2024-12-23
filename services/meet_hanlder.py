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
        

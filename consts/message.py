WELCOME_MESSAGE = """
👋 **Welcome to the Hanoman Devdsi!**

This bot helps you manage your GitLab projects efficiently.
"""

HELP_MESSAGE = """
🤖 *Hanoman Commands*

❕ *Join GitLab Notifications*  
  `/join GITLAB_PROJECT_ID:GITLAB_USERNAME`
   _Subscribe to notifications for a specific GitLab project._
   Example : `/join 58:suta`

❕ *View Task Details*  
   `/taskd GITLAB_ISSUE_ID`  
   _Get details about a specific task in a project._
   Example : `/taskd 123`

❕ *View My Tasks*
   `/mytask`
   _See all tasks assigned to your GitLab username._

❕ *Surprise me*
   `/surpriseme`
   _I will send you random memes that can boost your mood._

❕ *Show all team*
   `/ourteam`
   _Will show all team on project._

❕ *Generate daily meeting*
   `/meet generate or @TELEGRAM_USER_NAME`
   _Will send daily meeting invitation url._
   Example 1: `/meet generate`
   Example 2: `/meet @teleuser1 @teleuser2`

❕ *Show holidays*
   `/holiday`
   _Will show holiday in last 30 days._

❕ *Meme for me*
   `meme SAY_WHAT_YOU_WANT`
   _I will send you memes like you said._

❕ *External Webhook*
   1. `https://socialist-amber-bangsa-digital-221484cb.koyeb.app/external-webhook?teleuser=@teleuser,@teleuser1`
   2. `https://hanoman.digitalsekuriti.id/external-webhook?teleuser=@teleuser,@teleuser1`
   _Use hanoman as the recipient of the webhook._
"""
# DEV_DSI_BOT

## Warning !!! .env file configuration
1. **For the key `GITLAB_PROJECT_<GITLAB_PROJECT_ID>`:**
   - Example: `GITLAB_PROJECT_58`
   - Please replace `<GITLAB_PROJECT_ID>` with the actual `projectId` that has been registered in the `GITLAB_PROJECT_IDS` key.

2. **Value Format:**
   - The value for `GITLAB_PROJECT_<GITLAB_PROJECT_ID>` must be in JSON format. Specifically, it should be:
      - **JSON oneline** format (a single-line JSON representation).
      - Do not change the structure of the value for `GITLAB_PROJECT_<GITLAB_PROJECT_ID>`. Only replace the   `<GITLAB_PROJECT_ID>` placeholder with the appropriate value.

3. **Allowed Changes:**
   - The only modification allowed is to replace the placeholder `< >` with the corresponding `projectId`. Any other changes to the structure or contents of the value are not permitted.

4. **Multi Project**
   - You can add more than one project


## Usage
1. Create virtual env `python3 -m venv venv`
2. Activate virtual env `source venv/bin/activate`
3. pip install -r requirments.txt
4. Rename `.env.example` to `.env` and adjust to yous need.
6. Run `fastapi dev main.py` for development and `uvicorn main:app --host 0.0.0.0` for production


## Flow Notif telegram : 

1. Issue -> Open -> assigne to dev team 
            -> notify : dev_team -> notify : dev_team_base_on_assignee

2. Issue -> Dev Done 
            -> notify : tester_lead -> assign to team -> notify : tester_team_base_on_assignee

3. Issue -> Internal Testing
            -> Remove label : Re Open

4. Issue -> Internal Testing -> Open (state)
                                -> Add label : Re Open
                                -> Notify : dev_team_base_on_assignee

5. Issue -> Internal Testing -> Close (state)
                                -> Remove label : Re Open
                                -> Notify : dev_team_lead



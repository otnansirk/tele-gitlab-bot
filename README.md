# DEV_DSI_BOT

## Warning !!!
1. Do not change the data structure in the file `configs/projects/<Gitlab_Project_ID>.json`
   Only value with `< >` can be changed.

## Usage
1. Create virtual env `python3 -m venv venv`
2. Activate virtual env `source venv/bin/activate`
3. pip install -r requirments.txt
4. Rename `.env.example` to `.env` and adjust to yous need. 
5. Rename `configs/projects/<Gitlab_Project_ID>.json.example` to `configs/projects/<Gitlab_Project_ID>.json`. and adjust  <Gitlab_Project_ID> to your gitlab Project_ID. 
6. Run `fastapi dev main.py` for development and `uvicorn main:app --host 0.0.0.0` for production


Flow Notif telegram : 

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



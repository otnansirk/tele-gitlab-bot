# DEV_DSI_BOT

## Warning !!!
1. Do not change the data structure in the file `configs/projects/<Gitlab_Project_ID>.json`

## Usage
1. Create virtual env `python3 -m venv venv`
2. Activate virtual env `source venv/bin/activate`
3. pip install -r requirments.txt
4. Rename `.env.example` to `.env` and adjust to yous need. 
5. Rename `configs/projects/<Gitlab_Project_ID>.json.example` to `configs/projects/<Gitlab_Project_ID>.json`. and adjust  <Gitlab_Project_ID> to your gitlab Project_ID. 
6. Run `fastapi dev main.py`
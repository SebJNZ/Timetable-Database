import requests, os, subprocess, json
from dotenv import load_dotenv
from datetime import datetime
from mailer import emailer

load_dotenv()

TOPIC = "lectures" # Change this to your topics name
MOBILE_SERVER = f"https://ntfy.yourserver.ts.net/{TOPIC}"
LAPTOP_SERVER = f"https://ntfy.yourserverts.net/{TOPIC}_laptop"
HEADERS = {
    "Authorization": os.getenv("NTFY_API_KEY")
}
ADVANCE_MINUTES = 25
TIMETABLE = "database/database.json"
TIMETABLE_DATABASE_URL = "http://127.0.0.1:80" # No trailing forward slash (/)

print("pinging phone")
phone = subprocess.run(["tailscale", "ping", "--c", "1", "100.107.245.15"]).returncode
print("pinging laptop")
laptop = subprocess.run(["tailscale", "ping", "--c", "1", "100.123.27.49"]).returncode
print("pinged laptop")

now = datetime.now()

today = now.strftime("%A").lower()

def message(data, server):
    response = requests.post(server, data=data, headers=HEADERS)
    print(response.status_code)
    print(response.text)

def load_lectures(day):
    td_headers = {
        "Authorization": os.getenv("TDATABASE_API_KEY"),
        "Accept": "application/json"
    }
    timetable_api = f"{TIMETABLE_DATABASE_URL}/api/v1/timetable/{day}"
    response = requests.get(timetable_api, headers=td_headers)
    return response.json()

def get_name():
    td_headers = {
        "Authorization": os.getenv("TDATABASE_API_KEY"),
        "Accept": "application/json"
    }
    timetable_api = f"{TIMETABLE_DATABASE_URL}/api/v1/user/name"
    response = requests.get(timetable_api, headers=td_headers)
    return response.text

def read_lazy_data():
    with open("lazy.json", 'r') as lazy_data:
        data = json.load(lazy_data)
        lazy_data.close()
        return data["course_code"]
        
def add_lazy_data(lecture_id):
    with open("lazy.json", 'r+') as lazy_data:
        data = json.load(lazy_data)
        data["course_code"].append(lecture_id)
        lazy_data.seek(0)
        json.dump(data, lazy_data, indent=4)
        lazy_data.truncate()
        lazy_data.close()
        
def remove_lazy_data(lecture_id):
    with open("lazy.json", 'r+') as lazy_data:
        data = json.load(lazy_data)
        data["course_code"].remove(lecture_id)
        lazy_data.seek(0)
        json.dump(data, lazy_data, indent=4)
        lazy_data.truncate()
        lazy_data.close()
    
current_lectures = []

for lecture in load_lectures(today):
    start_hour, start_minute = map(int, lecture["start_time"].split(":"))
    start_dt = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    if 0 <= (start_dt - now).total_seconds() / 60 <= ADVANCE_MINUTES:
        current_lectures.append(lecture["lecture_id"])
        if lecture["lecture_id"] in read_lazy_data():
            continue
        add_lazy_data(lecture["lecture_id"])
        name = get_name()
        message_txt = f"Lecture '{lecture['course']}' starts at {lecture['start_time']} in {lecture['location']}"
        if phone != 1:
            message(message_txt, MOBILE_SERVER)
        else:
            if laptop == 0:
                message(message_txt, LAPTOP_SERVER)
            emailer(lecture, laptop, TIMETABLE_DATABASE_URL, name)

for lecture in read_lazy_data():
    print("Lecture: ", lecture)
    if lecture not in current_lectures:
        print("Removing....", lecture)
        remove_lazy_data(lecture)
        
print("done")
import json, time, secrets, re
from datetime import timedelta
from userdatabase import user_days, user_times
from urllib.parse import urlparse

# New Model
NM_DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
NM_DAYS_C = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

#### IMPORTANT TO USE ####
def check_time_safety(dtime):
    try:
        time.strptime(dtime, '%H:%M')
        return True
    except ValueError:
        return False

def validate_times(database_times):
    for dtime in database_times:
        check_time_safety(dtime)
        
def convert_time_h(data_time):
    safe = check_time_safety(data_time)
    if safe == False:
        return data_time
    time_hour, time_minute = map(int, data_time.split(':'))
    if time_hour < 12:
        return f"{data_time}am"
    if time_hour == 12:
        return f"{data_time}pm"
    if time_hour > 12:
        time_hour -= 12
        if time_minute == 0:
            time_minute = "00"
        return f"{time_hour}:{time_minute}pm"
    return data_time

def clean_morning_24h(time):
    time_hour, time_minute = map(int, time.split(':'))
    if time_hour < 10:
        if time_minute == 0:
            time_minute = "00"
        return [True, f"{time_hour}:{time_minute}"]
    return [False]
        
##########################


def read_database(userid):
    with open(f"db/user_timetables/{userid}.json", 'r') as database:
        return json.load(database)
        
def modify_database(data, day, userid, method):
    with open(f"db/user_timetables/{userid}.json", 'r+') as database:
        data_file = json.load(database)
        if method == "add":
            try:
                data_file[day].append(data)
            except KeyError:
                database.close()
                return None # Escape with a 404 or something, as this should be a touchable data without user modifications. 
        elif method == "keyadd":
            for day_key in data:
                data_file[day_key] = []
        else:
            try:
                data_file[day].pop(data)
            except IndexError:
                return None # Escape with a 404 or something, as this should be a touchable data without user modifications. 
        database.seek(0)
        json.dump(data_file, database, indent=4)
        database.truncate()
        database.close()
        
def read_day(day, userid):
    usersdays = user_days(userid)
    if day.lower().strip() not in usersdays:
        return None
    data = read_database(userid)
    return data[day]
        
def read_day_wiper(day, userid):
    data = read_database(userid)
    return data[day]

def load_lecture(lecture_id, userid):
    data = lecture_handler(userid, lecture_id, False)
    if data == None:
        return None
    for lecture in read_day(data[0], userid):
        if lecture["lecture_id"] == lecture_id:
            return lecture
    return None
    
def get_time_difference(start, end, reverse, provide_insight):
    try:
        start_hour, start_minute = map(int, start.split(':'))
        end_hour, end_minute = map(int, end.split(':'))
        start = timedelta(hours=start_hour, minutes=start_minute)
        end = timedelta(hours=end_hour, minutes=end_minute)
        if reverse:
            total = int((end - start).total_seconds())
        else:
            total = int((end - start).total_seconds())
        hours = total // 3600
        minutes = (total % 3600) // 60
        if provide_insight:
            if hours == 0:
                return [hours, minutes, True, True]
            else:
                return [hours, minutes, False, True]
        else:
            return f"{hours}:{minutes:02d}"
    except ValueError:
        return False
    
# Function used codes, so make sure that you replace them with some value.
# As said above, generate a new value for code, so that we know how to modify it in the future.
# We need to make sure that this includes the breaks that the users have, if they are a break it needs minimum to be in the correct place. 
def load_data(userid, users_times, users_days, user_breaks):
    data = {}
    for time in users_times:
        data[time] = []
        if time in user_breaks:
            break_lengths = get_break_length(users_times, user_breaks)
            for _ in range(len(users_days)):
                if break_lengths[f"break_{time}"][3]:
                    if break_lengths[f"break_{time}"][2]:
                        data[time].append({
                                "course": f"{break_lengths[f"break_{time}"][1]}-minute Break",
                                "day": "",
                                "start_time": "",
                                "end_time": "",
                                "location": "",
                                "blank": True,
                                "room": "",
                                "room_number": "",
                                "lecture_id": ""
                            })
                    else:
                        data[time].append({
                                "course": f"{break_lengths[f"break_{time}"][0]}-hour {break_lengths[f"break_{time}"][1]}-minute Break",
                                "day": "",
                                "start_time": "",
                                "end_time": "",
                                "location": "",
                                "blank": True,
                                "room": "",
                                "room_number": "",
                                "lecture_id": ""
                            })
                else:
                    data[time].append({
                            "course": "Break",
                            "day": "",
                            "start_time": "",
                            "end_time": "",
                            "location": "",
                            "blank": True,
                            "room": "",
                            "room_number": "",
                            "lecture_id": ""
                        })
        else:
            for day in users_days:
                day_has_added = False
                day_data = read_day(day, userid)
                for course in day_data:
                    if course["start_time"] == time:
                        data[time].append(course)
                        day_has_added = True
                if day_has_added == False:
                    data[time].append({
                        "course": "",
                        "day": day.lower(),
                        "start_time": time,
                        "end_time": "",
                        "location": "",
                        "blank": True,
                        "room": "",
                        "room_number": "",
                        "lecture_id": ""
                    })
    return data

def find_duplicates(name, user_id):
    database = read_database(user_id)
    courses = []
    for day in user_days(user_id):
        for data in database[day]:
            if data["course"] == name:
                courses.append(data["lecture_id"])
    return courses

def add_duplicate(original_lid, new_lid, userid, blank_serializer):
    original_data = load_lecture(original_lid, userid)
    
    new_data = blank_serializer.loads(new_lid)
    
    new_lid = generate_lecture_id(userid)
    
    users_times = user_times(userid)
    
    modify_database({
        "course": original_data["course"],
        "name": original_data["name"],
        "description": original_data["description"],
        "day": NM_DAYS_C[new_data[0]],
        "start_time": new_data[1],
        "end_time": get_lecture_length(new_data[1], users_times["times"], users_times["duration"]),
        "end_time_difference": "",
        "location": original_data["location"],
        "blank": False,
        "room": original_data["room"],
        "room_number": original_data["room_number"],
        "lecture_id": new_lid,
        "own_modified": original_data["own_modified"],
        "vikunja": original_data["vikunja"]
    }, NM_DAYS[new_data[0]], userid, "add")
    
    lecture_handler_adder(new_lid, userid, NM_DAYS[new_data[0]], new_data[1])
    
    
def get_lecture_index(lecture_id, day, userid):
    data = load_lecture(lecture_id, userid)
    database = read_database(userid)
    return database[day].index(data)

def delete_lecture(lecture_id, userid):
    data = lecture_handler(userid, lecture_id, False)
    modify_database(get_lecture_index(lecture_id, data[0], userid), data[0], userid, "remove")
    lecture_handler_remove(lecture_id, userid)
    

def modify_lecture(lecture_id, userid, feature, new_data):
    day = lecture_handler(userid, lecture_id, False)[0]
    index = get_lecture_index(lecture_id, day, userid)
    with open(f"db/user_timetables/{userid}.json", 'r+') as database:
        data_file = json.load(database)
        data_file[day][index][feature] = new_data
        if feature == "end_time" or feature == "start_time":
            data_file[day][index]["end_time_difference"] = get_time_difference(data_file[day][index]["start_time"], data_file[day][index]["end_time"], False, False)
        database.seek(0)
        json.dump(data_file, database, indent=4)
        database.truncate()
        database.close()
    

def check_lecture_existance(userid, lecture_id):
    for _ in user_times(userid):
        for day in user_days(userid):
            day_data = read_day(day, userid)
            for course in day_data:
                if course["lecture_id"] == lecture_id:
                    return True
    return False

def generate_lecture_id(userid):
    new_id = secrets.token_urlsafe(6)
    if check_lecture_existance(userid, new_id):
        while check_lecture_existance(userid, new_id):
            new_id = secrets.token_urlsafe(6)
    return new_id

    
def change_casing(day_data):
    new_data = []
    for day in day_data:
        new_data.append(NM_DAYS_C[NM_DAYS.index(day)])
    return new_data

def lecture_handler(userid, lecture_id, capital_day):
    with open(f"db/user_timetables/{userid}.dict.json", 'r') as database:
        data = json.load(database)
        try:
            if capital_day:
                data_var = data[lecture_id]
                data_list = [NM_DAYS_C[NM_DAYS.index(data_var[0])], data_var[1]]
                return data_list
            return data[lecture_id]
        except KeyError:
            return None
        
def lecture_handler_adder(lecture_id, userid, day, start_time):
    with open(f"db/user_timetables/{userid}.dict.json", 'r+') as database:
        data = json.load(database)
        database.seek(0)
        data[lecture_id] = [day, start_time]
        json.dump(data, database, indent=4)
        database.truncate()
        
def lecture_handler_remove(lecture_id, userid):
    with open(f"db/user_timetables/{userid}.dict.json", 'r+') as database:
        data = json.load(database)
        database.seek(0)
        data.pop(lecture_id)
        json.dump(data, database, indent=4)
        database.truncate()
        database.close()
        
        
def clean_data(data, day, userid, blank_serializer):
    times = user_times(userid)
    
    time_dict = {}
    
    
    for time in times["times"]:
        time_dict[time] = []
    for break_var in times["breaks"]:
        time_dict[break_var] = []
    
    for time_var in times["times"]:
        found_match = False
        if time_var in times["breaks"]:
            time_dict[time_var].append({
                        "course": data[time_var][0]["course"],
                        "day": NM_DAYS_C[NM_DAYS.index(day)],
                        "start_time": time_var,
                        "end_time": "",
                        "location": "",
                        "blank": True,
                        "room": "",
                        "room_number": "",
                        "lecture_id": generate_blank_id(day, time_var, blank_serializer)
                    })
        else:
            for time_data in data[time_var]:
                if time_data["blank"] == True:
                    found_match = False
                      
                elif time_data["day"].lower() == day.lower():
                    time_dict[time_var].append(time_data)
                    found_match = True
                    
            if found_match == False:
                time_dict[time_var].append({
                        "course": "",
                        "day": NM_DAYS_C[NM_DAYS.index(day)],
                        "start_time": time_var,
                        "end_time": "",
                        "location": "",
                        "blank": True,
                        "room": "",
                        "room_number": "",
                        "lecture_id": generate_blank_id(day, time_var, blank_serializer)
                    })
                
    return time_dict

def generate_blank_id(day, time, blank_serializer):
    day = NM_DAYS.index(day.lower())
    return blank_serializer.dumps([day, time])

def calculate_end(original_time, difference, user_tb):
    oh, om = map(int, original_time.split(':'))
    dh, dm = map(int, difference.split(':'))

    h, m = divmod(
        (timedelta(hours=oh, minutes=om)
         + timedelta(hours=dh, minutes=dm)
         - timedelta(minutes=user_tb)
        ).seconds,
        3600
    )

    return f"{h}:{m//60:02d}"

def get_lecture_length(time, users_times, duration):
    index = users_times.index(time) + 1
    if index == len(users_times):
        if len(users_times) < 2:
            print("ERROR: NOT ENOUGH ITEMS IN USER_TIMES, LECTURE LENGTH IS SET TO 0 BECAUSE OF THIS.")
            return time
        return calculate_end(time, get_time_difference(users_times[0], users_times[1], False, False), duration)
    return calculate_end(time, get_time_difference(time, users_times[index], False, False), duration)
    
    
def get_break_length(time, breaks):
    a = {
            "breaks": [
                
            ]
        }
    for break_val in breaks:
        if len(time) -1 < (time.index(break_val)):
            a[f"break_{break_val}"] = [0, 0, False, False]
            a["breaks"].append(break_val)
        else:
            new_value = get_time_difference(break_val, time[time.index(break_val) + 1], True, True)
            if new_value == False:
                a[f"break_{break_val}"] = [0, 0, False, False]
                a["breaks"].append(break_val)
            else:
                a[f"break_{break_val}"] = new_value
            a["breaks"].append(break_val)
    return a

def new_user_setup(userid):
    with open(f"db/user_timetables/{userid}.json", 'w') as database:
        user_data = {}
        for day in NM_DAYS:
            user_data[day] = []
        json.dump(user_data, database, indent=4)
        database.truncate()
        database.close()
    with open(f"db/user_timetables/{userid}.dict.json", 'w') as database:
        json.dump({}, database, indent=4)
        database.truncate()
        database.close()

def move_specialist_data(movedata, blank_serializer):
    for time in movedata:
        for data in movedata[time]:
            if data["blank"] == True:
                if "break" in data["course"].lower():
                    continue
                data["lecture_id"] = generate_blank_id(data["day"], data["start_time"], blank_serializer)
    return movedata

def generate_tids(time_data, blank_serializer):
    for ttime in time_data["times"]:
        if ttime in time_data["breaks"]:
            time_data["times"].remove(ttime)
    tids = {
        "times": [],
        "breaks": []
    }
    for time in time_data["times"]:
        tids["times"].append(blank_serializer.dumps(time))
    for time in time_data["breaks"]:
        tids["breaks"].append(blank_serializer.dumps(time))
    return tids

def get_new_index(times_list, newtime):
    newt_hour, newt_minute = map(int, newtime.split(':'))
    previous = None
    for looptime in times_list:
        time_hour, time_minute = map(int, looptime.split(':'))
        
        
        if time_hour > newt_hour:
            if previous != None:
                times_list.insert((times_list.index(previous) + 1), newtime)
            else:
                times_list.insert(0, newtime)
            break
        elif time_hour == newt_hour:
            if time_minute > newt_minute:
                if previous != None:
                    times_list.insert((times_list.index(looptime)), newtime)
                else:
                    times_list.insert(0, newtime)
                break
            if time_minute == newt_minute:
                break
        
        previous = looptime
    if newtime not in times_list:
        times_list.append(newtime)
    return times_list

def check_local_keys(userid, new_keys):
    user_data = read_database(userid)
    to_add = []
    for key in new_keys:
        if key not in user_data:
            to_add.append(key)
    modify_database(to_add, "", userid, "keyadd")
    
def check_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.fullmatch(pattern, email):
        return True
    else:
        return False
    
def check_url(url):
    try:
        result = urlparse(url)
        return True
    except AttributeError:
        return False
    
def wipe_day(userid, day):
    data = read_day_wiper(day, userid)
    for lecture in data:
        lecture_handler_remove(lecture["lecture_id"], userid)
    with open(f"db/user_timetables/{userid}.json", 'r+') as database:
        data = json.load(database)
        database.seek(0)
        data[day] = []
        json.dump(data, database, indent=4)
        database.truncate()
        database.close()
        
def wipe_time(userid, time, times):
    data = load_data(userid, times["times"], user_days(userid), times["breaks"])
    timedata = data[time]
    lectures = []
    for lecture in timedata:
        if lecture["blank"] == True:
            continue
        lectures.append(lecture["lecture_id"])
    for lecture in lectures:
        delete_lecture(lecture, userid)
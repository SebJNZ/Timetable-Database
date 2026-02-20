import sqlite3, base64, json

CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '_']
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
DAYS_C = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
DATABASE_INDEX = {
    "userid": 0,
    "username": 1,
    "password": 2,
    "apikey": 3,
    "days": 4,
    "times": 5,
    "breaks": 5,
    "duration": 5,
    "email": 6,
    "locations": 7,
    "ntfy": 8,
    "config": 9
}

def add_user(username, password, days, times, email, locations, config):
    connection = None
    try:
        connection = sqlite3.connect("db/users.db", timeout=10)
        with connection:
            connection.execute("INSERT INTO `users` (`username`, `password`, `days`, `times`, `email`, `locations`, `config`) VALUES (?, ?, ?, ?, ?, ?, ?)", (username, password, days, times, email, locations, config))
        return True
    except sqlite3.IntegrityError:
        print(f"Error: The username '{username}' is already taken.")
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally: # Close connection to prevent leaks.
        if connection:
            connection.close()
            
def read_data(id, field):
    try:
        connection = sqlite3.connect("db/users.db", timeout=10)
        with connection:
                if field == "userid":
                    cursor = connection.execute("SELECT * FROM users WHERE userid = ?", (id,))
                elif field == "username":
                    cursor = connection.execute("SELECT * FROM users WHERE username COLLATE NOCASE = ?", (id,))
                elif field == "apikey":
                    cursor = connection.execute("SELECT * FROM users WHERE apikey COLLATE NOCASE = ?", (id,))
                else:
                    connection.close()
                    return False
                data = cursor.fetchall()
                if not data:
                    return False
                return data[0]
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally: # Close connection to prevent leaks.
        if connection:
            connection.close()
            
def change_apikey(id, value):
    try:
        connection = sqlite3.connect("db/users.db", timeout=10)
        with connection:
            connection.execute("UPDATE users SET apikey = ? WHERE userid = ?", (value, id))
        return True
    except sqlite3.IntegrityError:
        print(f"Error: The apikey '{value}' is already taken.")
        return False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally: # Close connection to prevent leaks.
        if connection:
            connection.close()

def username_check(username):
    for character in username:
        if character not in CHARACTERS:
            return True
    return False

def load_udata(userid, data_type):
    data_types = ["days", "times", "breaks", "duration"]
    special_dtypes = ["apikey", "locations", "email", "ntfy", "config"]
    database_d = read_data(userid, "userid")
    if type(data_type) is list:
        data = []
        for dtype in data_type:
            if dtype in data_types:
                if data_type != "days":
                    decoded_data = decoder(database_d[DATABASE_INDEX[dtype]])
                    data.append(decoded_data[dtype])
                else:
                    decoded_data = decoder(database_d[DATABASE_INDEX["days"]])
                    data.append(decoded_data)
        return data
    if data_type not in data_types and data_type not in special_dtypes:
        return None
    if data_type != "days" and data_type not in special_dtypes:
        decoded_data = decoder(database_d[DATABASE_INDEX[data_type]])
        return decoded_data[data_type]
    elif data_type == "apikey":
        return database_d[DATABASE_INDEX["apikey"]]
    elif data_type == "email":
        return database_d[DATABASE_INDEX["email"]]
    elif data_type == "locations":
        decoded_data = decoder(database_d[DATABASE_INDEX["locations"]])
        return decoded_data
    elif data_type == "ntfy":
        if database_d[DATABASE_INDEX["ntfy"]] == None:
            return None
        decoded_data = decoder(database_d[DATABASE_INDEX["ntfy"]])
        return decoded_data
    elif data_type == "config":
        if database_d[DATABASE_INDEX["config"]] == None:
            return None
        decoded_data = decoder(database_d[DATABASE_INDEX["config"]])
        return decoded_data
    else:
        decoded_data = decoder(database_d[DATABASE_INDEX["days"]])
        return decoded_data

def user_days(userid):
    databasedays = load_udata(userid, "days")
    usersdays = []
    for uday in databasedays:
        usersdays.append(DAYS[uday])
    return usersdays
    
def user_times(userid):
    users_data = load_udata(userid, ["times", "breaks", "duration"])
    return {
        "breaks": users_data[1],
        "times": users_data[0],
        "duration": users_data[2]
    }
    
def days_setup(days):
    new_days = json.dumps(days).encode('utf-8')
    new_days_b64 = base64.b64encode(new_days)
    return new_days_b64
    
def times_setup(times, breaks, duration):
    new_data = {
        "times": times,
        "breaks": breaks,
        "duration": duration
    }
    new_data_json = json.dumps(new_data).encode('utf-8')
    new_data_b64 = base64.b64encode(new_data_json)
    return new_data_b64

def locations_setup(locations):
    new_locations = json.dumps(locations).encode('utf-8')
    new_locations_b64 = base64.b64encode(new_locations)
    return new_locations_b64
    
def decoder(data):
    decoded_data = base64.b64decode(data).decode('utf-8')
    return json.loads(decoded_data)

def modify_user_database(userid, b64data, data_type):
    try:
        connection = sqlite3.connect("db/users.db", timeout=10)
        with connection:
            if data_type == "time":
                connection.execute("UPDATE users SET times = ? WHERE userid = ?", (b64data, userid))
            if data_type == "day":
                connection.execute("UPDATE users SET days = ? WHERE userid = ?", (b64data, userid))
            if data_type == "email":
                connection.execute("UPDATE users SET email = ? WHERE userid = ?", (b64data, userid))
            if data_type == "locations":
                connection.execute("UPDATE users SET locations = ? WHERE userid = ?", (b64data, userid))
            if data_type == "ntfy":
                connection.execute("UPDATE users SET ntfy = ? WHERE userid = ?", (b64data, userid))
            if data_type == "config":
                connection.execute("UPDATE users SET config = ? WHERE userid = ?", (b64data, userid))
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally: # Close connection to prevent leaks.
        if connection:
            connection.close()

def modify_dt_data(userid, data_type, timeday, method, get_new_index):
    time_data = ["times", "breaks", "duration"]
    if data_type in time_data:
        data = user_times(userid)
        try:
            if method == "remove":
                data[data_type].remove(timeday)
            else:
                data[data_type] = get_new_index(data[data_type], timeday)
        except (ValueError, KeyError):
            return 404
        new_data_json = json.dumps(data).encode('utf-8')
        new_data_b64 = base64.b64encode(new_data_json)
        modify_user_database(userid, new_data_b64, "time")
        return 200
    elif data_type == "locations":
        new_data_json = json.dumps(timeday).encode('utf-8')
        new_data_b64 = base64.b64encode(new_data_json)
        modify_user_database(userid, new_data_b64, "locations")
        return 200
    elif data_type == "ntfy":
        new_data_json = json.dumps(timeday).encode('utf-8')
        new_data_b64 = base64.b64encode(new_data_json)
        modify_user_database(userid, new_data_b64, "ntfy")
    elif data_type == "config":
        new_data_json = json.dumps(timeday).encode('utf-8')
        new_data_b64 = base64.b64encode(new_data_json)
        modify_user_database(userid, new_data_b64, "config")
    else:
        new_data_json = json.dumps(timeday).encode('utf-8')
        new_data_b64 = base64.b64encode(new_data_json)
        modify_user_database(userid, new_data_b64, "day")
        return 200
    
def check_ud_existance(userid, data, datatype):
    time_data = ["times", "breaks"]
    if datatype in time_data:
        user_time_data = user_times(userid)
        if data in user_time_data[datatype]:
            return True
        else:
            return False
    else:
        return False
    
def database_username(userid):
    data = read_data(userid, "userid")
    return data[DATABASE_INDEX["username"]]

def add_email(userid, email):
    data = load_udata(userid, "email")
    if email != data:
        modify_user_database(userid, email, "email")
        
def change_locations(userid, new_location, locations, method, loctype):
    if loctype == "location":
        loctype = "locations"
    else:
        loctype = "rooms"
    print(locations)
    if method == "add":
        locations[loctype].append(new_location)
        modify_dt_data(userid, "locations", locations, "", "")
    else:
        locations[loctype].remove(new_location)
        modify_dt_data(userid, "locations", locations, "", "")
            
def check_location(userid, location, loctype):
    location_data = load_udata(userid, "locations")
    if loctype == "room":
        loctype = "rooms"
    else:
        loctype = "locations"
    if location in location_data[loctype]:
        return [True, location_data]
    else:
        return [False, location_data]
    
def modify_ntfy(userid, apikey, serverurl):
    new_data = {
        "apikey": apikey,
        "serverurl": serverurl
    }
    modify_dt_data(userid, "ntfy", new_data, "", "")
    
def modify_config (userid, new_config):
    modify_dt_data(userid, "config", new_config, "", "")
    
def setup_config(config):
    new_data_json = json.dumps(config).encode('utf-8')
    new_data_b64 = base64.b64encode(new_data_json)
    return new_data_b64
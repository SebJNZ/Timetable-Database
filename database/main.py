# Programmed by Sebastian Johnstone in 2026. Attribution is REQUIRED.
# Import required dependencies (packages)
import os, flask_login, flask_login, argon2, itsdangerous
from flask import Flask, render_template, redirect, request, abort, session, jsonify
from database import *
from userdatabase import *
from flask_login import current_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from itsdangerous import URLSafeSerializer

# Define apps, managers, secret keys, password hasher, Jinja Functions (for templates), and a data serializer.
app = Flask(__name__)
login_manager = flask_login.LoginManager(app)
jwt = JWTManager(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=365)
app.config['SECRET_KEY'] = os.urandom(32).hex()
app.config['JWT_SECRET_KEY'] = os.urandom(32).hex()
password_hasher = argon2.PasswordHasher()
app.jinja_env.filters['to_12_hour'] = convert_time_h
blank_serializer = URLSafeSerializer(app.config['SECRET_KEY'], salt="blank_lecture")

# Define Constants
FEATURES = ["course", "location", "room", "room_number", "name", "description", "vikunja"] # This is the names of the inputs when editing lectures.
DEFAULT_TIMES = ["9:00", "10:00", "11:00", "12:00", "12:50", "13:10", "14:10", "15:10", "16:10"] # Stored in 24h format for handling.
DEFAULT_BREAKS = ["12:50"] # Breaks are optional, added by default.
DEFAULT_DAYS = [0, 1, 2, 3, 4] # Indexes of Days, Monday = 0, Tuesday = 1, etc...
DEFAULT_DURATION = 10 # Minutes, currently this is the duration of time BETWEEN lectures. I will fix this oneday...
#DEFAULT_ROOMS = ["Unknown","AAG","AM","BWA","CEL","CO","CS","CSB","CT","EA","FT","FT77","GB","GIQ","HB","HM","HU","KK","KP","KS","LB","MARU","MC","MS","MT","MY","NEC","OK","PR133","RB","RBG","RC","REG","RFG","RH","RHG","RIG","RS","SS76","SU","TA","TTR","VS","VZ","VZS","WG","WH","WR"]
#DEFAULT_LOCATIONS = {
#    "rooms": ["Unknown","AAG","AM","BWA","CO","CSB","CT","EA","FT","FT77","HB","HM","HU","KK","KP","LB","MARU","MC","MS","MT","MY","OK","RB","RC","RS","SU","TTR","VZ","VZS","WR"],
#    "locations": ["Kelburn", "Pipitea", "Te Aro", "Lower Hutt"]
#}

DEFAULT_LOCATIONS = {
    "rooms": ["Unknown", "The Treehouse", "Lego Room", "The Coffee Shop", "The Studio", "Idea Lab"],
    "locations": ["Hogwarts", "Emerald City", "Pripyat", "Salem"]
}

DEFAULT_CONFIG = {
    "td_deletion": "off"
}

class User(flask_login.UserMixin):
    def __init__(self):
        self.username = None
        
@login_manager.user_loader
def load_user(user_id):
    user_data = read_data(user_id, "userid")
    if user_data:
        user = User()
        user.id = user_data[0]
        user.username = user_data[1]
        return user
    return None

@app.route('/')
def index():
    if current_user.is_authenticated == False:
        return redirect('/login')
    if "current_page" in session:
        del session["current_page"]
    daysdata = user_days(current_user.id)
    times = user_times(current_user.id)
    return render_template("index.html", database=load_data(current_user.id, times["times"], daysdata, times["breaks"]), udays=change_casing(daysdata), utimes=times["times"], ubreaks=times["breaks"], break_time=get_break_length(times["times"], times["breaks"]))

@app.route('/lecture/<lecture_id>', methods=['GET'])
def course(lecture_id):
    if current_user.is_authenticated == False:
        return redirect('/login')
    lecture_info = load_lecture(lecture_id, current_user.id)
    if lecture_info == None:
        return abort(404)
    duplicates = find_duplicates(lecture_info["course"], current_user.id)
    duplicate_dates = []
    for duplicate in duplicates:
        date = lecture_handler(current_user.id, duplicate, True)
        date.append(duplicate)
        duplicate_dates.append(date)
    url_root = request.host_url
    return render_template("lecture.html", lecture_info=lecture_info, duplicates=duplicates, duplicate_dates=duplicate_dates, url_root=url_root)

@app.route('/edit/<day>', methods=['GET'])
def edit_route(day):
    if current_user.is_authenticated == False:
        return redirect('/login')
    day = day.lower().strip()
    usersdays = user_days(current_user.id)
    if day not in usersdays:
        return abort(404)
    # This method can be replaced, there really isn't much of a need for it, you could try using request.referrer for this.
    session["current_page"] = day
    day = NM_DAYS_C[NM_DAYS.index(day)]
    session['edit_day'] = day
    times = user_times(current_user.id)
    database=clean_data(load_data(current_user.id, times["times"], usersdays, times["breaks"]), day.lower(), current_user.id, blank_serializer)
    return render_template("edit.html", day=day, database=database, utimes=times["times"], ubreaks=times["breaks"])

@app.route('/edit/lecture/<lecture_id>', methods=['GET', 'POST'])
def edit_lecture(lecture_id):
    if request.method == "POST":
        if current_user.is_authenticated == False:
            return redirect('/login')
        if check_lecture_existance(current_user.id, lecture_id) == False:
            if len(lecture_id) > 8:
                try:
                    data = blank_serializer.loads(lecture_id)
                except itsdangerous.exc.BadSignature:
                    return abort(404)
                except itsdangerous.exc.BadData:
                    return abort(500)
            else:
                return abort(404)
            lecture_id = generate_lecture_id(current_user.id)
            
            modify_database({
                "course": request.form.get("course"),
                "name": request.form.get("name"),
                "description": request.form.get("description"),
                "day": NM_DAYS_C[data[0]],
                "start_time": data[1],
                "end_time": get_lecture_length(data[1], user_times(current_user.id)["times"], load_udata(current_user.id, "duration")),
                "location": request.form.get("location"),
                "blank": False,
                "room": request.form.get("room"),
                "room_number": request.form.get("room_number"),
                "lecture_id": lecture_id,
                "own_modified": False,
                "vikunja": request.form.get("vikunja")
            }, NM_DAYS[data[0]], current_user.id, "add")
            
            lecture_handler_adder(lecture_id, current_user.id, NM_DAYS[data[0]], data[1])
            
            return redirect("/")
        else:
            if request.form.get("changeall") == "on":
                lecture_data = load_lecture(lecture_id, current_user.id)
                
                duplicates = find_duplicates(lecture_data["course"], current_user.id)
                for feature in FEATURES:
                    if request.form.get(feature) != lecture_data[feature]:
                        for duplicate_lid in duplicates:
                            modify_lecture(duplicate_lid, current_user.id, feature, request.form.get(feature))                
            else:
                lecture_data = load_lecture(lecture_id, current_user.id)
                for feature in FEATURES:
                    if request.form.get(feature) != lecture_data[feature]:
                        modify_lecture(lecture_id, current_user.id, feature, request.form.get(feature))
            return redirect("/")
    else:
        if current_user.is_authenticated == False:
                return redirect('/login')
        
        locations = load_udata(current_user.id, "locations")
    
        if len(lecture_id) == 8:
            exists = check_lecture_existance(current_user.id, lecture_id)
            if exists == False:
                return abort(404)
            lecture_data = load_lecture(lecture_id, current_user.id)
            if lecture_data == None:
                return abort(404)
            return render_template("edit_l.html", lecture_data=lecture_data, rooms=locations["rooms"], locations=locations["locations"])
        else:
            try:
                data = blank_serializer.loads(lecture_id)
            except itsdangerous.exc.BadSignature:
                return abort(404)
            except itsdangerous.exc.BadData:
                return abort(500)
            lecture_data = {
                            "course": "",
                            "day": NM_DAYS_C[data[0]],
                            "start_time": data[1],
                            "end_time": "",
                            "location": "",
                            "blank": True,
                            "room": "",
                            "room_number": "",
                            "lecture_id": lecture_id
                        }
            return render_template("edit_l.html", lecture_data=lecture_data, rooms=locations["rooms"], locations=locations["locations"])

@app.route('/move/lecture/<lecture_id>', methods=['GET', 'POST'])
def move_lecture(lecture_id):
    if request.method == "POST":
        if current_user.is_authenticated == False:
            return redirect('/')
        lecture_data=load_lecture(lecture_id, current_user.id)
        duplicate_lectures = find_duplicates(lecture_data["course"], current_user.id)
        
        database_lectures = []
        
        for key, value in request.form.items():
            if len(key) == 8 and check_lecture_existance(current_user.id, key):
                database_lectures.append(key)
                continue
            
            try:
                data = blank_serializer.loads(key)
                if not check_time_safety(data[1]):
                    continue
                try:
                    NM_DAYS[data[0]]
                except (IndexError, TypeError, NameError):
                    continue
                
            except (itsdangerous.exc.BadData, itsdangerous.exc.BadSignature):
                continue
            
            if value != "on":
                continue
            
            # still need to change key for this! may need to add a feature for this, depending on what other functions use itm don't worry about making it a feature, implement to function straight, and require.
            add_duplicate(lecture_id, key, current_user.id, blank_serializer)
        
        for course in duplicate_lectures:
            if course not in database_lectures:
                delete_lecture(course, current_user.id)
                
        return redirect('/')
    else:
        lecture_data=load_lecture(lecture_id, current_user.id)
        duplicates = find_duplicates(lecture_data["course"], current_user.id)
        times = user_times(current_user.id)
        day_data = user_days(current_user.id)
        
        database=load_data(current_user.id, times["times"], day_data, times["breaks"])
        
        database = move_specialist_data(database, blank_serializer)
        
        return render_template("move.html", lecture_data=lecture_data, duplicates=duplicates, database=database, utimes=times["times"], ubreaks=times["breaks"], udays=change_casing(day_data))

@app.route('/delete/lecture/<lecture_id>', methods=['GET'])
def delete_lecture_route(lecture_id):
    if check_lecture_existance(current_user.id, lecture_id) == None:
        return abort(404)
    delete_lecture(lecture_id, current_user.id)
    return redirect('/')

@app.route('/delete/allilectures/<lecture_id>', methods=['GET'])
def delete_all_instances(lecture_id):
    if check_lecture_existance(current_user.id, lecture_id) == None:
        return abort(404)
    lecture_data = load_lecture(lecture_id, current_user.id)
    courses = find_duplicates(lecture_data["course"], current_user.id)
    for course in courses:
        delete_lecture(course, current_user.id)
    return redirect('/')

@app.route("/return", methods=['GET'])
def return_page():
    if "current_page" in session:
        if session["current_page"] not in NM_DAYS:
            return redirect('/')
        return redirect(f"/edit/{NM_DAYS_C[NM_DAYS.index(session["current_page"])]}")
    else:
        return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        udata = read_data(username, "username")
        if udata == False:
            session['password_error'] = True
            return redirect('/login')
        try:
            password_hasher.verify(udata[2], request.form.get('password'))
        except argon2.exceptions.VerifyMismatchError:
            session['password_error'] = True
            return redirect('/login')
        session['password_error'] = False
        user = load_user(udata[0])
        flask_login.login_user(user)
        print("logged in as", current_user.id)
        return redirect('/')
    else:
        if current_user.is_authenticated == True:
            return redirect('/')
        if 'password_error' in session:
            if session['password_error'] == True:
                session['password_error'] = False
                return render_template("login.html", password_error=True)
        return render_template("login.html", password_error=False)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        if current_user.is_authenticated == True:
            return redirect('/')
        username = request.form.get("username")
        check_username = username_check(username)
        if check_username == True:
            session['not_allowed_character'] = True
            return redirect('/signup')
        udata = read_data(username, "username")
        if udata != False:
            session['already_exists'] = True
            return redirect("/signup")
        try:
            password_hasher.verify(password_hasher.hash(request.form.get('confirm-password')), request.form.get('password'))
        except argon2.exceptions.VerifyMismatchError:
            session['password_error'] = True
            return redirect("/signup")
        user_confirm = add_user(username, password_hasher.hash(request.form.get('confirm-password')), days_setup(DEFAULT_DAYS), times_setup(DEFAULT_TIMES, DEFAULT_BREAKS, DEFAULT_DURATION), "", locations_setup(DEFAULT_LOCATIONS), setup_config(DEFAULT_CONFIG))
        if user_confirm == False:
            return abort(500)
        user_id = read_data(username, "username")[0]
        new_user_setup(user_id)
        return redirect('/')
    else:
        if current_user.is_authenticated == True:
            return redirect('/')
        if 'already_exists' in session:
            if session['already_exists'] == True:
                session['already_exists'] = False
                session['password_error'] = False
                return render_template("signup.html", already_exists=True, password_error=True, bad_char=False)
        if 'password_error' in session:
            if session['password_error'] == True:
                session['password_error'] = False
                return render_template("signup.html", already_exists=False, password_error=True, bad_char=False)
        if 'not_allowed_character' in session:
            if session['not_allowed_character'] == True:
                session['not_allowed_character'] = False
                return render_template("signup.html", already_exists=False, password_error=False, bad_char=True)
        return render_template("signup.html", already_exists=False, password_error=False, bad_char=False)
            
@app.route("/logout")
def logout():
    if current_user.is_authenticated == False:
        return redirect('/')
    flask_login.logout_user()
    return redirect('/')

@app.route("/settings")
def settings():
    if current_user.is_authenticated == False:
        return redirect("/")
    return render_template("settings.html")

@app.route("/settings/timetable")
def settings_timetable():
    if current_user.is_authenticated == False:
        return redirect('/')
    times = user_times(current_user.id)
    times_inc = {}
    times_inc["times"] = times["times"][:]
    times_inc["breaks"] = times["breaks"][:]
    times_inc["times"].append("LASTTIME")
    times_inc["breaks"].append("LASTBREAK")
    return render_template("settings_tt.html", NM_DAYS_C=NM_DAYS_C, DatabaseDays=user_days(current_user.id), DAYS_LEN=len(NM_DAYS_C), TIMES_LEN=(len(times["times"]) - len(times["breaks"])), DatabaseTimes=times_inc["times"], DatabaseBreaks=times_inc["breaks"], DatabaseTIDs=generate_tids(times, blank_serializer))

@app.route("/settings/user")
def settings_user():
    if current_user.is_authenticated == False:
        return redirect("/")
    if 'invalid_email' in session:
        if session["invalid_email"] == True:
            session["invalid_email"] = False
            return render_template("settings_u.html", email=load_udata(current_user.id, "email"), invalid_email=True, ntfy=load_udata(current_user.id, "ntfy"))
    return render_template("settings_u.html", email=load_udata(current_user.id, "email"), invalid_email=False, ntfy=load_udata(current_user.id, "ntfy"), config=load_udata(current_user.id, "config"))

@app.route("/settings/api")
def settings_api():
    if current_user.is_authenticated == False:
        return redirect('/')
    return render_template("api.html", apikey=load_udata(current_user.id, "apikey"))

@app.route("/settings/api/gen")
def generate_api():
    if current_user.is_authenticated == False:
        return redirect('/')
    token = create_access_token(identity=str(current_user.id))
    result = change_apikey(current_user.id, token)
    if result == False:
        token = create_access_token(identity=str(current_user.id))
        result = change_apikey(current_user.id, token)
        if result == False:
            return abort(500)
    return redirect("/settings/api")

@app.route("/settings/edit/days", methods=['POST'])
def edit_days():
    if current_user.is_authenticated == False:
        return redirect('/')
    userdays = user_days(current_user.id)
    modified_days_list = []
    new_days = []
    to_be_removed = []
    changes_made = False
    for day in NM_DAYS:
        dayresult = request.form.get(day)
        
        if dayresult == "on":
            new_day_index = NM_DAYS.index(day)
            
            # This loop is here to ensure days are in order, just incase (:
            for indexday in modified_days_list:
                if new_day_index < indexday:
                    new_day_index.insert(modified_days_list.index(indexday), new_day_index)
            if new_day_index not in modified_days_list:
                modified_days_list.append(new_day_index)
            
        
        if day not in userdays and dayresult == "on":
            new_days.append(day)
            changes_made = True
        if day in userdays and dayresult != "on":
            to_be_removed.append(day)
            changes_made = True
        
    if changes_made == True:
        modify_dt_data(current_user.id, "days", modified_days_list, "add", get_new_index)
        check_local_keys(current_user.id, new_days)
    if load_udata(current_user.id, "config")["td_deletion"] == "on":
        for day in to_be_removed:
            wipe_day(current_user.id, day)
    return redirect("/")
    
@app.route("/settings/edit/config", methods=['POST'])
def edit_config():
    if current_user.is_authenticated == False:
        return redirect("/")
    user_config = load_udata(current_user.id, "config")
    if user_config["td_deletion"] != request.form.get("td_deletion"):
        if request.form.get("td_deletion") == "on":
            user_config["td_deletion"] = "on"
        else:
            user_config["td_deletion"] = "off"
    modify_config(current_user.id, user_config)
    return redirect("/settings/user")
    
@app.route("/settings/edit/ntfy/email", methods=['POST'])
def edit_ntfy_email():
    if current_user.is_authenticated == False:
        return redirect("/")
    email = request.form.get("email")
    if check_email(email) != True:
        session["invalid_email"] = True
        return redirect("/settings/user")
    add_email(current_user.id, email)
    return redirect("/settings/user")
    
@app.route("/settings/edit/ntfy/api", methods=['POST'])
def edit_ntfy_api():
    if current_user.is_authenticated == False:
        return redirect("/")
    url = request.form.get("url")
    if check_url(url) != True:
        session["invalid_url"] = True
        return redirect("/settings/user")
    modify_ntfy(current_user.id, request.form.get("api"), url)
    return redirect("/settings/user")

@app.route("/settings/edit/locations")
def user_locations():
    if current_user.is_authenticated == False:
        return redirect("/")
    locations = load_udata(current_user.id, "locations")
    locs = locations["locations"]
    locs_inc = locs[:]
    locs_inc.append("LASTLOC")
    rooms = locations["rooms"]
    rooms_inc = rooms[:]
    rooms_inc.append("LASTLOC")
    return render_template("settings_loc.html", rooms=rooms_inc, ROOMS_LEN=len(rooms), Locations=locs_inc, LOCATIONS_LEN=len(locs))

@app.route("/settings/edit/locations/<loctype>/new", methods=['GET', 'POST'])
def new_user_location(loctype):
    if current_user.is_authenticated == False:
        return redirect("/")
    if loctype not in ["location", "room"]:
        return redirect("/settings/edit/locations")
    if request.method == "POST":
        location = request.form.get("location")
        if len(location) > 15:
            session["length_too_long"] = True
            return redirect(f"/settings/edit/locations/{loctype}/new")
        locations = check_location(current_user.id, location, loctype)
        if locations[0] == True:
            session["length_too_long"] = True
            return redirect(f"/settings/edit/locations/{loctype}/new")
        change_locations(current_user.id, location, locations[1], "add", loctype)
        return redirect("/settings/edit/locations")
    else:
        if 'location_exists' in session:
            if session["location_exists"] == True:
                session["location_exists"] = False
                return render_template("new_location.html", length_too_long=False, location_exists=True, loctype=loctype)
        if "length_too_long" in session:
            if session["length_too_long"] == True:
                session["length_too_long"] = False
                return render_template("new_location.html", length_too_long=True, location_exists=False, loctype=loctype)
        return render_template("new_location.html", length_too_long=False, location_exists=False, loctype=loctype)

@app.route("/settings/delete/locations/<loctype>/<location>")
def delete_room(loctype, location):
    if current_user.is_authenticated == False:
        return redirect("/")
    locations = check_location(current_user.id, location, loctype)
    if locations[0] == False:
        return redirect("/settings/edit/locations")
    change_locations(current_user.id, location, locations[1], "remove", loctype)
    return redirect("/settings/edit/locations")

@app.route("/settings/delete/<timetype>/<tid>") # Endpoint open to attack. While it isn't possible due to anti-tamper, precaution prevention is required. Check if the len of times is 1. As we don't give the end user a button remove times if it is (except breaks).
def delete_time(timetype, tid): # You need to contemplate whether to delete data or not. Maybe give a confirm menu if we do delete it.
    if current_user.is_authenticated == False:
        return redirect('/')
    times = user_times(current_user.id)
    time = blank_serializer.loads(tid)
    if not check_time_safety(time):
        return abort(404)
    if timetype == "break":
        modify_dt_data(current_user.id, "breaks", time, "remove", get_new_index)
    modify_dt_data(current_user.id, "times", time, "remove", get_new_index) 
    if load_udata(current_user.id, "config")["td_deletion"] == "on":
        wipe_time(current_user.id, time, times)
    return redirect("/")

@app.route("/settings/add/<timetype>", methods=['GET', 'POST'])
def new_time(timetype):
    if current_user.is_authenticated == False:
        return redirect('/')
    if request.method == "POST":
        time = request.form.get("time")
        if timetype not in ["break", "time"]:
            return abort(404)
        if check_time_safety(time) == False:
            return abort(404)
        if timetype == "break":
            databasetimetype = "breaks"
        else:
            databasetimetype = "times"
        cleaner = clean_morning_24h(time)
        if cleaner[0] == True:
            time = cleaner[1]
        if check_ud_existance(current_user.id, time, databasetimetype):
            session["time_exists"] = True
            return redirect(f"/settings/add/{timetype}")
        if timetype == "break":
            modify_dt_data(current_user.id, "breaks", time, "add", get_new_index)
        modify_dt_data(current_user.id, "times", time, "add", get_new_index)
        return redirect("/")
    else:
        # Make sure to modify this function to make sure that the new time goes to the relevant time slot.
        if timetype == "time":
            if 'time_exists' in session:
                if session["time_exists"] == True:
                    session["time_exists"] = False
                    return render_template("new_time.html", new_type="Time", time_exists=True)
            return render_template("new_time.html", new_type="Time", time_exists=False)
        elif timetype == "break":
            if 'time_exists' in session:
                if session["time_exists"] == True:
                    session["time_exists"] = False
                    return render_template("new_time.html", new_type="Break", time_exists=True)
            return render_template("new_time.html", new_type="Break", time_exists=False)
        else:
            return abort(404)

@app.route("/api/v1/<route>")
@jwt_required()
def api(route):
    current_user = get_jwt_identity()
    if route == "test":
        return f"Successful Test, your UserID is: {current_user}. \n\nYour API Key is: \n{request.headers.get("Authorization")}\n", 200
    if route == "timetable":
        return jsonify(read_database(current_user))
    if route == "ntfy":
        email = load_udata(current_user, "email")
        ntfy_details = load_udata(current_user, "ntfy")
        if not email:
            return "email_error"
        email_safe = check_email(email)
        try:
            if ntfy_details["serverurl"]:
                pass
        except (TypeError, IndexError):
            return "No NTFY Credentials in account."
        url_safe = check_url(ntfy_details["serverurl"])
        if email_safe and url_safe and ntfy_details["apikey"]:
            return jsonify({
                "apikey": ntfy_details["apikey"],
                "serverurl": ntfy_details["serverurl"],
                "email": email
            })
        else:
            if email_safe == False:
                return "email_error"
            elif url_safe == False:
                return "url_error"
            elif ntfy_details["apikey"]:
                return "apikey_error"
        

@app.route("/api/v1/timetable/<route>")
@jwt_required()
def api_timetable(route):
    current_user = get_jwt_identity()
    
    if route.lower() in NM_DAYS:
        return jsonify(read_database(current_user)[NM_DAYS[NM_DAYS.index(route)]])

@app.route("/api/v1/user/name")
@jwt_required()
def api_user():
    current_user = get_jwt_identity()
    user_name = database_username(current_user)
    return user_name

# This if statement starts the app as sole, so it doesn't run the app if someone, for whatever reason, imports it as a package.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
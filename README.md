# Timetable-Database
Timetable Database is your self-hosted solution for all your timetable needs. It is designed to keep you on time. No matter the day.

# Features
Timetable Database is designed to be a streamlined and polished product, with lots of cool and useful features.
* NTFY and Email reminders.
* Full fledged API, including secure Bearer Tokens for each user.
* Easy interface with multiple user accounts.
* Hashed passwords and unique database design.
* Built on my own reliable timetable model, designed to adjust to different timetables.
* Customizable Days and Times.

# Future Features
* More API features.
* Hot-swappable timetables
* Vikunja API intergration - automatically create a Vikunja project from a click of a button.
* Slack Bot (in development) - Ever wanted a quick way to check when your lectures are? Our slack bot is the way to go.
* CalDav/Calendar intergration - Want your timetable in your favourite calendar app? No worries, we got you.
* Easier customisability - add custom rooms and colour schemes to the user gui, so you don't have to dig through the code to do this.
* Administrator account - Have a team and want to be able to manage and assign times to people? Timetable Database is the perfect tool for you and your team.

# Setup
Requirements:<br>
* A secure way to access your server, like Tailscale

Although I try to make this product as secure as possible, I'm not a security professional, and mistakes happen.
* Latest version of Python
* An internet connection (optional - only if you wish to access the product outside of your local network, or to use Email reminders (and NTFY out of your network).

Instructions:
<br>
1) (optional - recommended if you require sudo permissions) Create and enter an environment, run: `python -m venv env`, then enter it `source env/bin/activate` or `./env/Scripts/activate.ps1` on Windows.
3) Install the requirements. While in the home directory, run `pip3 install -r requirements.txt`. If you have issues with this, install `requirements.ver.txt`.
4) Run timetable database. You can either add this as a service, use a guide like [this](https://medium.com/@ni8hin/deploying-a-flask-application-with-systemd-on-ubuntu-5c767bf2f3b4) (haven't looked into it) or just in a shell, to do so enter /database, and run `python3 main.py`.

Setup Email/NTFY reminder (Linux only). <br>
If you aren't using NTFY with Email, you will need to modify the script yourself slightly, I will add both versions eventually in here.
1) Add your API keys and 
2) You will need to create a cronjob. So make sure you have cron (sudo apt install cron), search instructions for other distros.
3) Enter the crontab utility. Run: `crontab -e`. You will need to choose when you wish to schedule the cronjob, I recommend every 5-10 minutes for best accuracy.  

# API
To get your api key, log into your account and head to /api/v1, as long as you are logged in, a key will be generated. This key will expire after 1 year, unless you restart the service.

To stop your key from expiring whenever you restart the application, set app.config['SECRET_KEY'] and app.config['JWT_SECRET_KEY'] to a secure randomised key.

Is it possible to stop your key from expiring forever? Yeah... Unless your application is on a private network (such as Tailscale or your own home network, that isn't portforwarding) I wouldn't do this. If you would like to, research flask_jwt_extended online for more info.

API Routes:
* /api/v1/test

Test your API key here.

* /api/v1/timetable

Return your entire timetable in json.

* /api/v1/timetable/<day>

<day> is a variable, enter a valid day that you have in your timetable, and you will recieve all the data from that day.

* /api/v1/user/name

Returns your username, used in Email reminders.

# License
This product can be remixed, but you must attribute this product, you cannot market this as your own, the more you use, the more you attribute, you must leave a link to this GitHub Repo and my profile in/on the product, with a mention about using an adaptation of Timetable Database somewhere obvious on your product. This product can be used commercially, but MUST NOT be sold.

# Update Log
v1 - Initial release

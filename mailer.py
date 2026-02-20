import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

def emailer(lecture, laptop_status, TIMETABLE_DATABASE_URL, name):
    email = MIMEMultipart("alternative")
    email["From"] = formataddr((os.getenv("EMAIL_DSPNAME"), os.getenv("SMTP_EMAIL_ADDRESS")))
    email["To"] = os.getenv("RECIEVER_EMAIL")
    email["Subject"] = f"Lecture Notification - {lecture['course']}"

    if laptop_status == 1:
        total_string = "phone and laptop are"

    else:
        total_string = "phone is"

    text = f"""Hi {name},\n\nYour lecture {lecture['course']} starts at {lecture['start_time']} in {lecture['location']}.\n\nIt appears your {total_string} currently not connected to Tailscale.\nPlease reconnect to ensure you continue receiving notifications.\nIf the issue persists, we’ll keep emailing you important updates.\n\nYou can update your courses anytime through the dashboard: \n{TIMETABLE_DATABASE_URL}\n\nThis is an automated message from your notification system."""

    html = f"""<html>
    <body style="font-family: Arial, sans-serif; color: #222;">
        <p>Hi {name},</p>

        <p>
            Lecture <strong>{lecture['course']}</strong> starts at 
            <strong>{lecture['start_time']}</strong> in 
            <strong>{lecture['location']}</strong>.
        </p>

        <p>
            It appears your {total_string} disconnected from Tailscale.  
            Please reconnect to ensure you get your latest notifications.
            If you don't, we'll continue sending email alerts.
        </p>

        <p>
            To update your courses, head to the dashboard:<br>
            <a href="{TIMETABLE_DATABASE_URL}">{TIMETABLE_DATABASE_URL}</a>
        </p>

        <p style="color:#888; font-size: 0.9em;">
            This is an automated notification from your system.
        </p>
        </body>
</html>"""

    text_body = MIMEText(text, 'plain')
    html_body = MIMEText(html, 'html')

    email.attach(text_body)
    email.attach(html_body)

    with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), os.getenv("SMTP_PORT")) as s:
        s.login(os.getenv("SMTP_EMAIL_ADDRESS"), os.getenv("SMTP_EMAIL_PASSWORD"))
        s.send_message(email)
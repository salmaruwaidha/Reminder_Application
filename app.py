import smtplib
from flask import Flask, request, render_template, redirect,url_for
from email.message import EmailMessage
from datetime import datetime
import threading
import time
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB configuration
MONGO_URI = "mongodb+srv://ruwaidhafarook:bexxOXYURXKfDiji@cluster0.npttv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Replace with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client.reminder_db  # Name of your database
reminders_collection = db.reminders  # Name of your collection

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
GMAIL_USERNAME = "ruwaidhafarook@gmail.com"  # Replace with your email
GMAIL_PASSWORD = "ylkhveogvljrjsnx"  # Replace with your app password or email password

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        event_name = request.form.get('event_name')
        date_time_str = request.form.get('date_time')
        email = request.form.get('email')

        if event_name and date_time_str and email:
            # Save reminder to MongoDB
            reminders_collection.insert_one({
                "event_name": event_name,
                "date_time": date_time_str,
                "email": email
            })
            return redirect(url_for('reminder_success'))
        else:
            return 'Please provide event name, date/time, and email address.'

    return render_template('index.html')

def send_reminder_email(to_email, event_name):
    subject = "Reminder for Your Scheduled Event"
    body = f"Dear User,\n\nThis is a reminder for your event: '{event_name}'.\n\nBest regards,\nYour Reminder App Team"

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USERNAME
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(GMAIL_USERNAME, GMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Reminder email sent to {to_email} for event '{event_name}'.")
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/reminder_success')
def reminder_success():
    return render_template('success.html')

def check_reminders():
    while True:
        current_time = datetime.now()
        print(f"Current Time: {current_time}")
        reminders = reminders_collection.find()
        
        for reminder in reminders:
            event_time = datetime.strptime(reminder['date_time'], '%Y-%m-%dT%H:%M')
            print(f"Checking reminder for event '{reminder['event_name']}' at {event_time}")

            if current_time >= event_time:
                print(f"Sending email for event '{reminder['event_name']}' to {reminder['email']}")
                send_reminder_email(reminder['email'], reminder['event_name'])
                reminders_collection.delete_one({"_id": reminder['_id']})

        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    # Start the background thread to check for reminders
    threading.Thread(target=check_reminders, daemon=True).start()
    app.run(debug=True)

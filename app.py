import smtplib
from flask import Flask, request, render_template, redirect, url_for
from email.message import EmailMessage
from pymongo import MongoClient
from bson.objectid import ObjectId  # Import ObjectId for MongoDB
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz

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
GMAIL_PASSWORD = "ylkhveogvljrjsnx"  # Replace with your app password

# Scheduler setup
scheduler = BackgroundScheduler()

# Handle favicon error by ignoring the request
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return an empty response

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        event_name = request.form.get('event_name')
        date_time_str = request.form.get('date_time')  # This will have the format '2024-10-21T15:24'
        email = request.form.get('email')

        if event_name and date_time_str and email:
            # Save reminder to MongoDB
            reminders_collection.insert_one({
                "event_name": event_name,
                "date_time": date_time_str,
                "email": email
            })

            # Convert the datetime string to a datetime object
            scheduled_time = datetime.fromisoformat(date_time_str)  # Parse ISO format

            # Schedule the email to be sent at the specified time
            scheduler.add_job(send_reminder_email, 'date', run_date=scheduled_time, args=[email, event_name])

            # Send email immediately
            send_reminder_email(email, event_name)

            return redirect(url_for('reminder_success'))
        else:
            return 'Please provide event name, date/time, and email address.'

    return render_template('index.html')
@app.route('/reminders')
def reminders():
    reminders = reminders_collection.find()
    return render_template('reminders.html', reminders=reminders)

@app.route('/edit_reminder/<reminder_id>', methods=['GET', 'POST'])
def edit_reminder(reminder_id):
    reminder = reminders_collection.find_one({"_id": ObjectId(reminder_id)})
    if request.method == 'POST':
        event_name = request.form.get('event_name')
        date_time_str = request.form.get('date_time')
        email = request.form.get('email')

        # Update reminder in the database
        reminders_collection.update_one(
            {"_id": ObjectId(reminder_id)},
            {"$set": {"event_name": event_name, "date_time": date_time_str, "email": email}}
        )

        # Convert the datetime string to a datetime object
        scheduled_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')  # Adjust format as necessary
        # Schedule the updated email to be sent at the new specified time
        scheduler.add_job(send_updated_reminder_email, 'date', run_date=scheduled_time, args=[email, event_name, date_time_str])

        return redirect(url_for('reminders'))

    return render_template('edit_reminder.html', reminder=reminder)

@app.route('/delete_reminder/<reminder_id>', methods=['POST'])
def delete_reminder(reminder_id):
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
    return redirect(url_for('reminders'))

@app.route('/reminder_success')
def reminder_success():
    return render_template('success.html')

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

def send_updated_reminder_email(to_email, event_name, date_time):
    subject = "Your Event Reminder has been Updated"
    body = f"Dear User,\n\nYour event: '{event_name}' has been updated with new details.\n\nNew Event Date/Time: {date_time}\n\nBest regards,\nYour Reminder App Team"

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
            print(f"Updated reminder email sent to {to_email} for event '{event_name}'.")
    except Exception as e:
        print(f"Failed to send updated reminder email: {e}")

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    app.run(debug=True)

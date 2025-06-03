from email.mime.text import MIMEText
import smtplib
from email.message import EmailMessage

from datetime import datetime
import requests
import os
import time
import json
import traceback
import sys

HIBP_API_KEY = os.getenv("HIBP_API_KEY")
email_address = str(os.getenv("protonmail_email_address"))
protonmail_bridge_pass = str(os.getenv("protonmail_bridge_pass"))

with open('emails.txt', 'r') as f:
    emails = [email.strip() for email in f.readlines()]

breached_emails = {}

timeout = 8 # Pwned 1 subscription allows 10 email checks a minute so 6 seconds per email but added 2 seconds to be sure status code 429 is never recieved

HEADERS = {
    "hibp-api-key": HIBP_API_KEY,
    "User-Agent": "EmailSecurityCheck"
}

# function to email error code using ProtonMail Bridge
def send_error_email(error_message):
    # create message object
    message = MIMEText(f"🚨 An error occurred in your script:\n\n{error_message}")
    message["Subject"] = "🚨 Have I Been Pwned - Script Error Alert"
    message["From"] = email_address
    message["To"] = email_address

    with smtplib.SMTP('127.0.0.1', 1025) as smtp:  # Port 1025 is default for Bridge
        smtp.login(email_address, protonmail_bridge_pass)
        smtp.send_message(message)

    sys.exit(1)  # Exit script if error occurs (will show in task scheduler that error occurred)

# function to send email using ProtonMail Bridge
def send_email_alert():
    try:
        # Build the message body exactly as before
        message_body = "The following emails have been found in breaches:\n\n"
        
        for email, breaches in breached_emails.items():
            message_body += f"🚨 {email} found in {len(breaches)} breach(es):\n"
            for breach in breaches:
                message_body += f"  - {breach['name']} ({breach['date']})\n"
                message_body += (
                    f"    More info: https://haveibeenpwned.com/PwnedWebsites#{breach['name']}\n"
                )
            message_body += "\n"

        # Create the MIMEText message
        message = MIMEText(message_body)
        message["Subject"] = "🚨 Have I Been Pwned - Data Breach Alert"
        message["From"] = EMAIL_SENDER
        message["To"] = EMAIL_RECIPIENT

        # Send via ProtonMail Bridge (local SMTP at 127.0.0.1:1025)
        with smtplib.SMTP("127.0.0.1", 1025) as smtp:
            smtp.login(email_address, protonmail_bridge_pass)
            smtp.send_message(message)

    except Exception as e:
        # If anything goes wrong, fall back to the error‐email routine
        send_error_email(traceback.format_exc())


def check_breaches(email):
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            return response.json()  # Returns list of breaches
        elif response.status_code == 404:
            return []  # No breaches found
        else:
            return None

    except Exception as e:
        send_error_email(traceback.format_exc())

def check_pastes(email):
    pass # tbh copliot gave me this maybe add it idk
    # https://haveibeenpwned.com/api/v3/pasteaccount/{account}
    # https://haveibeenpwned.com/API/v3#PastesForAccount (documentation)


# Open file for appending and reading
def check_emails():
    try:
        with open("breached_emails.txt", "a+") as f:
            f.seek(0)
            file_contents = set(f.readlines())  # Use set for faster lookups

            for email in emails:
                breaches = check_breaches(email)

                if breaches:
                    new_breaches = []
                    
                    for breach in breaches:
                        formatted_date = datetime.strptime(breach['BreachDate'], "%Y-%m-%d").strftime("%d/%m/%Y")
                        entry = f"{email} - {breach['Name']} ({formatted_date})\n"

                        if entry not in file_contents:
                            f.write(entry)  # Append to file
                            new_breaches.append({"name": breach['Name'], "date": formatted_date})

                    if new_breaches:
                        breached_emails[email] = new_breaches

                # Add delay only if there are more emails left to check
                if email != emails[-1]:
                    time.sleep(timeout)

    except Exception as e:
        send_error_email(traceback.format_exc())

def main():
    try:
        # check if there is a new breach
        with open('last_known_breach.json', 'a+') as f:
            f.seek(0)
            try:
                last_breach = json.load(f)  # Load existing data
            except (json.JSONDecodeError, FileNotFoundError):
                last_breach = {}

            url = "https://haveibeenpwned.com/api/v3/latestbreach"
            response = requests.get(url, headers=HEADERS).json()

            if not last_breach or datetime.strptime(response["AddedDate"], "%Y-%m-%dT%H:%M:%SZ") > datetime.strptime(last_breach.get("AddedDate", "2000-01-01T00:00:00Z"), "%Y-%m-%dT%H:%M:%SZ"):
                # "2000-01-01T00:00:00Z" is a default date for comparison if no file contents
                f.seek(0)  # Move cursor back to overwrite
                f.truncate()  # Clear old data
            
                new_breach_data = {
                    "Name": response["Name"],
                    "BreachDate": response["BreachDate"],
                    "AddedDate": response["AddedDate"],
                    "ModifiedDate": response["ModifiedDate"]
                }

                json.dump(new_breach_data, f, indent=4)  # Save new breach

                # check all emails for breaches
                check_emails()

        # Send email alert if any new breaches found
        if breached_emails:
            send_email_alert()
    
    except Exception as e:
        send_error_email(traceback.format_exc())


if __name__ == "__main__":
    main()


'''
MIT License

Copyright (c) 2025 newKio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Original creator: newKio - https://github.com/newKio/HIBP
'''
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from datetime import datetime
import requests
import os
import time
import base64
import json
import traceback

HIBP_API_KEY = os.getenv("HIBP_API_KEY")
EMAIL_PASSWORD = os.getenv("HIBP_EMAIL_PASSWORD")
EMAIL_SENDER = os.getenv("HIBP_EMAIL_SENDER")
EMAIL_RECIPIENT = os.getenv("HIBP_EMAIL_RECIPIENT")

with open('emails.txt', 'r') as f:
    emails = [email.strip() for email in f.readlines()]

breached_emails = {}

timeout = 10 # Pwned 1 subscription allows 10 email checks a minute so 6 seconds per email but added 4 seconds to be sure status code 429 is never recieved

HEADERS = {
    "hibp-api-key": HIBP_API_KEY,
    "User-Agent": "EmailSecurityCheck"
}

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def send_error_email(error_message):
    service = build("gmail", "v1", credentials=authenticate_gmail())

    message = MIMEText(f"🚨 An error occurred in your script:\n\n{error_message}")
    message["Subject"] = "🚨 Have I Been Pwned - Script Error Alert"
    message["From"] = EMAIL_SENDER
    message["To"] = EMAIL_RECIPIENT

    service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()


def authenticate_gmail():
    creds = None
    token_path = "token.json"

    # Check if token.json exists to avoid re-authentication
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid credentials, authenticate manually
    if not creds or not creds.valid or not creds.refresh_token:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent")

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds

def send_email_alert():
    try:
        service = build("gmail", "v1", credentials=authenticate_gmail())

        message_body = "The following emails have been found in breaches:\n\n"
        
        for email, breaches in breached_emails.items():
            message_body += f"🚨 {email} found in {len(breaches)} breach(es):\n"
            for breach in breaches:
                message_body += f"  - {breach['name']} ({breach['date']})\n"
                message_body += f"    More info: https://haveibeenpwned.com/PwnedWebsites#{breach['name']}\n"
            message_body += "\n"

        message = MIMEText(message_body)
        message["Subject"] = "🚨 Have I Been Pwned - Data Breach Alert"
        message["From"] = EMAIL_SENDER
        message["To"] = EMAIL_RECIPIENT

        service.users().messages().send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}).execute()

    except Exception as e:
        send_error_email(traceback.format_exc())

def check_breaches(email):
    try:
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
        response = requests.get(url, headers=HEADERS)
        raise ValueError("Simulated error for testing!")  # Force an error

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

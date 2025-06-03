# 🔐 Automated Email Breach Monitoring Script

This Python script **automates checking if your email addresses/aliases have been involved in data breaches** using the **Have I Been Pwned (HIBP) API**. If a breach is detected, the script sends an **email alert** via **Proton Mail Bridge**, ensuring you stay informed of any compromises.

---

## 🚀 Features

- 📡 **Automated Breach Checking** – Checks all emails against HIBP.
- 📧 **Email Alerts** – Sends an email if a breach is found.
- ⏳ **Rate-Limit Handling** – Avoids 429 errors with timed requests.
- 🛠 **Error Notifications** – Emails you if the script fails.
- 🔁 **Runs Automatically** – Can be scheduled with Task Scheduler/Cron job.

---

## 🛠 Installation & Setup

### 1️⃣ Prerequisites

- **Python 3.x**
- HIBP **API Key**
- **Proton Mail Bridge**
- Windows **Task Scheduler**/Cron (for automation)

### 2️⃣ Install Dependencies

```bash
pip install requests
```

### 3️⃣ Configure Environment Variables

Set the following environment variables:

``` bash
HIBP_API_KEY = "your_hibp_api_key"
email_address = "your_email@email.com"
protonmail_bridge_pass = "your_bridge_password"
```

### 4️⃣ Setup Proton Mail Bridge (First-Time Only)

1. Download [proton mail bridge](https://proton.me/mail/bridge)
2. Log into your account.
3. Grab password from "SMTP" section in "Mailbox details".

### **Automate with Task Scheduler/Cron Jobs**

Task Scheduler

1. Open Task Scheduler (taskschd.msc).
2. Create a new task.
3. Set trigger: Every X days/weeks.
4. Set action: Run Python with the script.

Cron Job

1. Run ```crontab -e```
2. Add ```0 0 */2 * * /usr/bin/python3 /path/to/script.py```
3. Replace ```/path/to/script.py``` with the actual path to your script
4. Adjust when and how often you would like the script to run (command in 2. runs every 2 days at mightnight(00:00))
5. Note: check documentation for help on how to use cron jobs

---

### 📜 Example Output

✅ No breaches found:

``` bash
All emails are safe for now.
```

🚨 Breach Detected:

``` bash
🚨 example@email.com found in 2 breaches:
  - LinkedIn (05-05-2012)
  - Adobe (04-10-2013)
```

Note: only new breaches will be shown in the email

---

### 📌 How It Works

1. Retrives email addresses/aliases (via ```emails.txt```)
2. Checks for a new breach via ```https://haveibeenpwned.com/api/v3/latestbreach```
   - if a new breach is detected
     - Checks each email against HIBP.
     - If any emails found in the breach, it
       - Saves it to ```breached_emails.txt```
3. Sends an alert email if any of your emails were affected.

---

### 🏗 To-Do List

- Automate retrieving email aliases.

---

### License

This project is licensed under the **MIT License**. Feel free to **use, modify, and distribute** it, but **please provide attribution** by keeping my name in the copyright notice.

If you improve the script or use it in a project, a **shoutout** or a mention would be appreciated! 😊

---

### Why Choose Have I Been Pwned?

Troy Hunt, the creator of HIBP, **manually verifies each breach** to ensure its legitimacy before adding it to the database. Instead of relying on automation, this process ensures that the information is **accurate, reliable, and trustworthy**. **Because of this rigorous verification process, I have chosen to use HIBP for my breach monitoring script.**

### Notes

If you buy a higher tier HIBP API key you can adjust the timeout (e.g. for a Pwned 2 key you can do 1 second timeout). You can change the date format if you wish.

If you do not have a proton email acccount, please refer to the previous version of ```main.py``` and ```readme.md```. There is a detailed description on how to set this script up using a google email address.

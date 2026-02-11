# Quick Start Guide

Get your Gmail monitor running in 10 minutes!

## Prerequisites

- Gmail account
- Python 3.8+
- (Optional) Twilio account for SMS

## Step 1: Clone & Install

```bash
git clone https://github.com/yourusername/job-search-gmail-monitor.git
cd job-search-gmail-monitor
chmod +x setup.sh
./setup.sh
```

## Step 2: Gmail API Setup (5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" (top left)
3. Name it "Gmail Monitor" and click Create
4. In the search bar, type "Gmail API" and enable it
5. Click "Credentials" in the left sidebar
6. Click "Create Credentials" → "OAuth client ID"
7. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: Gmail Monitor
   - User support email: your email
   - Developer contact: your email
   - Click Save and Continue through all screens
8. Back to Create OAuth client ID:
   - Application type: Desktop app
   - Name: Gmail Monitor
   - Click Create
9. Click Download JSON
10. Rename file to `credentials.json` and move to `config/` directory

## Step 3: Configure Email Notifications

Edit `.env`:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # See note below
NOTIFICATION_EMAIL=your-email@gmail.com
```

**Getting Gmail App Password:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification if not already enabled
3. Search for "App passwords"
4. Generate new app password for "Mail"
5. Copy the 16-character password to `.env`

## Step 4: Configure SMS (Optional)

If you want SMS alerts:

1. Sign up at [Twilio](https://www.twilio.com/try-twilio) (free trial available)
2. Get a phone number
3. Add to `.env`:

```bash
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
YOUR_PHONE_NUMBER=+1234567890
```

## Step 5: Customize Settings

Edit `config/settings.yaml` to add:
- Companies you're applying to
- Keywords specific to your job search
- Domains to track

## Step 6: Run!

```bash
# Single check
python src/main.py

# Continuous monitoring (checks every 5 minutes)
python src/main.py --daemon --interval 300
```

On first run, a browser will open asking you to authorize the app. Grant permission (read-only access to Gmail).

## Common Issues

**"Credentials file not found"**
- Make sure `credentials.json` is in the `config/` directory

**"SMTP authentication failed"**
- Use an App Password, not your regular Gmail password
- Ensure 2-Step Verification is enabled

**No emails detected**
- Check that `config/settings.yaml` has relevant keywords
- Try running with `--verbose` flag to see what's happening

## Running as a Background Service

### macOS/Linux (cron):
```bash
# Edit crontab
crontab -e

# Add this line to check every 5 minutes
*/5 * * * * cd /path/to/job-search-gmail-monitor && /path/to/venv/bin/python src/main.py
```

### Windows (Task Scheduler):
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 5 minutes
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `src/main.py`
   - Start in: `C:\path\to\job-search-gmail-monitor`

## Need Help?

Check the main [README.md](README.md) for detailed documentation or open an issue on GitHub.

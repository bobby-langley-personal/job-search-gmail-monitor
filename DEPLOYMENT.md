# Cloud Deployment Guide

Run your Gmail monitor 24/7 in the cloud without keeping your desktop running.

## Deployment Options Comparison

| Platform | Cost | Complexity | Best For | Limitations |
|----------|------|------------|----------|-------------|
| **GitHub Actions** | Free | Low | Simple schedules | 5-10 min intervals max, 6 hours/day limit |
| **Railway.app** | $5/month | Low | 24/7 monitoring | Requires payment |
| **AWS Lambda** | Free tier | Medium | Scalable solution | Complex setup |
| **Google Cloud Run** | Free tier | Medium | Gmail integration | Requires GCP setup |
| **DigitalOcean** | $6/month | Medium | Full control | Manual setup |

---

## Option 1: GitHub Actions (Recommended for Beginners)

**Pros**: Free, no server management, easy setup
**Cons**: Max frequency every 5 minutes, 6-hour daily runtime limit

### Setup Steps

1. **Create GitHub repository** (if not already done)
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/job-search-gmail-monitor.git
git push -u origin main
```

2. **Add secrets to GitHub**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `GMAIL_CREDENTIALS` - Content of `config/credentials.json`
     - `GMAIL_TOKEN` - Content of `config/token.pickle` (base64 encoded)
     - `ANTHROPIC_API_KEY` - Your Anthropic API key
     - `SMTP_USERNAME` - Your Gmail address
     - `SMTP_PASSWORD` - Your Gmail app password
     - `NOTIFICATION_EMAIL` - Where to send alerts

3. **Create workflow file**

Create `.github/workflows/monitor.yml`:

```yaml
name: Gmail Job Monitor

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  monitor:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Setup credentials
      run: |
        mkdir -p config
        echo '${{ secrets.GMAIL_CREDENTIALS }}' > config/credentials.json
        echo '${{ secrets.GMAIL_TOKEN }}' | base64 -d > config/token.pickle || echo "No token yet"
    
    - name: Setup environment
      run: |
        cat > .env << EOF
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        SMTP_USERNAME=${{ secrets.SMTP_USERNAME }}
        SMTP_PASSWORD=${{ secrets.SMTP_PASSWORD }}
        NOTIFICATION_EMAIL=${{ secrets.NOTIFICATION_EMAIL }}
        ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
        LOG_LEVEL=INFO
        EOF
    
    - name: Run monitor
      run: python src/main.py
    
    - name: Save token
      if: always()
      run: |
        if [ -f config/token.pickle ]; then
          echo "TOKEN_BASE64=$(base64 -w 0 config/token.pickle)" >> $GITHUB_ENV
        fi
```

4. **Encode and upload token**
```bash
# On your local machine, after first successful run
base64 config/token.pickle
# Copy output and add as GMAIL_TOKEN secret in GitHub
```

5. **Commit and push**
```bash
git add .github/workflows/monitor.yml
git commit -m "Add GitHub Actions workflow"
git push
```

**Note**: GitHub Actions has limitations:
- Minimum interval: 5 minutes (but often runs every 15+ due to queue)
- Maximum 6 hours of runtime per repository per day (free tier)

---

## Option 2: Railway.app (Easiest Paid Option)

**Pros**: Simple deployment, always running, good for beginners
**Cons**: ~$5/month

### Setup Steps

1. **Create `Procfile`**:
```
worker: python src/main.py --daemon --interval 300
```

2. **Sign up at [Railway.app](https://railway.app)**

3. **Deploy from GitHub**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python

4. **Add environment variables** in Railway dashboard:
   - All the variables from your `.env` file
   - `GMAIL_CREDENTIALS` - Content of credentials.json (as JSON string)

5. **Deploy** - Railway automatically builds and runs

**Cost**: ~$5/month after free trial

---

## Option 3: AWS Lambda + EventBridge

**Pros**: Free tier (1M requests/month), highly scalable
**Cons**: More complex setup, cold starts

### Setup Steps

1. **Install AWS CLI and SAM**:
```bash
pip install aws-sam-cli
aws configure
```

2. **Create `template.yaml`**:
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  GmailMonitorFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: src/lambda_handler.lambda_handler
      Runtime: python3.11
      Timeout: 300
      Environment:
        Variables:
          ANTHROPIC_API_KEY: !Ref AnthropicApiKey
          SMTP_USERNAME: !Ref SmtpUsername
          SMTP_PASSWORD: !Ref SmtpPassword
          NOTIFICATION_EMAIL: !Ref NotificationEmail
      Events:
        ScheduleEvent:
          Type: Schedule
          Properties:
            Schedule: rate(5 minutes)

Parameters:
  AnthropicApiKey:
    Type: String
    NoEcho: true
  SmtpUsername:
    Type: String
  SmtpPassword:
    Type: String
    NoEcho: true
  NotificationEmail:
    Type: String
```

3. **Create Lambda handler** - `src/lambda_handler.py`:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import main

def lambda_handler(event, context):
    """AWS Lambda handler"""
    try:
        main()
        return {
            'statusCode': 200,
            'body': 'Monitor ran successfully'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
```

4. **Package dependencies**:
```bash
pip install -r requirements.txt -t ./package
```

5. **Deploy**:
```bash
sam build
sam deploy --guided
```

**Note**: Credentials need to be stored in AWS Secrets Manager for security.

---

## Option 4: Google Cloud Run (Best for Gmail Integration)

**Pros**: Free tier, good Gmail API integration, runs in Google ecosystem
**Cons**: Requires Dockerfile knowledge

### Setup Steps

1. **Create `Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "src/main.py", "--daemon", "--interval", "300"]
```

2. **Enable Google Cloud Run API**:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com
```

3. **Build and deploy**:
```bash
gcloud run deploy gmail-monitor \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=xxx,SMTP_USERNAME=xxx,...
```

4. **Set up Cloud Scheduler** to trigger every 5 minutes:
```bash
gcloud scheduler jobs create http gmail-monitor-job \
  --schedule="*/5 * * * *" \
  --uri="https://gmail-monitor-xxx.run.app"
```

---

## Option 5: DigitalOcean Droplet (Full Control)

**Pros**: Full control, no limitations
**Cons**: Requires Linux knowledge, manual maintenance

### Setup Steps

1. **Create a $6/month Droplet** (Ubuntu 22.04)

2. **SSH and setup**:
```bash
ssh root@your-droplet-ip

# Install Python and dependencies
apt update
apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/yourusername/job-search-gmail-monitor.git
cd job-search-gmail-monitor

# Install dependencies
pip3 install -r requirements.txt

# Setup .env file
nano .env
# (paste your environment variables)

# Setup credentials
mkdir -p config
nano config/credentials.json
# (paste credentials)
```

3. **Create systemd service** - `/etc/systemd/system/gmail-monitor.service`:
```ini
[Unit]
Description=Gmail Job Search Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/job-search-gmail-monitor
ExecStart=/usr/bin/python3 src/main.py --daemon --interval 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

4. **Enable and start**:
```bash
systemctl enable gmail-monitor
systemctl start gmail-monitor
systemctl status gmail-monitor
```

5. **View logs**:
```bash
journalctl -u gmail-monitor -f
```

---

## Recommended Approach

**For beginners**: Start with **Railway.app** - simple setup, reliable, worth $5/month

**For free solution**: Use **GitHub Actions** with 15-minute intervals (good enough for most job searches)

**For advanced users**: Use **Google Cloud Run** - best integration with Gmail, free tier

---

## Testing Your Deployment

After deploying to any platform:

1. **Check logs** to ensure it's running
2. **Send a test email** to yourself matching your keywords
3. **Verify notification** arrives within expected time
4. **Monitor for 24 hours** to ensure stability

---

## Security Best Practices

1. **Never commit credentials** - Use environment variables or secrets managers
2. **Use app-specific passwords** for Gmail (not your main password)
3. **Enable 2FA** on all cloud accounts
4. **Rotate API keys** every 90 days
5. **Monitor cloud costs** (set up billing alerts)
6. **Review logs regularly** for errors or unauthorized access

---

## Troubleshooting

**Monitor not running on schedule**
- Check cloud platform logs
- Verify environment variables are set
- Ensure credentials are valid

**Gmail authentication fails**
- Re-generate OAuth token locally
- Upload fresh token to cloud platform
- Check credentials.json is properly formatted

**High cloud costs**
- Review execution frequency
- Check for infinite loops in logs
- Optimize email fetch size (reduce max_results)

**Notifications not received**
- Test SMTP credentials locally first
- Check spam folder
- Verify notification email is correct

---

## Need Help?

- Check [README.md](README.md) for general documentation
- Review cloud platform documentation
- Open an issue on GitHub with logs (redact sensitive data)

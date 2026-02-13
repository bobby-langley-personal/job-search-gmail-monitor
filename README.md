# Job Search Gmail Monitor

A smart email monitoring tool that helps you stay on top of job applications, interview requests, and recruiter outreach during your job search.

## Features

- 🔍 **Smart Detection**: Combines keyword matching, subject pattern analysis, and AI classification
- 📧 **Email Summaries**: Receive digestible email reports of job-related messages
- 📱 **SMS Alerts**: Optional SMS notifications for urgent interview requests
- ⚙️ **Configurable**: Easy customization via config file
- 🔒 **Secure**: Read-only Gmail access, credentials never committed

## Quick Start

### Prerequisites

- Python 3.8+
- Gmail account
- Google Cloud Project (free tier works fine)
- (Optional) AWS Account for cloud deployment

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/job-search-gmail-monitor.git
cd job-search-gmail-monitor
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Gmail API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Download credentials as `credentials.json` and place in `config/` directory

5. Configure settings:
```bash
cp config/settings.example.yaml config/settings.yaml
# Edit settings.yaml with your preferences
```

6. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Usage

Run the monitor:
```bash
python src/main.py
```

Run in daemon mode (checks periodically):
```bash
python src/main.py --daemon --interval 300  # Check every 5 minutes
```

## AWS Lambda Deployment (Run 24/7 in the Cloud)

Deploy to AWS Lambda for automatic monitoring without keeping your computer running.

### Why AWS Lambda?

- ✅ **Free Tier**: 1M requests/month free (you'll use ~60/month at 2x daily)
- ✅ **No Server Management**: AWS handles everything
- ✅ **Highly Reliable**: 99.95% uptime SLA
- ✅ **Auto-scaling**: Handles any load
- ✅ **Cost**: **$0/month** on free tier
- ✅ **Smart Schedule**: Runs at 8 AM and 8 PM EST to optimize API usage

### Setup Prerequisites

1. **AWS Account** (free tier eligible)
2. **AWS CLI** installed: `choco install awscli` (Windows) or from [aws.amazon.com/cli](https://aws.amazon.com/cli/)
3. **AWS SAM CLI** installed: `choco install aws-sam-cli` (Windows) or from [aws.amazon.com/serverless/sam](https://aws.amazon.com/serverless/sam/)
4. **Application working locally** (test with `python src/main.py`)

### Quick Deploy

1. **Configure AWS CLI**:
```powershell
aws configure
# Enter your AWS Access Key ID and Secret Access Key
# Default region: us-east-1
# Default output: json
```

2. **Deploy to Lambda**:
```powershell
.\deploy-aws.ps1
```

That's it! The script handles:
- Building the Lambda function
- Encoding credentials securely
- Deploying to AWS
- Setting up 2x daily schedule at 8 AM and 8 PM EST (via EventBridge)

### Monitoring Your Deployment

#### Manual Testing (On-Demand)
```powershell
.\test-lambda-manual.ps1
```

This triggers the function immediately, useful for testing without waiting for scheduled runs.

#### View Real-time Logs
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --tail
```

#### Test Manually
```powershell
aws lambda invoke --function-name job-search-gmail-monitor response.json
Get-Content response.json
```

#### Check Function Status
```powershell
aws lambda get-function --function-name job-search-gmail-monitor
```

### AWS Console Navigation

**Lambda Function**:
1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Find `job-search-gmail-monitor` function
3. Click "Monitor" tab → "View CloudWatch logs"

**CloudWatch Logs**:
1. Go to [CloudWatch Logs Console](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups)
2. Find `/aws/lambda/job-search-gmail-monitor`
3. Click latest log stream to see execution details

**EventBridge Schedule**:
1. Go to [EventBridge Console](https://console.aws.amazon.com/events/)
2. Click "Rules" in sidebar
3. Find rules with `job-search-gmail-monitor` in name
4. Verify "State: Enabled" and schedules:
   - Morning: "cron(0 13 * * ? *)" = 8 AM EST
   - Evening: "cron(0 1 * * ? *)" = 8 PM EST

### Understanding Lambda Execution

**What happens at 8 AM and 8 PM EST:**

1. **EventBridge triggers** Lambda function at scheduled times
2. **Lambda wakes up** and loads your credentials from environment variables
3. **Connects to Gmail** and fetches last 50 emails
4. **Classifies emails** using keywords and AI (if enabled)
5. **Detects deltas** - only processes NEW emails since last run
6. **Sends notification** email if new job-related emails found (excluding application confirmations)
7. **Saves state** to /tmp for next run
8. **Lambda shuts down** (no cost while idle)

**Costs per execution** (on free tier): $0

**Notifications**:
- Only sent when NEW job-related emails are found
- Filters out duplicate notifications automatically
- Excludes application submission confirmations
- Email timestamp shows YOUR local timezone

### Debugging Common Issues

#### Issue: No email notifications received

**Check 1 - Lambda is running:**
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --start-time '10min ago'
```
Look for: `[INFO] Identified X job-related emails`

**Check 2 - SMTP credentials:**
Look for errors like: `Failed to send email: (535, b'5.7.8 Username and Password not accepted')`

Fix: Verify `.env` has correct Gmail App Password (no spaces), then redeploy

**Check 3 - Schedule enabled:**
```powershell
aws events list-rules --query "Rules[?contains(Name, 'job-search-gmail-monitor')]"
```
Verify `State: ENABLED`

#### Issue: Lambda timing out

**Check execution time:**
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor | Select-String "Duration"
```

If > 30 seconds consistently, increase timeout in `template.yaml`:
```yaml
Globals:
  Function:
    Timeout: 600  # 10 minutes
```

#### Issue: AI classification failing

**Check logs for:**
```
[ERROR] AI classification error: Error code: 401 - invalid x-api-key
```

Fix: Update ANTHROPIC_API_KEY in `.env` and redeploy

#### Issue: Duplicate emails being sent

**Check state persistence:**
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor | Select-String "State:"
```

Look for: `State: {'total_seen': X, 'last_run': ...}`

If state resets frequently (cold starts), consider upgrading to S3-backed state storage.

### Updating Configuration

**Change keywords or settings:**
1. Edit `config/settings.yaml`
2. Redeploy: `.\deploy-aws.ps1`

**Change schedule times:**
Edit `template.yaml` cron expressions:
```yaml
MorningSchedule:
  Schedule: 'cron(0 13 * * ? *)'  # 8 AM EST = 1 PM UTC
EveningSchedule:
  Schedule: 'cron(0 1 * * ? *)'   # 8 PM EST = 1 AM UTC
```
Then redeploy.

**Test manually without waiting for schedule:**
```powershell
.\test-lambda-manual.ps1
```

**Update environment variables:**
1. Edit `.env` file locally
2. Redeploy: `.\deploy-aws.ps1`

### Cost Monitoring

**Set up billing alerts:**
1. Go to [AWS Billing Dashboard](https://console.aws.amazon.com/billing/)
2. Click "Budgets" → "Create budget"
3. Set threshold: $1 (you should never hit this)
4. Enter your email for alerts

**Expected monthly cost:** $0 (free tier covers everything)

**What uses free tier:**
- Lambda: ~60 invocations/month (2x daily)
- CloudWatch: ~10 MB logs/month
- EventBridge: 60 events/month (free forever)

### Advanced: Multi-Environment Setup

**Deploy to dev/staging/prod:**
```powershell
# Development
sam deploy --stack-name gmail-monitor-dev --parameter-overrides CheckIntervalMinutes=10

# Production
sam deploy --stack-name gmail-monitor-prod --parameter-overrides CheckIntervalMinutes=5
```

### Cleanup / Uninstall

**Remove from AWS:**
```powershell
aws cloudformation delete-stack --stack-name job-search-gmail-monitor
```

This removes:
- Lambda function
- EventBridge schedule
- CloudWatch log groups
- IAM roles

**Note:** Does not delete local files or Gmail credentials.

For more detailed deployment information, see [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md).

## Configuration

Edit `config/settings.yaml` to customize:

- Keywords to match
- Email subject patterns
- Notification preferences
- AI classification threshold
- Companies/domains to track

## Project Structure

```
job-search-gmail-monitor/
├── src/
│   ├── main.py              # Entry point
│   ├── gmail_client.py      # Gmail API wrapper
│   ├── classifier.py        # Email classification logic
│   ├── notifier.py          # Notification handlers
│   └── utils.py             # Helper functions
├── config/
│   ├── settings.yaml        # User configuration
│   └── credentials.json     # Gmail API credentials (gitignored)
├── tests/
│   └── test_classifier.py   # Unit tests
├── logs/                    # Application logs (gitignored)
├── .env                     # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

## Security Notes

- Never commit `credentials.json`, `.env`, or `token.pickle` files
- The app only requests read-only access to Gmail
- All sensitive data is stored locally

## Contributing

Pull requests welcome! Please ensure tests pass before submitting.

## License

MIT License - feel free to use and modify as needed.

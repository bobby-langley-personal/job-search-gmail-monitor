# AWS Lambda Deployment Guide

Deploy your Gmail monitor to AWS Lambda and run it 24/7 on the free tier!

## Why AWS Lambda?

- ✅ **Free Tier**: 1M requests/month free (you'll use ~8,640/month at 5-min intervals)
- ✅ **No Server Management**: AWS handles everything
- ✅ **Highly Reliable**: 99.95% uptime SLA
- ✅ **Auto-scaling**: Handles any load automatically
- ✅ **Pay-per-use**: Only pay when running (which is minimal)

## Prerequisites

1. AWS Account (free tier eligible)
2. AWS CLI installed and configured
3. AWS SAM CLI installed
4. Gmail credentials already set up locally
5. Application working locally (test with `python dry_run.py`)

---

## Installation Steps

### Step 1: Install AWS CLI

**Windows (PowerShell as Administrator):**
```powershell
# Using Chocolatey
choco install awscli

# OR download MSI installer from:
# https://aws.amazon.com/cli/
```

**Verify installation:**
```powershell
aws --version
```

### Step 2: Install AWS SAM CLI

**Windows (PowerShell as Administrator):**
```powershell
# Using Chocolatey
choco install aws-sam-cli

# OR download MSI installer from:
# https://aws.amazon.com/serverless/sam/
```

**Verify installation:**
```powershell
sam --version
```

### Step 3: Configure AWS CLI

```powershell
aws configure
```

You'll be asked for:
- **AWS Access Key ID**: Get from AWS Console → IAM → Users → Security credentials
- **AWS Secret Access Key**: Shown when you create the access key (save it!)
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

**To create access keys:**
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Click your name (top right) → Security credentials
3. Scroll to "Access keys" → Create access key
4. Choose "CLI" → Create
5. **Save both keys immediately** (you won't see the secret again!)

### Step 4: Prepare Your Application

Make sure these files exist and are configured:
- ✅ `config/credentials.json` (Gmail OAuth)
- ✅ `config/token.pickle` (Gmail token - run locally first)
- ✅ `config/settings.yaml` (your settings)
- ✅ `.env` (all environment variables)

**Test locally first:**
```powershell
python dry_run.py
```

If this works, you're ready to deploy!

---

## Deployment

### Automated Deployment (Easiest)

Simply run the deployment script:

```powershell
.\deploy-aws.ps1
```

This script will:
1. ✅ Check prerequisites
2. ✅ Encode credentials
3. ✅ Build the Lambda function
4. ✅ Deploy to AWS
5. ✅ Set up EventBridge schedule

**Deployment takes 3-5 minutes.**

---

### Manual Deployment (Advanced)

If you prefer manual control:

#### 1. Encode Credentials

```powershell
# Encode credentials.json
$credentialsContent = Get-Content "config\credentials.json" -Raw
$credentialsB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($credentialsContent))
Write-Output $credentialsB64

# Encode token.pickle
$tokenBytes = [System.IO.File]::ReadAllBytes("config\token.pickle")
$tokenB64 = [Convert]::ToBase64String($tokenBytes)
Write-Output $tokenB64
```

Save these base64 strings - you'll need them.

#### 2. Build

```powershell
sam build
```

#### 3. Deploy

```powershell
sam deploy \
  --stack-name job-search-gmail-monitor \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    AnthropicApiKey=YOUR_KEY \
    SmtpUsername=YOUR_EMAIL \
    SmtpPassword=YOUR_APP_PASSWORD \
    NotificationEmail=YOUR_EMAIL \
    GmailCredentials=BASE64_CREDENTIALS \
    GmailToken=BASE64_TOKEN \
    CheckIntervalMinutes=5 \
  --resolve-s3
```

Replace all the values with your actual credentials.

---

## Post-Deployment

### Verify Deployment

```powershell
# Check if function was created
aws lambda list-functions --query 'Functions[?FunctionName==`job-search-gmail-monitor`]'

# Check if schedule is enabled
aws events list-rules --name-prefix job-search-gmail-monitor
```

### Test the Function

**Invoke manually:**
```powershell
sam remote invoke GmailMonitorFunction --stack-name job-search-gmail-monitor
```

**View output:**
Should return:
```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Monitor check completed successfully\", ...}"
}
```

### View Logs

**Real-time logs:**
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --tail
```

**Specific time range:**
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --start-time '10min ago'
```

**In AWS Console:**
1. Go to [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/home#logsV2:log-groups)
2. Find `/aws/lambda/job-search-gmail-monitor`
3. View log streams

---

## Configuration

### Change Check Interval

Edit `template.yaml` and change `CheckIntervalMinutes`:
```yaml
Parameters:
  CheckIntervalMinutes:
    Default: 5  # Change this (1-60 minutes)
```

Then redeploy:
```powershell
.\deploy-aws.ps1
```

### Update Keywords/Settings

1. Edit `config/settings.yaml`
2. Redeploy:
```powershell
.\deploy-aws.ps1
```

### Update Environment Variables

Option 1 - Redeploy with new parameters:
```powershell
# Edit .env file, then:
.\deploy-aws.ps1
```

Option 2 - Update directly in AWS Console:
1. Go to Lambda → Functions → job-search-gmail-monitor
2. Configuration → Environment variables
3. Edit and save

---

## Monitoring & Management

### CloudWatch Dashboard

Create a dashboard to monitor your function:

1. Go to [CloudWatch](https://console.aws.amazon.com/cloudwatch/)
2. Create Dashboard → Add widget
3. Select:
   - Lambda Invocations
   - Lambda Errors
   - Lambda Duration

### Set Up Alarms

Get notified if the monitor fails:

```powershell
# Create SNS topic for alerts
aws sns create-topic --name gmail-monitor-alerts

# Subscribe your email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT:gmail-monitor-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Create CloudWatch alarm for errors
aws cloudwatch put-metric-alarm \
  --alarm-name gmail-monitor-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=job-search-gmail-monitor \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT:gmail-monitor-alerts
```

### Cost Monitoring

Set up billing alerts:

1. Go to [Billing Dashboard](https://console.aws.amazon.com/billing/)
2. Billing preferences → Receive Free Tier Usage Alerts
3. Set threshold: $1 (should never reach this)

**Expected cost**: $0/month (free tier covers everything)

---

## Troubleshooting

### Function Times Out

**Symptom**: Lambda times out after 5 minutes

**Solution**: Increase timeout in `template.yaml`:
```yaml
Globals:
  Function:
    Timeout: 600  # 10 minutes
```

### Gmail Authentication Fails

**Symptom**: "invalid_grant" or "credentials not found"

**Solution 1** - Regenerate token locally:
```powershell
# Delete old token
Remove-Item config\token.pickle

# Run locally to generate new one
python dry_run.py

# Redeploy
.\deploy-aws.ps1
```

**Solution 2** - Check credentials encoding:
```powershell
# Verify credentials.json is valid JSON
Get-Content config\credentials.json | ConvertFrom-Json
```

### AI Classification Not Working

**Symptom**: All emails classified as medium/low priority, no AI insights

**Solution**: Verify Anthropic API key:
```powershell
# Test locally first
python dry_run.py

# If it works locally, update Lambda env var:
aws lambda update-function-configuration \
  --function-name job-search-gmail-monitor \
  --environment Variables="{ANTHROPIC_API_KEY=sk-ant-...}"
```

### No Notifications Received

**Symptom**: Function runs but no emails/SMS received

**Solution 1** - Check SMTP settings:
```powershell
# Verify Gmail app password is correct
# Test locally first:
python src/main.py
```

**Solution 2** - Check CloudWatch logs:
```powershell
sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --tail
```

Look for "SMTP authentication failed" or similar errors.

### Function Not Triggering on Schedule

**Symptom**: Function works when invoked manually but not on schedule

**Solution**: Check EventBridge rule:
```powershell
# List rules
aws events list-rules

# Check if rule is enabled
aws events describe-rule --name job-search-gmail-monitor-<ID>

# If disabled, enable it:
aws events enable-rule --name job-search-gmail-monitor-<ID>
```

---

## Updating the Application

### Update Code

1. Make changes to your Python files
2. Redeploy:
```powershell
.\deploy-aws.ps1
```

### Update Dependencies

1. Edit `requirements.txt`
2. Redeploy:
```powershell
.\deploy-aws.ps1
```

---

## Cleanup / Deletion

To completely remove the application from AWS:

```powershell
# Delete CloudFormation stack (removes everything)
aws cloudformation delete-stack --stack-name job-search-gmail-monitor

# Verify deletion
aws cloudformation describe-stacks --stack-name job-search-gmail-monitor
```

Alternatively, in AWS Console:
1. Go to [CloudFormation](https://console.aws.amazon.com/cloudformation/)
2. Select `job-search-gmail-monitor` stack
3. Click Delete

This removes:
- Lambda function
- EventBridge schedule
- CloudWatch logs
- IAM roles

**Note**: This does NOT delete your Gmail credentials or local files.

---

## Cost Breakdown

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 8,640 invocations/month (5 min) | **$0** (Free: 1M/month) |
| Lambda | 43,200 seconds compute/month | **$0** (Free: 400,000 GB-sec) |
| CloudWatch Logs | ~100 MB/month | **$0** (Free: 5 GB) |
| EventBridge | 8,640 events/month | **$0** (Free forever) |
| **Total** | | **$0/month** |

You'll stay in free tier unless you:
- Run more frequently than every 2 minutes
- Have extremely long execution times (>5 min each)
- Store logs for >7 days

---

## Security Best Practices

1. **IAM Permissions**: Use least-privilege IAM roles (SAM does this automatically)
2. **Secrets**: Never commit credentials to Git
3. **Encryption**: Lambda environment variables are encrypted at rest
4. **API Keys**: Rotate regularly (every 90 days)
5. **Monitoring**: Set up CloudWatch alarms for failures
6. **VPC** (optional): Run Lambda in VPC for additional security

---

## Advanced Configuration

### Using AWS Secrets Manager

For better security, store credentials in Secrets Manager:

```powershell
# Store credentials
aws secretsmanager create-secret \
  --name gmail-monitor/credentials \
  --secret-string file://config/credentials.json

# Update Lambda to use Secrets Manager
# (requires code changes to fetch from Secrets Manager)
```

### Multiple Environments

Deploy to dev/staging/prod:

```powershell
# Development
sam deploy --stack-name gmail-monitor-dev --parameter-overrides Stage=dev

# Production
sam deploy --stack-name gmail-monitor-prod --parameter-overrides Stage=prod
```

---

## Support

**Issues?**
- Check CloudWatch logs first
- Review [GitHub Issues](https://github.com/yourusername/job-search-gmail-monitor/issues)
- Test locally with `python dry_run.py` to isolate issues

**Working locally but not in Lambda?**
- Check environment variables match
- Verify credentials are properly encoded
- Check Lambda timeout settings
- Review CloudWatch logs for specific errors

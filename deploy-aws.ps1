# AWS Lambda Deployment Script for Job Search Gmail Monitor
# Run this script to deploy the application to AWS Lambda

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AWS Lambda Deployment Script" -ForegroundColor Cyan
Write-Host "Job Search Gmail Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS SAM CLI is installed
Write-Host "Checking for AWS SAM CLI..." -ForegroundColor Yellow
try {
    $samVersion = sam --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SAM CLI found: $samVersion" -ForegroundColor Green
    } else {
        throw "SAM CLI not found"
    }
}
catch {
    Write-Host "AWS SAM CLI not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install AWS SAM CLI first:" -ForegroundColor Yellow
    Write-Host "  choco install aws-sam-cli" -ForegroundColor White
    Write-Host "  OR download from: https://aws.amazon.com/serverless/sam/" -ForegroundColor White
    exit 1
}

# Check if AWS CLI is configured
Write-Host "Checking AWS CLI configuration..." -ForegroundColor Yellow
try {
    $awsIdentity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "AWS CLI configured" -ForegroundColor Green
    } else {
        throw "AWS CLI not configured"
    }
}
catch {
    Write-Host "AWS CLI not configured!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please configure AWS CLI first:" -ForegroundColor Yellow
    Write-Host "  aws configure" -ForegroundColor White
    exit 1
}

# Encode credentials
Write-Host ""
Write-Host "Encoding credentials..." -ForegroundColor Yellow

$credentialsPath = Join-Path $PSScriptRoot "config\credentials.json"
$tokenPath = Join-Path $PSScriptRoot "config\token.pickle"

if (Test-Path $credentialsPath) {
    $credentialsContent = Get-Content $credentialsPath -Raw
    $credentialsB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($credentialsContent))
    Write-Host "credentials.json encoded" -ForegroundColor Green
} else {
    Write-Host "config\credentials.json not found!" -ForegroundColor Red
    Write-Host "Path checked: $credentialsPath" -ForegroundColor Gray
    exit 1
}

if (Test-Path $tokenPath) {
    $tokenBytes = [System.IO.File]::ReadAllBytes($tokenPath)
    $tokenB64 = [Convert]::ToBase64String($tokenBytes)
    Write-Host "token.pickle encoded" -ForegroundColor Green
} else {
    Write-Host "config\token.pickle not found - will authenticate on first run" -ForegroundColor Yellow
    $tokenB64 = ""
}

# Get environment variables
Write-Host ""
Write-Host "Loading environment variables from .env..." -ForegroundColor Yellow

if (Test-Path ".env") {
    $envVars = @{}
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $envVars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    Write-Host "Environment variables loaded" -ForegroundColor Green
} else {
    Write-Host ".env file not found!" -ForegroundColor Red
    exit 1
}

# Create parameter overrides
$parameters = @(
    "AnthropicApiKey=$($envVars['ANTHROPIC_API_KEY'])"
    "SmtpUsername=$($envVars['SMTP_USERNAME'])"
    "SmtpPassword=$($envVars['SMTP_PASSWORD'])"
    "NotificationEmail=$($envVars['NOTIFICATION_EMAIL'])"
    "GmailCredentials=$credentialsB64"
    "GmailToken=$tokenB64"
)

$parameterOverrides = $parameters -join " "

# Build the Lambda function
Write-Host ""
Write-Host "Building Lambda function..." -ForegroundColor Yellow
sam build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Build successful" -ForegroundColor Green

# Deploy
Write-Host ""
Write-Host "Deploying to AWS Lambda..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray

sam deploy `
    --stack-name job-search-gmail-monitor `
    --capabilities CAPABILITY_IAM `
    --parameter-overrides $parameterOverrides `
    --resolve-s3

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Gmail monitor is now running on AWS Lambda!" -ForegroundColor Cyan
    Write-Host "It will check for emails every 5 minutes." -ForegroundColor White
    Write-Host ""
    Write-Host "To view logs:" -ForegroundColor Yellow
    Write-Host "  sam logs -n GmailMonitorFunction --stack-name job-search-gmail-monitor --tail" -ForegroundColor White
    Write-Host ""
    Write-Host "To invoke manually:" -ForegroundColor Yellow
    Write-Host "  sam remote invoke GmailMonitorFunction --stack-name job-search-gmail-monitor" -ForegroundColor White
    Write-Host ""
    Write-Host "To update configuration:" -ForegroundColor Yellow
    Write-Host "  Edit config/settings.yaml and run this script again" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Deployment failed!" -ForegroundColor Red
    Write-Host "Check the error messages above for details." -ForegroundColor Yellow
    exit 1
}

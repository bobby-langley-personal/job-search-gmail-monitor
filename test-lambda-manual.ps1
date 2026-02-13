#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Manually invoke the Gmail monitor Lambda function for testing
    
.DESCRIPTION
    This script triggers the Lambda function on-demand, useful for testing
    without waiting for the scheduled runs at 8am/8pm.
    
.EXAMPLE
    .\test-lambda-manual.ps1
#>

param(
    [switch]$ShowLogs = $false,
    [switch]$WaitForCompletion = $true
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Gmail Monitor - Manual Test" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check AWS CLI is configured
try {
    $null = aws sts get-caller-identity 2>&1
    Write-Host "AWS CLI configured" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: AWS CLI not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

# Invoke Lambda function
Write-Host ""
Write-Host "Invoking Lambda function..." -ForegroundColor Yellow
Write-Host ""

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$outputFile = "test-output-$timestamp.json"

try {
    # Invoke the function
    aws lambda invoke `
        --function-name job-search-gmail-monitor `
        --log-type Tail `
        --output json `
        $outputFile | Out-Null
    
    if (Test-Path $outputFile) {
        Write-Host "Lambda invocation completed!" -ForegroundColor Green
        Write-Host ""
        
        # Display response
        Write-Host "Response:" -ForegroundColor Cyan
        $response = Get-Content $outputFile | ConvertFrom-Json
        
        if ($response.statusCode -eq 200) {
            $body = $response.body | ConvertFrom-Json
            Write-Host "  Status: SUCCESS" -ForegroundColor Green
            Write-Host "  Emails checked: $($body.emails_checked)" -ForegroundColor White
            Write-Host "  Job-related found: $($body.job_related_found)" -ForegroundColor White
            Write-Host "  New emails: $($body.new_emails)" -ForegroundColor White
        }
        else {
            Write-Host "  Status: ERROR" -ForegroundColor Red
            Write-Host "  Response: $($response.body)" -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "Full response saved to: $outputFile" -ForegroundColor Gray
    }
    else {
        Write-Host "ERROR: Lambda invocation failed - no output file created" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "ERROR: Failed to invoke Lambda function" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Show recent logs if requested
if ($ShowLogs) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Recent Lambda Logs" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    
    aws logs tail /aws/lambda/job-search-gmail-monitor --since 2m --format short
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Write-Host "To view live logs, run:" -ForegroundColor Gray
Write-Host "  aws logs tail /aws/lambda/job-search-gmail-monitor --follow" -ForegroundColor White
Write-Host ""

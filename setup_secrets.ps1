# Databricks Secrets Setup Script for Windows PowerShell
# This script helps you set up Databricks Secrets for secure token storage

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Databricks Secrets Setup (Windows)" -ForegroundColor Cyan
Write-Host "Hackathon Chatbot" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if databricks CLI is installed
$databricksInstalled = Get-Command databricks -ErrorAction SilentlyContinue

if (-not $databricksInstalled) {
    Write-Host "Error: Databricks CLI is not installed" -ForegroundColor Red
    Write-Host "Installing Databricks CLI..." -ForegroundColor Yellow
    pip install databricks-cli
    Write-Host "✓ Databricks CLI installed" -ForegroundColor Green
}
else {
    Write-Host "✓ Databricks CLI is installed" -ForegroundColor Green
}

Write-Host ""

# Check if configured
$configTest = databricks workspace ls / 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Databricks CLI not configured" -ForegroundColor Yellow
    Write-Host "Let's configure it now..." -ForegroundColor Yellow
    Write-Host ""
    databricks configure --token
    Write-Host "✓ Databricks CLI configured" -ForegroundColor Green
    Write-Host ""
}

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Step 1: Create Secret Scope" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# Check if scope exists
$scopes = databricks secrets list-scopes 2>&1 | Out-String
if ($scopes -match "hackathon-chatbot") {
    Write-Host "Secret scope 'hackathon-chatbot' already exists" -ForegroundColor Yellow
}
else {
    Write-Host "Creating secret scope 'hackathon-chatbot'..." -ForegroundColor White
    databricks secrets create-scope hackathon-chatbot
    Write-Host "✓ Secret scope created" -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Step 2: Add Databricks Token to Secrets" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

Write-Host "You need to add your Databricks token to the secret scope." -ForegroundColor White
Write-Host ""
Write-Host "To get a token:" -ForegroundColor Cyan
Write-Host "1. Go to your Databricks workspace" -ForegroundColor White
Write-Host "2. Click your username (top right)" -ForegroundColor White
Write-Host "3. Select 'User Settings'" -ForegroundColor White
Write-Host "4. Go to 'Access Tokens' tab" -ForegroundColor White
Write-Host "5. Click 'Generate New Token'" -ForegroundColor White
Write-Host "6. Copy the token" -ForegroundColor White
Write-Host ""

$hasToken = Read-Host "Do you have a token ready? (y/N)"

if ($hasToken -match "^[Yy]$") {
    Write-Host ""
    Write-Host "Opening editor to enter your token..." -ForegroundColor Yellow
    Write-Host "Paste your token, save (Ctrl+S), and close the editor (Ctrl+Q or Alt+F4)." -ForegroundColor Yellow
    Write-Host ""
    Start-Sleep -Seconds 2
    
    databricks secrets put-secret hackathon-chatbot databricks-token
    
    Write-Host ""
    Write-Host "✓ Token stored in Databricks Secrets" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Please generate a token first, then run this script again" -ForegroundColor Yellow
    Write-Host "Or manually add it:" -ForegroundColor White
    Write-Host "  databricks secrets put-secret hackathon-chatbot databricks-token" -ForegroundColor Cyan
    exit
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Step 3: Verify Setup" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# List secrets
Write-Host "Secrets in scope:" -ForegroundColor White
databricks secrets list --scope hackathon-chatbot

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your Databricks token is now stored securely." -ForegroundColor White
Write-Host ""
Write-Host "What's configured:" -ForegroundColor Cyan
Write-Host "  Scope: hackathon-chatbot" -ForegroundColor White
Write-Host "  Secret: databricks-token" -ForegroundColor White
Write-Host ""
Write-Host "The notebook will automatically use this secret." -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open your Databricks workspace" -ForegroundColor White
Write-Host "2. Navigate to your repository" -ForegroundColor White
Write-Host "3. Open databricks_backend_notebook.py" -ForegroundColor White
Write-Host "4. Run all cells" -ForegroundColor White
Write-Host ""
Write-Host "The code will automatically retrieve the token from secrets!" -ForegroundColor Green
Write-Host ""

# Create summary
$summary = @"
Databricks Secrets Setup Summary
=================================

Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Configuration:
- Scope Name: hackathon-chatbot
- Secret Key: databricks-token
- Status: ✓ Configured

Access the secret in code:
  token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")

Manage secrets:
  # List scopes
  databricks secrets list-scopes
  
  # List secrets in scope
  databricks secrets list --scope hackathon-chatbot
  
  # Update secret
  databricks secrets put-secret hackathon-chatbot databricks-token
  
  # Delete secret
  databricks secrets delete-secret hackathon-chatbot databricks-token

Security Notes:
- ✓ Token is encrypted at rest
- ✓ Never appears in logs or code
- ✓ Access is audited
- ✓ Can be rotated easily

Next Steps:
1. Open Databricks notebook
2. Run all cells
3. Token will be retrieved automatically

For more information, see: SECRETS_SETUP.md
"@

$summary | Out-File -FilePath "secrets_setup_summary.txt" -Encoding UTF8

Write-Host "Setup summary saved to: secrets_setup_summary.txt" -ForegroundColor Cyan
Write-Host ""


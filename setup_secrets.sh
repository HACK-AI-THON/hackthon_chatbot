#!/bin/bash

# Databricks Secrets Setup Script
# This script helps you set up Databricks Secrets for secure token storage

set -e

echo "=========================================="
echo "Databricks Secrets Setup"
echo "Hackathon Chatbot"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${RED}Error: Databricks CLI is not installed${NC}"
    echo "Installing Databricks CLI..."
    pip install databricks-cli
    echo -e "${GREEN}✓ Databricks CLI installed${NC}"
fi

echo -e "${GREEN}✓ Databricks CLI is installed${NC}"
echo ""

# Check if configured
if ! databricks workspace ls / &> /dev/null; then
    echo -e "${YELLOW}Databricks CLI not configured${NC}"
    echo "Let's configure it now..."
    echo ""
    databricks configure --token
    echo -e "${GREEN}✓ Databricks CLI configured${NC}"
    echo ""
fi

echo -e "${BLUE}=========================================="
echo "Step 1: Create Secret Scope"
echo "==========================================${NC}"
echo ""

# Check if scope exists
if databricks secrets list-scopes | grep -q "hackathon-chatbot"; then
    echo -e "${YELLOW}Secret scope 'hackathon-chatbot' already exists${NC}"
else
    echo "Creating secret scope 'hackathon-chatbot'..."
    databricks secrets create-scope hackathon-chatbot
    echo -e "${GREEN}✓ Secret scope created${NC}"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Step 2: Add Databricks Token to Secrets"
echo "==========================================${NC}"
echo ""

echo "You need to add your Databricks token to the secret scope."
echo ""
echo "To get a token:"
echo "1. Go to your Databricks workspace"
echo "2. Click your username (top right)"
echo "3. Select 'User Settings'"
echo "4. Go to 'Access Tokens' tab"
echo "5. Click 'Generate New Token'"
echo "6. Copy the token"
echo ""

read -p "Do you have a token ready? (y/N): " has_token

if [[ $has_token =~ ^[Yy]$ ]]; then
    echo ""
    echo "Opening editor to enter your token..."
    echo "Paste your token, save, and close the editor."
    echo ""
    sleep 2
    
    databricks secrets put-secret hackathon-chatbot databricks-token
    
    echo ""
    echo -e "${GREEN}✓ Token stored in Databricks Secrets${NC}"
else
    echo ""
    echo -e "${YELLOW}Please generate a token first, then run this script again${NC}"
    echo "Or manually add it:"
    echo "  databricks secrets put-secret hackathon-chatbot databricks-token"
    exit 0
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Step 3: Verify Setup"
echo "==========================================${NC}"
echo ""

# List secrets
echo "Secrets in scope:"
databricks secrets list --scope hackathon-chatbot

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Your Databricks token is now stored securely."
echo ""
echo "What's configured:"
echo "  Scope: hackathon-chatbot"
echo "  Secret: databricks-token"
echo ""
echo "The notebook will automatically use this secret."
echo ""
echo "Next steps:"
echo "1. Open your Databricks workspace"
echo "2. Navigate to your repository"
echo "3. Open databricks_backend_notebook.py"
echo "4. Run all cells"
echo ""
echo "The code will automatically retrieve the token from secrets!"
echo ""

# Create summary
cat > secrets_setup_summary.txt << EOF
Databricks Secrets Setup Summary
=================================

Date: $(date)

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
EOF

echo "Setup summary saved to: secrets_setup_summary.txt"
echo ""


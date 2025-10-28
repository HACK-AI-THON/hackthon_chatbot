#!/bin/bash

# Databricks Setup Script for Hackathon Chatbot
# This script helps set up the Databricks environment

set -e

echo "=========================================="
echo "Databricks Setup - Hackathon Chatbot"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if databricks CLI is installed
if ! command -v databricks &> /dev/null; then
    echo -e "${YELLOW}Databricks CLI not found. Installing...${NC}"
    pip install databricks-cli
    echo -e "${GREEN}✓ Databricks CLI installed${NC}"
fi

echo ""
echo "This script will help you:"
echo "1. Configure Databricks CLI"
echo "2. Upload backend files to Databricks workspace"
echo "3. Create necessary DBFS directories"
echo ""

read -p "Continue? (y/N): " continue_setup
if [[ ! $continue_setup =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Configure Databricks CLI
echo ""
echo -e "${YELLOW}Step 1: Configure Databricks CLI${NC}"
echo "You'll need:"
echo "  - Your Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)"
echo "  - A personal access token (generate in User Settings > Access Tokens)"
echo ""
read -p "Configure now? (y/N): " configure_cli

if [[ $configure_cli =~ ^[Yy]$ ]]; then
    databricks configure --token
    echo -e "${GREEN}✓ Databricks CLI configured${NC}"
else
    echo "Skipped CLI configuration"
fi

# Get username for workspace paths
echo ""
read -p "Enter your Databricks username (email): " username

if [ -z "$username" ]; then
    echo -e "${RED}Username is required${NC}"
    exit 1
fi

# Create workspace directories
echo ""
echo -e "${YELLOW}Step 2: Creating workspace directories${NC}"

workspace_path="/Users/$username/hackathon-chatbot"

databricks workspace mkdirs "$workspace_path/backend" || true
echo -e "${GREEN}✓ Created $workspace_path/backend${NC}"

# Upload backend files
echo ""
echo -e "${YELLOW}Step 3: Uploading backend files${NC}"

files=("main.py" "chat_handler.py" "knowledge_base.py" "document_processor.py" "__init__.py")

for file in "${files[@]}"; do
    if [ -f "backend/$file" ]; then
        echo "Uploading backend/$file..."
        databricks workspace import "backend/$file" "$workspace_path/backend/$file" --language PYTHON --overwrite
        echo -e "${GREEN}✓ Uploaded $file${NC}"
    else
        echo -e "${YELLOW}⚠ File backend/$file not found, skipping${NC}"
    fi
done

# Upload requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Uploading requirements.txt..."
    databricks workspace import "requirements.txt" "$workspace_path/requirements.txt" --overwrite
    echo -e "${GREEN}✓ Uploaded requirements.txt${NC}"
fi

# Create DBFS directories
echo ""
echo -e "${YELLOW}Step 4: Creating DBFS directories${NC}"

databricks fs mkdirs "dbfs:/FileStore/hackathon-chatbot/uploads"
databricks fs mkdirs "dbfs:/FileStore/hackathon-chatbot/simple_db"

echo -e "${GREEN}✓ Created DBFS directories${NC}"

# Upload sample documents if they exist
echo ""
read -p "Upload sample documents from uploads/ folder? (y/N): " upload_docs

if [[ $upload_docs =~ ^[Yy]$ ]]; then
    if [ -d "uploads" ]; then
        for file in uploads/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                echo "Uploading $filename..."
                databricks fs cp "$file" "dbfs:/FileStore/hackathon-chatbot/uploads/$filename" --overwrite
                echo -e "${GREEN}✓ Uploaded $filename${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ uploads/ directory not found${NC}"
    fi
fi

# Upload the notebook
echo ""
echo -e "${YELLOW}Step 5: Uploading Databricks notebook${NC}"

if [ -f "databricks_backend_notebook.py" ]; then
    databricks workspace import "databricks_backend_notebook.py" "$workspace_path/Hackathon_Chatbot_Backend" --language PYTHON --overwrite
    echo -e "${GREEN}✓ Uploaded notebook${NC}"
else
    echo -e "${YELLOW}⚠ databricks_backend_notebook.py not found${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Databricks workspace"
echo "2. Navigate to: $workspace_path"
echo "3. Open 'Hackathon_Chatbot_Backend' notebook"
echo "4. Attach to a cluster (or create a new one)"
echo "5. Run all cells in the notebook"
echo "6. Get the driver proxy URL from the notebook output"
echo "7. Update your frontend with the API URL"
echo ""
echo "Documentation:"
echo "  - See DATABRICKS_DEPLOYMENT.md for detailed instructions"
echo ""
echo "=========================================="

# Create a summary file
cat > databricks_setup_summary.txt << EOF
Databricks Setup Summary
========================

Date: $(date)
Username: $username
Workspace Path: $workspace_path

Files Uploaded:
- Backend files: $workspace_path/backend/
- Notebook: $workspace_path/Hackathon_Chatbot_Backend

DBFS Directories:
- dbfs:/FileStore/hackathon-chatbot/uploads
- dbfs:/FileStore/hackathon-chatbot/simple_db

Next Steps:
1. Open Databricks workspace
2. Navigate to $workspace_path
3. Open Hackathon_Chatbot_Backend notebook
4. Attach to cluster and run all cells
5. Get driver proxy URL from notebook output
6. Update frontend configuration with API URL

Useful Commands:
- List workspace files: databricks workspace ls $workspace_path
- List DBFS files: databricks fs ls dbfs:/FileStore/hackathon-chatbot/
- View notebook: databricks workspace export_dir $workspace_path ./export

For more help, see DATABRICKS_DEPLOYMENT.md
EOF

echo ""
echo "Setup summary saved to: databricks_setup_summary.txt"
echo ""


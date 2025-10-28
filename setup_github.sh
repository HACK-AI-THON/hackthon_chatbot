#!/bin/bash

# GitHub Repository Setup Script
# This script helps initialize and push your code to a new GitHub repository

set -e

echo "=========================================="
echo "GitHub Repository Setup"
echo "Hackathon Chatbot"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed${NC}"
    echo "Please install Git first: https://git-scm.com/downloads"
    exit 1
fi

echo -e "${GREEN}✓ Git is installed${NC}"
echo ""

# Check if already a git repository
if [ -d ".git" ]; then
    echo -e "${YELLOW}Warning: This directory is already a git repository${NC}"
    read -p "Do you want to continue anyway? (y/N): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi
    REINIT=true
else
    REINIT=false
fi

# Instructions for creating GitHub repository
echo -e "${BLUE}=========================================="
echo "Step 1: Create GitHub Repository"
echo "==========================================${NC}"
echo ""
echo "Please follow these steps to create a new repository on GitHub:"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Enter repository name: 'hackathon-chatbot' (or your preferred name)"
echo "3. Add description: 'AI-powered RAG chatbot for hackathons'"
echo "4. Choose visibility: Public or Private"
echo "5. DO NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo "7. Copy the repository URL (it will look like: https://github.com/username/hackathon-chatbot.git)"
echo ""
read -p "Press Enter after you've created the repository..."
echo ""

# Get repository URL
echo -e "${YELLOW}Enter your GitHub repository URL:${NC}"
echo "Example: https://github.com/username/hackathon-chatbot.git"
echo "Or: git@github.com:username/hackathon-chatbot.git"
read -p "Repository URL: " repo_url

if [ -z "$repo_url" ]; then
    echo -e "${RED}Error: Repository URL is required${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Step 2: Initialize Local Repository"
echo "==========================================${NC}"
echo ""

# Initialize git repository
if [ "$REINIT" = false ]; then
    echo "Initializing git repository..."
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${YELLOW}Using existing git repository${NC}"
fi

# Configure git if not configured
if [ -z "$(git config user.name)" ]; then
    echo ""
    read -p "Enter your name for git commits: " git_name
    git config user.name "$git_name"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "Enter your email for git commits: " git_email
    git config user.email "$git_email"
fi

echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Create .gitkeep files for empty directories
echo "Creating .gitkeep files for empty directories..."
touch uploads/.gitkeep
touch simple_db/.gitkeep
echo -e "${GREEN}✓ Directory structure preserved${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "Step 3: Add Files to Git"
echo "==========================================${NC}"
echo ""

# Add all files
echo "Adding files to git..."
git add .

# Show status
echo ""
echo "Files to be committed:"
git status --short

echo ""
read -p "Proceed with these files? (y/N): " proceed
if [[ ! $proceed =~ ^[Yy]$ ]]; then
    echo "Aborted"
    exit 0
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Step 4: Create Initial Commit"
echo "==========================================${NC}"
echo ""

# Create commit
echo "Creating initial commit..."
git commit -m "Initial commit: Hackathon Chatbot RAG application

Features:
- FastAPI backend with RAG implementation
- React frontend with chat interface
- Databricks LLM integration
- Document upload and processing (PDF, DOCX)
- Vector-based semantic search
- Comprehensive Databricks deployment guides

Tech Stack:
- Backend: Python, FastAPI, Sentence Transformers
- Frontend: React, Vite, Axios
- AI: Databricks Llama 4 Maverick
- Deployment: Databricks notebooks and apps"

echo -e "${GREEN}✓ Initial commit created${NC}"
echo ""

echo -e "${BLUE}=========================================="
echo "Step 5: Add Remote and Push"
echo "==========================================${NC}"
echo ""

# Add remote
echo "Adding remote repository..."
if git remote | grep -q origin; then
    echo "Updating existing origin remote..."
    git remote set-url origin "$repo_url"
else
    git remote add origin "$repo_url"
fi

echo -e "${GREEN}✓ Remote repository added${NC}"
echo ""

# Get default branch name
default_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")

# Push to GitHub
echo "Pushing to GitHub..."
echo -e "${YELLOW}Note: You may be prompted for GitHub credentials${NC}"
echo ""

if git push -u origin "$default_branch"; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ Successfully Pushed to GitHub!"
    echo "==========================================${NC}"
    echo ""
    echo "Your repository is now available at:"
    # Extract repo URL without .git
    repo_web_url="${repo_url%.git}"
    echo -e "${BLUE}$repo_web_url${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Visit your repository on GitHub"
    echo "2. Add a LICENSE file if needed"
    echo "3. Enable GitHub Pages for documentation (optional)"
    echo "4. Set up branch protection rules (optional)"
    echo "5. Add collaborators if working in a team"
    echo ""
    echo "To make changes and push updates:"
    echo "  git add ."
    echo "  git commit -m 'Your commit message'"
    echo "  git push"
    echo ""
else
    echo ""
    echo -e "${RED}=========================================="
    echo "Push Failed"
    echo "==========================================${NC}"
    echo ""
    echo "Common issues and solutions:"
    echo ""
    echo "1. Authentication failed:"
    echo "   - Use a Personal Access Token instead of password"
    echo "   - Generate token at: https://github.com/settings/tokens"
    echo "   - Use: git push -u origin $default_branch"
    echo ""
    echo "2. Repository already has content:"
    echo "   - Pull first: git pull origin $default_branch --allow-unrelated-histories"
    echo "   - Then push: git push -u origin $default_branch"
    echo ""
    echo "3. Using SSH but keys not set up:"
    echo "   - Switch to HTTPS, or"
    echo "   - Set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
    echo ""
    exit 1
fi

# Create a summary file
cat > git_setup_summary.txt << EOF
Git Setup Summary
=================

Date: $(date)
Repository: $repo_url
Branch: $default_branch

Local Configuration:
- Git user: $(git config user.name)
- Git email: $(git config user.email)

Repository Details:
- Remote: origin
- URL: $repo_url
- Branch: $default_branch

Files Committed:
- Backend: FastAPI application with RAG
- Frontend: React chat interface
- Deployment: Databricks guides and scripts
- Documentation: README.md and guides

Next Steps:
1. Visit your repository on GitHub
2. Review the README.md
3. Set up deployment following DATABRICKS_DEPLOYMENT.md
4. Add collaborators if needed

Useful Git Commands:
- View status: git status
- View log: git log --oneline
- Create branch: git checkout -b feature-name
- Push changes: git add . && git commit -m "message" && git push
- Pull updates: git pull origin $default_branch

For deployment help, see:
- README_DEPLOYMENT.md (Quick start)
- DATABRICKS_DEPLOYMENT.md (Complete guide)
EOF

echo ""
echo "Setup summary saved to: git_setup_summary.txt"
echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete! 🎉"
echo "==========================================${NC}"
echo ""


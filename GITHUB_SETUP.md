# GitHub Setup Guide

This guide will help you create a new GitHub repository and push your Hackathon Chatbot code to it.

---

## 🚀 Quick Setup (Automated)

### Option 1: Use the Setup Script (Recommended)

```bash
# Make the script executable
chmod +x setup_github.sh

# Run the setup script
./setup_github.sh
```

The script will:
1. ✅ Check if Git is installed
2. ✅ Initialize a local Git repository
3. ✅ Configure Git (if not already configured)
4. ✅ Add all project files
5. ✅ Create initial commit
6. ✅ Prompt you for the GitHub repository URL
7. ✅ Push to GitHub

---

## 📖 Manual Setup (Step by Step)

### Step 1: Create GitHub Repository

1. Go to [https://github.com/new](https://github.com/new)
2. Fill in repository details:
   - **Repository name**: `hackathon-chatbot` (or your preferred name)
   - **Description**: `AI-powered RAG chatbot for hackathons`
   - **Visibility**: Choose Public or Private
   - **⚠️ IMPORTANT**: Do NOT initialize with README, .gitignore, or license
3. Click "Create repository"
4. Copy the repository URL (will be shown on the next page)

### Step 2: Initialize Local Git Repository

```bash
# Navigate to your project directory
cd /path/to/Hackthon_Chatbot

# Initialize git repository
git init

# Configure git (if not already configured)
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 3: Add Files to Git

```bash
# Create .gitkeep files for empty directories
touch uploads/.gitkeep
touch simple_db/.gitkeep

# Add all files to staging
git add .

# Check what will be committed
git status
```

### Step 4: Create Initial Commit

```bash
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
```

### Step 5: Add Remote and Push

```bash
# Add remote repository (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/hackathon-chatbot.git

# Push to GitHub
git push -u origin main

# If your default branch is 'master' instead of 'main':
# git push -u origin master
```

---

## 🔐 Authentication Methods

### Method 1: Personal Access Token (Recommended)

1. Go to [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "Hackathon Chatbot Repo"
4. Select scopes: `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)
7. When pushing, use the token as password:
   - Username: your GitHub username
   - Password: the token you just generated

### Method 2: SSH Keys

1. Generate SSH key:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```

2. Add to ssh-agent:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

3. Copy public key:
```bash
cat ~/.ssh/id_ed25519.pub
```

4. Add to GitHub:
   - Go to [https://github.com/settings/keys](https://github.com/settings/keys)
   - Click "New SSH key"
   - Paste your public key
   - Save

5. Use SSH URL for remote:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/hackathon-chatbot.git
```

---

## 📁 What Gets Committed

The `.gitignore` file excludes:

### ✅ **Included in Repository:**
- All source code (backend & frontend)
- Configuration files
- Documentation (README, guides)
- Deployment scripts
- Sample configuration files
- Directory structure markers (.gitkeep)

### ❌ **Excluded from Repository:**
- `node_modules/` (frontend dependencies)
- `__pycache__/` (Python cache)
- `.env` files (environment variables)
- `uploads/*` (uploaded documents)
- `simple_db/*.pkl` and `simple_db/*.json` (knowledge base data)
- IDE settings (.vscode, .idea)
- Build artifacts (dist/, build/)
- Log files

---

## 🔧 Repository Settings (After Push)

### 1. Add Description and Topics

Go to repository settings and add:
- **Description**: "AI-powered RAG chatbot with Databricks LLM integration"
- **Topics**: `chatbot`, `rag`, `databricks`, `fastapi`, `react`, `llm`, `ai`, `hackathon`

### 2. Enable GitHub Pages (Optional)

For documentation hosting:
1. Go to Settings → Pages
2. Source: Deploy from branch `main`
3. Folder: `/docs` or `/(root)`
4. Save

### 3. Set Branch Protection Rules (Recommended)

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Include administrators

### 4. Add Collaborators

1. Go to Settings → Collaborators
2. Add team members
3. Set permissions (Write, Maintain, or Admin)

---

## 🔄 Making Changes and Pushing Updates

### Daily Workflow

```bash
# 1. Check status
git status

# 2. Add changes
git add .

# 3. Commit with descriptive message
git commit -m "Add feature: document metadata display"

# 4. Push to GitHub
git push

# 5. Pull latest changes (if working in a team)
git pull
```

### Creating a Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/new-feature-name

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push to GitHub
git push -u origin feature/new-feature-name

# Create Pull Request on GitHub
```

### Syncing with Remote

```bash
# Fetch latest changes
git fetch origin

# Pull and merge
git pull origin main

# View remote branches
git branch -r
```

---

## 🐛 Troubleshooting

### Issue: "Permission denied (publickey)"

**Solution:** Set up SSH keys (see Method 2 above) or use HTTPS with Personal Access Token

### Issue: "Repository not found"

**Solution:** 
- Check the repository URL is correct
- Ensure you have access to the repository
- Try: `git remote -v` to see configured remotes

### Issue: "Failed to push some refs"

**Solution:**
```bash
# Pull first (if repository has content)
git pull origin main --allow-unrelated-histories

# Then push
git push -u origin main
```

### Issue: "Authentication failed"

**Solution:**
- Use Personal Access Token instead of password
- Generate token at: https://github.com/settings/tokens
- Use token as password when prompted

### Issue: "Large files detected"

**Solution:**
```bash
# If you accidentally added large files
git rm --cached path/to/large/file
git commit --amend
git push --force-with-lease
```

### Issue: Want to change remote URL

**Solution:**
```bash
# Change from HTTPS to SSH (or vice versa)
git remote set-url origin git@github.com:username/repo.git

# Verify
git remote -v
```

---

## 📊 Repository Structure

After pushing, your GitHub repository will look like this:

```
hackathon-chatbot/
├── .github/              # GitHub workflows (if added)
├── backend/              # Backend Python code
│   ├── main.py
│   ├── chat_handler.py
│   ├── knowledge_base.py
│   └── document_processor.py
├── frontend/             # Frontend React code
│   ├── src/
│   ├── public/
│   └── package.json
├── uploads/              # (empty, just .gitkeep)
├── simple_db/            # (empty, just .gitkeep)
├── databricks_backend_notebook.py
├── databricks_setup.sh
├── setup_github.sh
├── DATABRICKS_DEPLOYMENT.md
├── README_DEPLOYMENT.md
├── README.md
├── requirements.txt
├── .gitignore
└── GITHUB_SETUP.md
```

---

## 📝 Commit Message Guidelines

### Good Commit Messages

✅ **Do:**
```bash
git commit -m "Add document deletion feature to API"
git commit -m "Fix: Resolve CORS issue for production deployment"
git commit -m "Update README with deployment instructions"
git commit -m "Refactor: Optimize vector search performance"
```

❌ **Don't:**
```bash
git commit -m "updates"
git commit -m "fix"
git commit -m "stuff"
git commit -m "asdfasdf"
```

### Commit Message Format

```
<type>: <subject>

<body> (optional)

<footer> (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

---

## 🎯 Post-Setup Checklist

After successfully pushing to GitHub:

- [ ] Repository is visible on GitHub
- [ ] README.md displays correctly
- [ ] All files are present (check file tree)
- [ ] `.gitignore` is working (no node_modules, __pycache__, etc.)
- [ ] Repository description and topics added
- [ ] License file added (if needed)
- [ ] Collaborators invited (if working in a team)
- [ ] Branch protection rules set (if needed)
- [ ] README.md links work correctly
- [ ] GitHub Pages enabled (optional)

---

## 🌟 Useful Git Commands

### Information
```bash
git status                    # Check status
git log --oneline            # View commit history
git remote -v                # View remotes
git branch -a                # View all branches
git diff                     # View changes
```

### Branching
```bash
git checkout -b new-branch   # Create and switch to branch
git branch                   # List branches
git merge branch-name        # Merge branch
git branch -d branch-name    # Delete branch
```

### Undoing Changes
```bash
git checkout -- file.txt     # Discard changes in file
git reset HEAD file.txt      # Unstage file
git reset --soft HEAD~1      # Undo last commit (keep changes)
git reset --hard HEAD~1      # Undo last commit (discard changes)
```

### Syncing
```bash
git fetch origin             # Fetch changes
git pull origin main         # Pull and merge
git push origin main         # Push commits
git push --tags              # Push tags
```

---

## 📚 Additional Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Pro Git Book](https://git-scm.com/book/en/v2)

---

## ✅ Success!

Once you've completed the setup, your code is now:
- ✅ Backed up on GitHub
- ✅ Version controlled
- ✅ Accessible from anywhere
- ✅ Ready for collaboration
- ✅ Professional and shareable

**Your repository URL:**
```
https://github.com/YOUR_USERNAME/hackathon-chatbot
```

Share this URL with:
- Team members
- Hackathon organizers
- Potential employers
- On your resume/portfolio

---

**Happy coding! 🚀**


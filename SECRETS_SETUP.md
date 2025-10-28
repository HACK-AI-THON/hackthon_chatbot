# Databricks Secrets Setup Guide

This guide shows you how to securely store your Databricks token using **Databricks Secrets**.

---

## 🔐 Why Use Databricks Secrets?

✅ **Secure** - Tokens never appear in code or notebooks  
✅ **Encrypted** - Secrets are encrypted at rest  
✅ **Access Controlled** - Only authorized users can access  
✅ **Auditable** - All access is logged  
❌ **NEVER** hardcode tokens in code files!

---

## 📝 Step 1: Generate a New Databricks Token

1. Go to your Databricks workspace
2. Click your **username** (top right corner)
3. Select **User Settings**
4. Click **Access Tokens** tab
5. Click **Generate New Token**
6. Configure:
   - **Comment**: `Hackathon Chatbot - Secure`
   - **Lifetime**: 90 days (or less for security)
7. Click **Generate**
8. **COPY THE TOKEN** (you'll only see it once!)
9. Save it temporarily in a secure location (password manager)

---

## 🔧 Step 2: Create Secret Scope (One-Time Setup)

### Method A: Using Databricks CLI

```bash
# Install Databricks CLI if not already installed
pip install databricks-cli

# Configure CLI (if not already done)
databricks configure --token

# Create secret scope
databricks secrets create-scope hackathon-chatbot

# Verify scope was created
databricks secrets list-scopes
```

### Method B: Using Databricks UI

1. Go to: `https://<your-workspace>.cloud.databricks.com/#secrets/createScope`
2. **Scope Name**: `hackathon-chatbot`
3. **Manage Principal**: Select who can manage secrets
4. Click **Create**

---

## 🔑 Step 3: Store Your Token in Secrets

### Method A: Using Databricks CLI

```bash
# Add your token to the secret scope
databricks secrets put-secret hackathon-chatbot databricks-token

# This will open a text editor
# Paste your token, save, and close the editor

# Verify the secret was created (won't show the value)
databricks secrets list --scope hackathon-chatbot
```

### Method B: Using Databricks UI (if available)

1. Go to your workspace settings
2. Navigate to Secrets
3. Select scope: `hackathon-chatbot`
4. Click **Add Secret**
5. **Key**: `databricks-token`
6. **Value**: Paste your token
7. Click **Save**

---

## 📓 Step 4: Use Secrets in Your Notebook

The code is already configured! In the Databricks notebook, it will automatically:

```python
# The notebook code already includes this:
try:
    # Get token from Databricks secrets
    self.access_token = dbutils.secrets.get(
        scope="hackathon-chatbot", 
        key="databricks-token"
    )
    print("✅ Using Databricks Secrets for authentication")
except:
    print("⚠️ WARNING: No DATABRICKS_TOKEN found!")
```

---

## 🧪 Step 5: Verify Setup

### Test in a Databricks Notebook Cell:

```python
# Run this in a notebook cell to verify
try:
    token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")
    print("✅ Secret retrieved successfully!")
    print(f"Token starts with: {token[:10]}...")  # Show first 10 chars only
except Exception as e:
    print(f"❌ Error: {e}")
```

**Expected Output:**
```
✅ Secret retrieved successfully!
Token starts with: dapi...
```

---

## 🔄 For Local Development (Not in Databricks)

If running locally on your computer:

### Step 1: Create .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your token
# nano .env  # or use any text editor
```

### Step 2: Add Your Token to .env

```bash
DATABRICKS_TOKEN=your-actual-token-here
DATABRICKS_ENDPOINT=https://dbc-4a93b454-f17b.cloud.databricks.com/serving-endpoints/databricks-llama-4-maverick/invocations
```

### Step 3: Make Sure .env is in .gitignore

```bash
# Check if .env is ignored
cat .gitignore | grep .env

# Should show:
# .env
# .env.local
# .env.*.local
```

### Step 4: Run Your Application

```bash
cd backend
python main.py
```

The code will automatically load from `.env` file using `python-dotenv`.

---

## 🔐 Security Best Practices

### ✅ DO:
- ✅ Use Databricks Secrets in production
- ✅ Use `.env` files for local development only
- ✅ Add `.env` to `.gitignore`
- ✅ Rotate tokens every 90 days
- ✅ Use descriptive token comments
- ✅ Revoke tokens immediately if compromised
- ✅ Use separate tokens for dev/prod

### ❌ DON'T:
- ❌ NEVER hardcode tokens in code
- ❌ NEVER commit tokens to Git
- ❌ NEVER share tokens in chat/email
- ❌ NEVER use the same token for multiple projects
- ❌ NEVER set token lifetime to "never expire"

---

## 🔄 Rotating Tokens (Every 90 Days)

1. Generate new token in Databricks
2. Update the secret:
   ```bash
   databricks secrets put-secret hackathon-chatbot databricks-token
   ```
3. Paste new token and save
4. Restart your notebook/application
5. Revoke the old token in Databricks

---

## 🐛 Troubleshooting

### Issue: "Secret not found"

**Solution:**
```bash
# List all scopes
databricks secrets list-scopes

# List secrets in scope
databricks secrets list --scope hackathon-chatbot

# Recreate if missing
databricks secrets put-secret hackathon-chatbot databricks-token
```

### Issue: "Permission denied"

**Solution:**
- Check you have access to the secret scope
- Verify you're using the correct scope name
- Contact your Databricks admin for access

### Issue: "dbutils not found" (local development)

**Solution:**
- This is expected when running locally
- The code will fall back to environment variables
- Make sure you have `.env` file with your token

### Issue: Token expired

**Solution:**
1. Generate new token in Databricks
2. Update secret with new token
3. Restart application

---

## 📊 Secret Access Audit

To see who accessed your secrets:

1. Go to Databricks workspace
2. Navigate to **Admin Console** → **Audit Logs**
3. Filter by: `secretsRead` events
4. Review access patterns

---

## 🎯 Quick Reference Commands

```bash
# Create scope
databricks secrets create-scope hackathon-chatbot

# Add/update secret
databricks secrets put-secret hackathon-chatbot databricks-token

# List scopes
databricks secrets list-scopes

# List secrets in scope
databricks secrets list --scope hackathon-chatbot

# Delete secret (if needed)
databricks secrets delete-secret hackathon-chatbot databricks-token

# Delete scope (if needed)
databricks secrets delete-scope hackathon-chatbot
```

---

## ✅ Setup Complete!

Once you've completed these steps:

- ✅ Token stored securely in Databricks Secrets
- ✅ No tokens in code or Git
- ✅ Ready to run notebook safely
- ✅ Can share code without exposing credentials

---

**Next Step:** Return to the deployment guide and run your notebook!

The notebook will automatically retrieve the token from Databricks Secrets. 🎉


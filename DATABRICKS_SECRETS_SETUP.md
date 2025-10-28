# Setting Up Databricks Secrets (In Databricks Workspace)

Quick guide for storing your token securely **in Databricks** before running the notebook.

---

## 🎯 Two Simple Methods

### **Method 1: Using Databricks UI (Easiest)**

#### Step 1: Get Your Token
1. In Databricks, click your **username** (top right)
2. Click **User Settings**
3. Click **Access Tokens** tab
4. Click **Generate New Token**
   - Name: `Hackathon Chatbot`
   - Lifetime: 90 days
5. Click **Generate**
6. **COPY THE TOKEN** (save it temporarily)

#### Step 2: Create Secret Scope
1. In your browser, go to:
   ```
   https://<your-workspace>.cloud.databricks.com/#secrets/createScope
   ```
   Replace `<your-workspace>` with your actual workspace URL

2. Fill in:
   - **Scope Name**: `hackathon-chatbot`
   - **Manage Principal**: Choose "All Users" or specific users
3. Click **Create**

#### Step 3: Add Token to Secrets (Using CLI)

Open a **new Databricks notebook** and run:

```python
# Create the secret scope (if not already created)
try:
    dbutils.secrets.createScope("hackathon-chatbot")
    print("✓ Secret scope created")
except Exception as e:
    print(f"Scope already exists or error: {e}")
```

**Note:** You can't add secrets directly via notebook API for security. You need to use the CLI.

---

### **Method 2: Using a Notebook Cell (Alternative)**

Since you're already in Databricks, just run this in a notebook cell:

```python
# Store token as a widget (TEMPORARY - only for testing)
dbutils.widgets.text("databricks_token", "", "Databricks Token")

# Get the token
token = dbutils.widgets.get("databricks_token")
print("Token received (will not be shown)")
```

Then in your main notebook, retrieve it:
```python
token = dbutils.widgets.get("databricks_token")
```

⚠️ **Warning:** This is less secure than using Secrets, but works for testing.

---

## 🔐 Method 3: Best Practice - Use Databricks CLI from Local Computer

Since you're on Windows, you can set up secrets from your computer:

### Step 1: Install Databricks CLI
```powershell
pip install databricks-cli
```

### Step 2: Configure CLI
```powershell
databricks configure --token
```
Enter:
- **Host**: Your Databricks workspace URL
- **Token**: A personal access token

### Step 3: Create Secret Scope
```powershell
databricks secrets create-scope hackathon-chatbot
```

### Step 4: Add Your Token
```powershell
databricks secrets put-secret hackathon-chatbot databricks-token
```

This will open Notepad. Paste your token, save, and close.

### Step 5: Verify
```powershell
databricks secrets list --scope hackathon-chatbot
```

---

## ✅ Your Notebook Code Already Handles This!

The `databricks_backend_notebook.py` is already configured:

```python
# This code is already in your notebook:
try:
    # Try to get from Databricks secrets
    self.access_token = dbutils.secrets.get(
        scope="hackathon-chatbot", 
        key="databricks-token"
    )
    print("✅ Using Databricks Secrets for authentication")
except:
    # Fallback
    print("⚠️ WARNING: No DATABRICKS_TOKEN found!")
```

---

## 🚀 Quick Start (If You Just Want to Test)

**Simplest way for immediate testing:**

1. **Generate a new token** (User Settings → Access Tokens)

2. **Open your notebook** (`databricks_backend_notebook.py`)

3. **Add this cell at the beginning:**
```python
# TEMPORARY: Store token in notebook for testing
# ⚠️ DELETE THIS CELL before committing!
import os
os.environ["DATABRICKS_TOKEN"] = "your-token-here"  # Replace with your token
```

4. **Run the rest of the notebook**

5. **Remember to DELETE that cell** before sharing!

---

## 🧪 Test Your Setup

Run this in a Databricks notebook cell:

```python
# Test if secrets are set up correctly
try:
    token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")
    print("✅ Secret retrieved successfully!")
    print(f"Token starts with: {token[:10]}...")
except Exception as e:
    print(f"❌ Error retrieving secret: {e}")
    print("\nTroubleshooting:")
    print("1. Create scope: dbutils.secrets.createScope('hackathon-chatbot')")
    print("2. Use Databricks CLI to add token")
    print("3. Or use temporary method above")
```

---

## 📝 Summary

**For Production (Recommended):**
- Use Databricks Secrets via CLI
- Scope: `hackathon-chatbot`
- Key: `databricks-token`

**For Quick Testing:**
- Use environment variable in notebook
- Remember to remove before sharing

**Your notebook code automatically:**
- ✅ Tries Databricks Secrets first
- ✅ Falls back to environment variable
- ✅ Shows clear warnings if not found

---

## ✅ Once Secrets Are Set Up

Just run your notebook normally! The code will automatically:
1. Retrieve token from secrets
2. Connect to Databricks LLM
3. Process documents
4. Start the API server

No code changes needed! 🎉


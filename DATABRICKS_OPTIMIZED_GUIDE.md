# Databricks Deployment Guide - Optimized

**Complete guide for deploying the Hackathon Chatbot on Databricks (Fully Native)**

## 🎯 What's New in This Version

✅ **Auto-Detection**: Automatically detects workspace paths and configuration  
✅ **Native Secrets**: Uses Databricks Secrets (no manual env variables)  
✅ **Unity Catalog**: First-class support for volumes  
✅ **Zero Config**: Works out of the box with minimal setup  
✅ **Better Errors**: Clear error messages and troubleshooting  

---

## 📋 Prerequisites

1. **Databricks Workspace**
   - Unity Catalog enabled
   - Cluster with DBR 13.0+ (ML Runtime recommended)

2. **Access Rights**
   - Create volumes in Unity Catalog
   - Create secret scopes
   - Access LLM serving endpoints

3. **Databricks LLM**
   - Llama 4 Maverick model access
   - Serving endpoint enabled

---

## 🚀 Quick Start (5 Steps)

### Step 1: Create Unity Catalog Volumes (1 minute)

```sql
-- In a Databricks SQL notebook or SQL editor
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads
COMMENT 'Uploaded documents (PDF, DOCX)';

CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_data
COMMENT 'Knowledge base embeddings';

-- Verify
SHOW VOLUMES IN main.default;
```

**Expected Output:**
```
volume_catalog | volume_schema | volume_name
main           | default       | hackathon_chatbot_uploads
main           | default       | hackathon_chatbot_data
```

---

### Step 2: Set Up Databricks Token (2 minutes)

**Option A: Using Databricks Secrets (Recommended)**

```bash
# In terminal with Databricks CLI
databricks secrets create-scope hackathon-chatbot

# Add your token
databricks secrets put-secret hackathon-chatbot databricks-token
# (Paste your token when prompted)
```

**Option B: Using Notebook Cell (Quick Testing)**

```python
# Run this cell once
dbutils.secrets.putSecret(scope="hackathon-chatbot", key="databricks-token", value="YOUR_TOKEN_HERE")
```

**Generate Token:**
1. Go to: `User Settings` → `Access Tokens`
2. Click `Generate New Token`
3. Name: `Hackathon Chatbot`
4. Lifetime: 90 days
5. Copy the token (you won't see it again!)

---

### Step 3: Upload Optimized Notebook (30 seconds)

1. Open Databricks workspace
2. Navigate to `Workspace` → `Users` → `Your folder`
3. Click `Import`
4. Upload `databricks_notebook_optimized.py`
5. Notebook appears as `databricks_notebook_optimized`

---

### Step 4: Start Your Cluster (2 minutes)

**Cluster Configuration:**
- **Runtime**: DBR 13.3 LTS ML or newer
- **Node Type**: `m5.xlarge` or better
- **Workers**: 0 (single node for cost savings) or 2-4 for production
- **Auto-terminate**: After 30 minutes

**Why ML Runtime?**
- Pre-installed ML libraries
- Faster startup
- Better GPU support

---

### Step 5: Run the Notebook (5 minutes)

1. Open `databricks_notebook_optimized`
2. Attach to your cluster (wait for green status)
3. Click **Run All**

**What Happens:**
```
Cell 1: Create volumes ✅       (skips if exist)
Cell 2: Install deps ✅         (~2 minutes)
Cell 3: Restart Python ✅       (~30 seconds)
Cell 4: Configure paths ✅      (~5 seconds)
Cell 5-7: Load code ✅          (~10 seconds)
Cell 8: Download model ✅       (~3 minutes first time, cached after)
Cell 9: Start server ✅         (~5 seconds)
```

**Expected Output (Cell 9):**
```
================================================================================
✅ HACKATHON CHATBOT API STARTED!
================================================================================

🌐 YOUR API URL:
https://dbc-4a93b454-f17b.cloud.databricks.com/driver-proxy/o/1234567890/0815-123456-abc123/8000

📚 API Documentation:
https://dbc-4a93b454-f17b.cloud.databricks.com/driver-proxy/o/1234567890/0815-123456-abc123/8000/docs

🔍 Health Check:
https://dbc-4a93b454-f17b.cloud.databricks.com/driver-proxy/o/1234567890/0815-123456-abc123/8000/health

================================================================================
```

**✅ COPY YOUR API URL - YOU'LL NEED IT FOR THE FRONTEND!**

---

## 🔍 Testing Your Deployment

### Test 1: Health Check

```bash
curl "https://YOUR_DRIVER_PROXY_URL/health"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "environment": "Databricks",
  "storage_type": "Unity Catalog Volumes",
  "documents_count": 0,
  "databricks_context": true
}
```

### Test 2: Upload a Document

```bash
curl -X POST "https://YOUR_DRIVER_PROXY_URL/upload" \
  -F "file=@test_document.pdf"
```

**Expected Response:**
```json
{
  "message": "Document 'test_document.pdf' uploaded successfully",
  "chunks_created": 42
}
```

### Test 3: Chat Query

```bash
curl -X POST "https://YOUR_DRIVER_PROXY_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this document about?", "use_llm": true}'
```

**Expected Response:**
```json
{
  "response": "Based on the document...",
  "sources": ["test_document.pdf"]
}
```

---

## 🎨 Connect Your Frontend

### Update React App

Edit `frontend/src/components/ChatInterface.jsx`:

```javascript
const API_URL = "https://YOUR_DRIVER_PROXY_URL";
```

### Deploy Frontend

**Option 1: Databricks Apps (Recommended)**

```python
# In a new notebook
%pip install streamlit

# Your streamlit app code
```

**Option 2: External Hosting**

Deploy to Vercel/Netlify:
```bash
cd frontend
npm run build
# Deploy the dist/ folder
```

---

## 📊 Key Features Explained

### 1. Auto-Detection

The notebook automatically detects:
- ✅ Workspace URL
- ✅ Cluster ID
- ✅ Organization ID
- ✅ Storage paths (Volumes → DBFS → Local)

**Code:**
```python
db_context = get_databricks_context()
# Returns workspace_url, org_id, cluster_id, user
```

### 2. Flexible Token Management

Priority order:
1. **Databricks Secrets** (Production) → Most secure
2. **Widget Input** (Testing) → Easy for demos
3. **Environment Variable** (Fallback) → Development

### 3. Storage Flexibility

Automatically chooses:
1. **Unity Catalog Volumes** (Preferred) - Modern, governed
2. **DBFS** (Fallback) - Legacy, works everywhere
3. **Local** (Development) - For testing

### 4. Smart Error Handling

```python
if not DATABRICKS_TOKEN:
    print("⚠️ WARNING: No token found!")
    print("📝 Fix: Run this command...")
```

Clear, actionable error messages!

---

## 🔧 Troubleshooting

### Issue 1: Token Not Found

**Symptoms:**
```
⚠️ WARNING: No Databricks token found!
```

**Fix:**
```python
# Option A: Create secret (permanent)
dbutils.secrets.putSecret(
    scope="hackathon-chatbot",
    key="databricks-token",
    value="YOUR_TOKEN_HERE"
)

# Option B: Use widget (temporary)
dbutils.widgets.text("databricks_token", "YOUR_TOKEN_HERE", "Token")
```

---

### Issue 2: Volumes Don't Exist

**Symptoms:**
```
⚠️ Using DBFS (consider migrating to Unity Catalog Volumes)
```

**Fix:**
```sql
-- Run this SQL
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads;
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_data;
```

---

### Issue 3: LLM Endpoint Error

**Symptoms:**
```
❌ LLM error: 401 Unauthorized
```

**Possible Causes:**
1. Token expired (generate new one)
2. No access to LLM endpoint (request access)
3. Wrong endpoint URL (check workspace URL)

**Fix:**
```python
# Check your endpoint
print(DATABRICKS_ENDPOINT)
# Should match: https://YOUR_WORKSPACE/serving-endpoints/databricks-llama-4-maverick/invocations

# Verify token
print(bool(DATABRICKS_TOKEN))  # Should be True
```

---

### Issue 4: Model Download Slow

**Symptoms:**
```
📥 Loading embedding model... (stuck for 5+ minutes)
```

**Fix:**
- ✅ Normal on first run (downloads ~100MB model)
- ✅ Cached after first download
- ✅ Use ML Runtime cluster (has some models pre-installed)

**Speed it up:**
```python
# Use a smaller model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Default: 80MB
# Or even faster:
embedding_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 50MB
```

---

### Issue 5: Server Stops After Idle

**Symptoms:**
- Server works, then stops after 30 minutes

**Fix:**
- ✅ This is normal (cluster auto-termination)
- ✅ Set cluster auto-termination to longer (60-120 min)
- ✅ Use Databricks Jobs for production (always-on)
- ✅ Or restart notebook when needed

---

## 📈 Production Deployment

### Option 1: Databricks Job (Recommended)

```json
{
  "name": "Hackathon Chatbot API",
  "job_clusters": [{
    "job_cluster_key": "chatbot_cluster",
    "new_cluster": {
      "spark_version": "13.3.x-cpu-ml-scala2.12",
      "node_type_id": "m5.xlarge",
      "num_workers": 0
    }
  }],
  "tasks": [{
    "task_key": "run_chatbot",
    "job_cluster_key": "chatbot_cluster",
    "notebook_task": {
      "notebook_path": "/Users/your-email/databricks_notebook_optimized",
      "source": "WORKSPACE"
    }
  }],
  "schedule": {
    "quartz_cron_expression": "0 0 8 * * ?",
    "timezone_id": "America/Los_Angeles"
  }
}
```

### Option 2: Databricks Apps

```python
# Coming soon - native Databricks Apps support
```

### Option 3: Always-On Cluster

- Set auto-termination to `Never`
- Use spot instances for cost savings
- Monitor with Databricks monitoring

---

## 💰 Cost Optimization

### Estimated Costs

**Development:**
- Cluster: ~$0.30/hour (single node m5.xlarge)
- Storage: <$0.01/GB/month (volumes)
- LLM calls: Varies by usage

**Production (1000 queries/day):**
- Cluster: ~$7/day (24/7)
- Storage: <$1/month
- LLM: ~$10-50/month (depends on model)

### Tips to Save Money

1. **Use Auto-Termination**
   ```
   Auto-terminate after 30 minutes
   → Cluster only runs when needed
   ```

2. **Use Spot Instances**
   ```
   Enable spot instances: 70% cheaper
   → Works great for dev/test
   ```

3. **Right-Size Your Cluster**
   ```
   Single node (0 workers) for <100 users
   → Cheapest option
   ```

4. **Cache Embeddings**
   ```python
   # Already implemented!
   # Model loads once, embeddings cached
   ```

---

## 🔒 Security Best Practices

### 1. Never Hardcode Tokens
✅ Use Databricks Secrets  
❌ Don't put tokens in code

### 2. Restrict Access
```bash
# Limit secret scope access
databricks secrets put-acl hackathon-chatbot --principal user@company.com --permission READ
```

### 3. Rotate Tokens
- Generate new tokens every 90 days
- Update secret scope

### 4. Use Unity Catalog Governance
- Set volume permissions
- Track data lineage
- Monitor access logs

---

## 📚 Additional Resources

- [Databricks Secrets Guide](https://docs.databricks.com/security/secrets/index.html)
- [Unity Catalog Volumes](https://docs.databricks.com/data-governance/unity-catalog/volumes.html)
- [Databricks LLMs](https://docs.databricks.com/machine-learning/foundation-models/index.html)
- [FastAPI on Databricks](https://docs.databricks.com/notebooks/notebooks-code.html#fastapi)

---

## ✅ Success Checklist

Before going to production:

- [ ] Volumes created and accessible
- [ ] Secrets configured (no hardcoded tokens)
- [ ] Cluster properly sized for load
- [ ] Auto-termination set appropriately
- [ ] Health check passes
- [ ] Sample documents uploaded and tested
- [ ] Chat queries returning good responses
- [ ] Frontend connected to driver proxy URL
- [ ] Error monitoring set up
- [ ] Cost monitoring enabled

---

## 🎉 You're Done!

Your Databricks-native chatbot is now running!

**Next Steps:**
1. Upload your documents via the API
2. Test chat queries
3. Connect your frontend
4. Share the URL with your team

**Need Help?**
- Check the troubleshooting section above
- Review cell outputs in notebook
- Check Databricks cluster logs

---

**Version:** 2.0.0  
**Last Updated:** 2025-10-29  
**Author:** AI Team


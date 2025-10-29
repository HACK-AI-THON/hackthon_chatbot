# Quick Start - Databricks Deployment

**Get your chatbot running in 10 minutes!**

---

## ⚡ Super Quick Setup

### 1️⃣ Create Volumes (2 min)
```sql
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_uploads;
CREATE VOLUME IF NOT EXISTS main.default.hackathon_chatbot_data;
```

### 2️⃣ Set Up Token (2 min)
```bash
# Generate token: User Settings → Access Tokens → Generate
databricks secrets put-secret hackathon-chatbot databricks-token
# (Paste your token)
```

### 3️⃣ Upload & Run (1 min)
1. Import `databricks_notebook_optimized.py` to Databricks
2. Attach to cluster (DBR 13.3 LTS ML recommended)
3. Click **Run All**

### 4️⃣ Get Your URL (30 sec)
Look for output like:
```
🌐 YOUR API URL:
https://dbc-xxx.cloud.databricks.com/driver-proxy/o/xxx/xxx/8000
```

### 5️⃣ Test (30 sec)
```bash
curl "YOUR_API_URL/health"
```

---

## ✅ Expected Output

After running all cells, you should see:

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

⏰ 14:25:30 - Server running - Documents: 0
```

---

## 🎯 What to Do Next

### Upload a Document
```bash
curl -X POST "YOUR_API_URL/upload" \
  -F "file=@document.pdf"
```

### Ask a Question
```bash
curl -X POST "YOUR_API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this about?", "use_llm": true}'
```

### Connect Frontend
```javascript
// frontend/src/components/ChatInterface.jsx
const API_URL = "YOUR_DRIVER_PROXY_URL";
```

---

## 🔍 Troubleshooting

### Token Not Found?
```python
# Run this cell in notebook:
dbutils.secrets.putSecret(
    scope="hackathon-chatbot",
    key="databricks-token",
    value="YOUR_TOKEN_HERE"
)
```

### Volumes Don't Exist?
```sql
-- Run this SQL:
SHOW VOLUMES IN main.default;

-- If empty, create them:
CREATE VOLUME main.default.hackathon_chatbot_uploads;
CREATE VOLUME main.default.hackathon_chatbot_data;
```

### Server Won't Start?
1. Check cluster is running (green status)
2. Verify all cells ran successfully
3. Look for error messages in cell outputs
4. Check cluster logs

---

## 📚 Full Documentation

- **Detailed Guide**: `DATABRICKS_OPTIMIZED_GUIDE.md`
- **Refactoring Details**: `REFACTORING_SUMMARY.md`
- **Security Setup**: `SECRETS_SETUP.md`

---

## 💡 Pro Tips

1. **Save Your URL**: Copy the driver proxy URL and save it somewhere safe
2. **Bookmark Docs**: The `/docs` endpoint has interactive API testing
3. **Watch Costs**: Use auto-termination (30 min) to save money
4. **Test First**: Try health check before uploading documents

---

**Need help?** See `DATABRICKS_OPTIMIZED_GUIDE.md` for detailed troubleshooting!


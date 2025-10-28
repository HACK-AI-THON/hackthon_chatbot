# Hackathon Chatbot - Deployment Guide

This document provides a quick overview of how to deploy the Hackathon Chatbot on **Databricks**.

---

## 🎯 Quick Start - Databricks Deployment

### Prerequisites
- Databricks workspace (Premium or Enterprise tier recommended)
- Databricks CLI installed: `pip install databricks-cli`
- Personal access token from Databricks workspace

---

## 📚 Deployment Files

| File | Description |
|------|-------------|
| `DATABRICKS_DEPLOYMENT.md` | **Comprehensive deployment guide** with 3 options |
| `databricks_backend_notebook.py` | **Ready-to-use Databricks notebook** for the backend |
| `databricks_setup.sh` | **Automated setup script** for CLI and file uploads |

---

## 🚀 Three Deployment Options

### Option 1: Databricks Apps (Production Ready)
Deploy as a managed application with auto-scaling, load balancing, and SSL.

**Best for:** Production deployments with high availability requirements

**Steps:**
1. Install Databricks CLI
2. Configure app deployment
3. Deploy with `databricks apps deploy`

**See:** Section "Option 1" in `DATABRICKS_DEPLOYMENT.md`

---

### Option 2: Databricks Notebook (Recommended for Hackathon) ✨
Run backend in a notebook cell with all code embedded.

**Best for:** Quick demos, hackathons, development

**Steps:**
1. Run `./databricks_setup.sh` to upload files
2. Open `databricks_backend_notebook.py` in Databricks workspace
3. Attach to a cluster
4. Run all cells
5. Get driver proxy URL
6. Update frontend with API URL

**See:** Section "Option 2" in `DATABRICKS_DEPLOYMENT.md`

---

### Option 3: Databricks Jobs + External Hosting
Run backend as a scheduled/continuous job, host frontend separately.

**Best for:** Complex deployments with external frontend infrastructure

**Steps:**
1. Create Databricks job configuration
2. Deploy job
3. Host frontend on Vercel/Netlify/etc.

**See:** Section "Option 3" in `DATABRICKS_DEPLOYMENT.md`

---

## ⚡ Quick Deploy (5 Minutes)

### Step 1: Install and Configure Databricks CLI
```bash
# Install CLI
pip install databricks-cli

# Configure (you'll need your workspace URL and token)
databricks configure --token
```

### Step 2: Run Setup Script
```bash
# Make script executable (Linux/Mac)
chmod +x databricks_setup.sh

# Run setup
./databricks_setup.sh

# Follow the prompts to upload files
```

### Step 3: Open and Run Notebook
1. Open your Databricks workspace
2. Navigate to `/Users/{your-email}/hackathon-chatbot/`
3. Open `Hackathon_Chatbot_Backend` notebook
4. Create or select a cluster
5. Run all cells

### Step 4: Get Your API URL
The notebook will display your API URL:
```
https://<workspace>.cloud.databricks.com/driver-proxy/o/<org-id>/<cluster-id>/8000/
```

### Step 5: Update Frontend
Edit `frontend/src/components/ChatInterface.jsx`:

```javascript
const API_BASE_URL = 'https://<your-workspace>.cloud.databricks.com/driver-proxy/o/<org-id>/<cluster-id>/8000';
```

### Step 6: Deploy Frontend
```bash
cd frontend
npm install
npm run build

# Deploy to your preferred hosting service
# Or run locally: npm run dev
```

---

## 🎬 Video Walkthrough Steps

1. **Install Databricks CLI** (1 min)
   ```bash
   pip install databricks-cli
   databricks configure --token
   ```

2. **Upload Files** (2 min)
   ```bash
   ./databricks_setup.sh
   # Enter your email when prompted
   ```

3. **Open Notebook in Databricks** (30 sec)
   - Go to workspace → Users → {your-email} → hackathon-chatbot
   - Open `Hackathon_Chatbot_Backend`

4. **Start Cluster and Run** (1 min)
   - Attach to cluster (or create new one)
   - Click "Run All"
   - Wait for "Server started successfully!" message

5. **Copy API URL** (30 sec)
   - Scroll to cell with driver proxy URL
   - Copy the URL

6. **Update Frontend** (1 min)
   - Edit `ChatInterface.jsx`
   - Replace API_BASE_URL with your URL
   - Save file

7. **Test Application** (30 sec)
   - Build frontend: `npm run build`
   - Run locally: `npm run dev`
   - Open browser to `http://localhost:3000`
   - Test chat with sample questions

**Total Time: ~6 minutes** ⚡

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│     Runs on: localhost:3000             │
│     or Vercel/Netlify                   │
└─────────────┬───────────────────────────┘
              │ HTTP Requests
              ▼
┌─────────────────────────────────────────┐
│    Databricks Driver Proxy URL          │
│    (Authenticated access)               │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│   Backend (FastAPI in Notebook)         │
│   - Document Processing                 │
│   - Knowledge Base (Embeddings)         │
│   - RAG Pipeline                        │
│   - Databricks LLM Integration          │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│        DBFS Storage                     │
│   - /uploads (PDF, DOCX files)         │
│   - /simple_db (Vector embeddings)     │
└─────────────────────────────────────────┘
```

---

## 🔧 Configuration

### Backend Configuration
The backend is already configured to use:
- **Databricks LLM**: Llama 4 Maverick endpoint
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Storage**: DBFS file system
- **Port**: 8000 (accessed via driver proxy)

### Frontend Configuration
Update these settings in `ChatInterface.jsx`:
```javascript
const API_BASE_URL = 'YOUR_DRIVER_PROXY_URL_HERE';
```

---

## 🧪 Testing

### Test Backend API
```bash
# Replace with your actual driver proxy URL
curl https://<workspace>.cloud.databricks.com/driver-proxy/o/<org-id>/<cluster-id>/8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "documents_count": 1,
  "knowledge_base_status": "ready",
  "environment": "Databricks"
}
```

### Test Frontend
1. Build: `npm run build`
2. Run: `npm run dev`
3. Open: http://localhost:3000
4. Try suggested questions

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to backend"
**Solution:** 
- Verify the cluster is running
- Check the driver proxy URL is correct
- Ensure CORS is enabled in backend (already configured)

### Issue: "Module not found" in notebook
**Solution:**
```python
# Run this cell first
%pip install fastapi uvicorn python-multipart PyPDF2 python-docx sentence-transformers requests
dbutils.library.restartPython()
```

### Issue: "Permission denied" for DBFS
**Solution:**
- Use `/tmp` for testing: `UPLOAD_DIR = "/tmp/hackathon-chatbot/uploads"`
- Or request DBFS access from your admin

### Issue: Frontend can't reach API
**Solution:**
- Check browser console for CORS errors
- Verify API_BASE_URL in frontend matches notebook output
- Test API directly with curl first

---

## 📱 Access Points

After deployment, you'll have:

| Service | URL |
|---------|-----|
| **Backend API** | `https://<workspace>.cloud.databricks.com/driver-proxy/...` |
| **API Docs (Swagger)** | `{backend-url}/docs` |
| **Health Check** | `{backend-url}/health` |
| **Frontend** | `http://localhost:3000` (dev) or your hosting URL |

---

## 📖 Documentation Index

- **DATABRICKS_DEPLOYMENT.md** - Complete deployment guide (all 3 options)
- **databricks_backend_notebook.py** - Ready-to-use notebook file
- **databricks_setup.sh** - Automated setup script
- **README_DEPLOYMENT.md** - This file (quick start)

---

## 💡 Pro Tips

1. **Keep Notebook Running**: The backend only runs while the notebook cell is active
2. **Use Auto-Termination**: Set cluster auto-termination to save costs
3. **Monitor Costs**: Check cluster usage in Databricks workspace
4. **Upload Documents**: Put initial documents in `uploads/` before running setup
5. **Use Secrets**: Store API tokens in Databricks secrets for production

---

## ✅ Deployment Checklist

- [ ] Databricks CLI installed and configured
- [ ] Setup script executed (`./databricks_setup.sh`)
- [ ] Notebook uploaded to workspace
- [ ] Cluster created and running
- [ ] Notebook cells all executed successfully
- [ ] Driver proxy URL copied
- [ ] Frontend configured with API URL
- [ ] Test document uploaded successfully
- [ ] Chat functionality tested
- [ ] Application accessible from browser

---

## 🎓 Learning Resources

- [Databricks Documentation](https://docs.databricks.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Sentence Transformers Guide](https://www.sbert.net/)
- [React Documentation](https://react.dev/)

---

## 🤝 Support

For issues or questions:
1. Check `DATABRICKS_DEPLOYMENT.md` for detailed troubleshooting
2. Review notebook cell outputs for error messages
3. Test API endpoints individually with curl
4. Check Databricks cluster logs

---

## 🎉 Success!

Once deployed, you'll have a fully functional RAG chatbot that:
- ✅ Processes PDF and Word documents
- ✅ Uses semantic search with embeddings
- ✅ Generates AI responses using Databricks LLM
- ✅ Provides a beautiful React frontend
- ✅ Runs entirely on Databricks infrastructure

**Happy Hacking! 🚀**


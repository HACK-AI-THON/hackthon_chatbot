# Databricks Deployment Guide - Hackathon Chatbot

This guide covers deploying the Hackathon Chatbot application on **Databricks**.

---

## 📋 Overview

The application consists of:
- **Backend**: FastAPI application with RAG capabilities using Databricks LLM
- **Frontend**: React application for the user interface
- **Knowledge Base**: File-based vector storage for document embeddings

---

## 🚀 Deployment Options

### Option 1: Databricks Apps (Recommended for Production)
### Option 2: Databricks Notebooks + Web App
### Option 3: Databricks Jobs + External Hosting

---

## 📦 Option 1: Databricks Apps Deployment

Databricks Apps allows you to deploy web applications directly on Databricks.

### Prerequisites
- Databricks workspace with Premium or Enterprise tier
- Databricks CLI installed
- Access to Databricks Apps feature

### Step 1: Install Databricks CLI
```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token

# Enter your Databricks workspace URL and personal access token
```

### Step 2: Create App Configuration
```yaml
# databricks-app.yml
name: hackathon-chatbot
runtime: python3.11

compute:
  size: small  # small, medium, or large
  min_instances: 1
  max_instances: 3

env:
  - PORT=8000
  - EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

volumes:
  - name: uploads
    mount_path: /app/uploads
  - name: knowledge_base
    mount_path: /app/simple_db

healthcheck:
  path: /health
  interval: 30s
  timeout: 10s

ports:
  - 8000
  - 3000
```

### Step 3: Prepare Application for Databricks
```bash
# Create deployment package
cd /path/to/Hackthon_Chatbot

# Create requirements file with all dependencies
cat > databricks-requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
PyPDF2==3.0.1
python-docx==1.1.0
sentence-transformers==2.2.2
requests==2.31.0
python-dotenv==1.0.0
scikit-learn==1.3.2
numpy==1.24.3
EOF
```

### Step 4: Deploy to Databricks Apps
```bash
# Deploy the application
databricks apps deploy \
  --name hackathon-chatbot \
  --source-path . \
  --config databricks-app.yml

# Check deployment status
databricks apps status hackathon-chatbot

# Get app URL
databricks apps get-url hackathon-chatbot
```

---

## 📓 Option 2: Databricks Notebooks Deployment

Deploy the backend as a Databricks notebook and host the frontend separately.

### Step 1: Create Backend Notebook

Create a notebook named `Hackathon_Chatbot_Backend`:

```python
# Databricks notebook source
# MAGIC %md
# MAGIC # Hackathon Chatbot Backend
# MAGIC This notebook runs the FastAPI backend for the Hackathon Chatbot

# COMMAND ----------
# Install dependencies
%pip install fastapi uvicorn python-multipart PyPDF2 python-docx sentence-transformers requests python-dotenv

# COMMAND ----------
# Restart Python to load new packages
dbutils.library.restartPython()

# COMMAND ----------
# Import libraries
import os
import sys
from pathlib import Path

# Set up paths
backend_path = "/Workspace/Users/{your-email}/hackathon-chatbot/backend"
sys.path.append(backend_path)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Upload Backend Files
# MAGIC 
# MAGIC Upload the following files to Databricks workspace:
# MAGIC - backend/main.py
# MAGIC - backend/chat_handler.py
# MAGIC - backend/knowledge_base.py
# MAGIC - backend/document_processor.py

# COMMAND ----------
# Import backend modules
from main import app
import uvicorn
from threading import Thread

# COMMAND ----------
# Configure paths for DBFS
UPLOAD_DIR = "/dbfs/FileStore/hackathon-chatbot/uploads"
SIMPLE_DB = "/dbfs/FileStore/hackathon-chatbot/simple_db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SIMPLE_DB, exist_ok=True)

# COMMAND ----------
# Run the FastAPI server
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Start server in background thread
server_thread = Thread(target=run_server, daemon=True)
server_thread.start()

print("✅ Backend server started on port 8000")
print("📍 Access the API at: https://{your-workspace}.cloud.databricks.com/driver-proxy/o/{org-id}/{cluster-id}/8000/")

# COMMAND ----------
# Keep notebook running
import time
while True:
    time.sleep(60)
    print("✅ Server is running...")
```

### Step 2: Configure Backend for Databricks

Update `backend/main.py` for Databricks:

```python
# Add at the top of main.py
import os

# Use DBFS paths if running on Databricks
if os.path.exists("/dbfs"):
    UPLOAD_DIR = Path("/dbfs/FileStore/hackathon-chatbot/uploads")
else:
    UPLOAD_DIR = Path("uploads")
```

Update `backend/knowledge_base.py`:

```python
# In __init__ method
if os.path.exists("/dbfs"):
    self.storage_directory = Path("/dbfs/FileStore/hackathon-chatbot/simple_db")
else:
    self.storage_directory = Path("../simple_db")
```

### Step 3: Upload Files to Databricks Workspace

```bash
# Using Databricks CLI
databricks workspace mkdirs /Users/{your-email}/hackathon-chatbot/backend

databricks workspace import \
  backend/main.py \
  /Users/{your-email}/hackathon-chatbot/backend/main.py

databricks workspace import \
  backend/chat_handler.py \
  /Users/{your-email}/hackathon-chatbot/backend/chat_handler.py

databricks workspace import \
  backend/knowledge_base.py \
  /Users/{your-email}/hackathon-chatbot/backend/knowledge_base.py

databricks workspace import \
  backend/document_processor.py \
  /Users/{your-email}/hackathon-chatbot/backend/document_processor.py
```

### Step 4: Create and Start Cluster

```bash
# Create cluster configuration
cat > cluster-config.json << EOF
{
  "cluster_name": "hackathon-chatbot-cluster",
  "spark_version": "14.3.x-scala2.12",
  "node_type_id": "i3.xlarge",
  "num_workers": 1,
  "autotermination_minutes": 60
}
EOF

# Create cluster
databricks clusters create --json-file cluster-config.json

# Get cluster ID
databricks clusters list
```

### Step 5: Run the Notebook

1. Open Databricks workspace
2. Navigate to your notebook
3. Attach to the cluster you created
4. Run all cells
5. Note the driver proxy URL for API access

### Step 6: Update Frontend Configuration

Update `frontend/src/components/ChatInterface.jsx`:

```javascript
// Replace getCurrentHost() function
const getCurrentHost = () => {
  // Use Databricks driver proxy URL
  return 'https://{your-workspace}.cloud.databricks.com/driver-proxy/o/{org-id}/{cluster-id}/8000';
};
```

---

## 🌐 Option 3: Databricks Jobs + External Frontend

Run backend as a Databricks Job and host frontend externally.

### Step 1: Create Job Configuration

```json
{
  "name": "hackathon-chatbot-backend",
  "tasks": [
    {
      "task_key": "run_backend",
      "notebook_task": {
        "notebook_path": "/Users/{your-email}/hackathon-chatbot/backend/Hackathon_Chatbot_Backend"
      },
      "new_cluster": {
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 1
      },
      "libraries": [
        {"pypi": {"package": "fastapi==0.104.1"}},
        {"pypi": {"package": "uvicorn[standard]==0.24.0"}},
        {"pypi": {"package": "python-multipart==0.0.6"}},
        {"pypi": {"package": "PyPDF2==3.0.1"}},
        {"pypi": {"package": "python-docx==1.1.0"}},
        {"pypi": {"package": "sentence-transformers==2.2.2"}},
        {"pypi": {"package": "requests==2.31.0"}},
        {"pypi": {"package": "python-dotenv==1.0.0"}}
      ]
    }
  ],
  "schedule": {
    "quartz_cron_expression": "0 0 0 * * ?",
    "timezone_id": "America/New_York"
  }
}
```

### Step 2: Deploy Job

```bash
# Create the job
databricks jobs create --json-file job-config.json

# Run the job
databricks jobs run-now --job-id {job-id}

# Monitor job
databricks runs list
```

---

## 🔧 Configuration for Databricks Environment

### Environment Variables

Create a `.env` file in Databricks:

```bash
# Create DBFS directory for config
dbutils.fs.mkdirs("dbfs:/FileStore/hackathon-chatbot/config")

# Upload .env file (REPLACE 'your-token-here' with your actual token)
# ⚠️ NEVER commit actual tokens to Git!
dbutils.fs.put("dbfs:/FileStore/hackathon-chatbot/config/.env", """
DATABRICKS_HOST=https://dbc-4a93b454-f17b.cloud.databricks.com
DATABRICKS_TOKEN=your-token-here
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
PORT=8000
""", overwrite=True)
```

### Access Control

Set up proper access controls:

```python
# In your notebook
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Grant permissions to workspace users
w.permissions.set(
    request_object_type="notebooks",
    request_object_id="{notebook-id}",
    access_control_list=[
        {
            "group_name": "users",
            "permission_level": "CAN_RUN"
        }
    ]
)
```

---

## 📊 Databricks-Specific Features

### Use Databricks Model Serving

Instead of calling the LLM endpoint directly, use Databricks Model Serving:

```python
# Update chat_handler.py
from databricks.sdk import WorkspaceClient

class ChatHandler:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.w = WorkspaceClient()
        
    async def _generate_databricks_response(self, query: str, documents: List[str]) -> str:
        context = "\n\n".join(documents[:3])
        
        prompt = f"""You are a helpful AI assistant...
        
Context from documents:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""
        
        # Use Databricks Model Serving
        response = self.w.serving_endpoints.query(
            name="databricks-llama-4-maverick",
            inputs=[{"prompt": prompt}]
        )
        
        return response.predictions[0]
```

### Use Unity Catalog for Storage

```python
# Update knowledge_base.py to use Unity Catalog volumes
class KnowledgeBase:
    def __init__(self, collection_name: str = "documents"):
        # Use Unity Catalog volume
        self.storage_directory = Path("/Volumes/main/default/hackathon_chatbot_data")
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.storage_directory / "documents.json"
        self.embeddings_file = self.storage_directory / "embeddings.pkl"
        # ... rest of initialization
```

### Use Databricks SQL for Document Metadata

```python
# Create Delta table for document metadata
spark.sql("""
CREATE TABLE IF NOT EXISTS hackathon_chatbot.documents (
    filename STRING,
    upload_date TIMESTAMP,
    chunk_count INT,
    total_size INT
) USING DELTA
""")

# Insert metadata when uploading
def add_document(self, filename: str, text_chunks: List[str]) -> None:
    # ... existing code ...
    
    # Insert metadata to Delta table
    from datetime import datetime
    spark.sql(f"""
    INSERT INTO hackathon_chatbot.documents VALUES (
        '{filename}',
        '{datetime.now()}',
        {len(text_chunks)},
        {sum(len(chunk) for chunk in text_chunks)}
    )
    """)
```

---

## 🔐 Security Best Practices

### 1. Use Databricks Secrets
```python
# Store sensitive information in Databricks secrets
dbutils.secrets.createScope("hackathon-chatbot")

# Add secrets
dbutils.secrets.put("hackathon-chatbot", "databricks-token", "your-token-here")

# Use in code
access_token = dbutils.secrets.get("hackathon-chatbot", "databricks-token")
```

### 2. Enable Authentication
```python
# Add authentication to FastAPI
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/chat")
async def chat(
    message: ChatMessage,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    # Validate token
    token = credentials.credentials
    if token != os.getenv("EXPECTED_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # ... rest of chat logic
```

---

## 📈 Monitoring and Logging

### Enable MLflow Tracking
```python
import mlflow

mlflow.set_experiment("/Users/{your-email}/hackathon-chatbot")

# Log each chat interaction
with mlflow.start_run():
    mlflow.log_param("query", query)
    mlflow.log_param("use_openai", use_openai)
    mlflow.log_metric("response_time", response_time)
    mlflow.log_text(response, "response.txt")
```

### Use Databricks Logging
```python
import logging
from databricks.sdk.runtime import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log events
logger.info(f"Document uploaded: {filename}")
logger.info(f"Query received: {query}")
```

---

## 🚀 Quick Start - Step by Step

### 1. Set Up Databricks Workspace
```bash
# Install CLI
pip install databricks-cli

# Configure
databricks configure --token
# Enter: https://your-workspace.cloud.databricks.com
# Enter your personal access token
```

### 2. Create Required Directories
```sql
-- In Databricks SQL or notebook
CREATE VOLUME IF NOT EXISTS hackathon.default.hackathon_chatbot_uploads
COMMENT 'Storage for uploaded documents (PDF, DOCX)';

CREATE VOLUME IF NOT EXISTS hackathon.default.hackathon_chatbot_data
COMMENT 'Storage for vector embeddings and knowledge base';

-- Verify
SHOW VOLUMES IN hackathon.default;
```

**Note:** Unity Catalog Volumes are the modern best practice. The code automatically falls back to DBFS if volumes are not available.

### 3. Upload Backend Files
```bash
# Upload Python files
databricks workspace import backend/main.py \
  /Users/{your-email}/hackathon-chatbot/main.py

databricks workspace import backend/chat_handler.py \
  /Users/{your-email}/hackathon-chatbot/chat_handler.py

databricks workspace import backend/knowledge_base.py \
  /Users/{your-email}/hackathon-chatbot/knowledge_base.py

databricks workspace import backend/document_processor.py \
  /Users/{your-email}/hackathon-chatbot/document_processor.py
```

### 4. Create and Run Notebook
- Create new notebook in Databricks
- Copy the backend notebook code (from Option 2)
- Attach to a cluster
- Run all cells

### 5. Access Your Application
- Backend API: Use the driver proxy URL shown in notebook output
- Frontend: Build and deploy to a static hosting service (Netlify, Vercel, etc.)

---

## 🐛 Troubleshooting

### Issue: Module Import Errors
```python
# Ensure all dependencies are installed
%pip install -r requirements.txt
dbutils.library.restartPython()
```

### Issue: DBFS Permission Denied
```python
# Use /tmp for testing
UPLOAD_DIR = "/tmp/hackathon-chatbot/uploads"
SIMPLE_DB = "/tmp/hackathon-chatbot/simple_db"
```

### Issue: Model Download Timeout
```python
# Pre-download model in separate cell
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

### Issue: API Not Accessible
- Check cluster is running
- Verify driver proxy URL is correct
- Ensure CORS settings allow your frontend domain

---

## 📝 Deployment Checklist

- [ ] Databricks workspace access configured
- [ ] CLI installed and authenticated
- [ ] Backend files uploaded to workspace
- [ ] Required directories created in DBFS/Unity Catalog
- [ ] Cluster created and running
- [ ] Notebook created and tested
- [ ] LLM endpoint accessible
- [ ] Frontend updated with correct API URL
- [ ] Test document upload
- [ ] Test chat functionality
- [ ] Monitoring and logging configured

---

## 🎯 Production Recommendations

1. **Use Unity Catalog Volumes** for data persistence
2. **Enable MLflow** for experiment tracking
3. **Set up CI/CD** with Databricks Repos
4. **Configure Auto-scaling** for the cluster
5. **Implement Rate Limiting** on API endpoints
6. **Use Databricks Secrets** for credentials
7. **Enable Audit Logs** for compliance
8. **Set up Alerts** for errors and performance

---

## 📚 Additional Resources

- [Databricks Apps Documentation](https://docs.databricks.com/apps/index.html)
- [Databricks Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [Unity Catalog Volumes](https://docs.databricks.com/unity-catalog/volumes.html)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)

---

**Need Help?** Contact your Databricks administrator or check the logs:
```python
# View application logs
display(dbutils.fs.ls("dbfs:/databricks/driver/logs/"))
```


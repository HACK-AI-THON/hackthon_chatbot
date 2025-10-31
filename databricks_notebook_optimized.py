# Databricks notebook source
# Install FastAPI and dependencies inside the cluster
%pip install --upgrade "huggingface_hub>=0.14.1" "sentence-transformers>=2.3.1,<5.2.0" fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 PyPDF2==3.0.1 python-docx==1.1.0 requests==2.31.0 scikit-learn==1.3.2



# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

"""
Hackathon Chatbot - Databricks Optimized
----------------------------------------
Fully Databricks-native backend + frontend deployment
- FastAPI backend with RAG & Databricks LLM
- Frontend static serving (CSS/JS) fixed for driver proxy MIME stripping
"""

# ================================================================
# 1️⃣ Imports & Setup
# ================================================================
import os, sys, json, time, shutil, zipfile, mimetypes
from pathlib import Path
from typing import List, Dict, Tuple
import requests
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from threading import Thread
import uvicorn
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
from docx import Document as DocxDocument

# COMMAND ----------

# ================================================================
# 2️⃣ Databricks Context (Dynamic)
# ================================================================
# Get actual Databricks context dynamically from the running cluster
try:
    db_context = json.loads(dbutils.notebook.entry_point.getDbutils().notebook().getContext().toJson())
    DATABRICKS_WORKSPACE_URL = db_context['tags']['browserHostName']
    if not DATABRICKS_WORKSPACE_URL.startswith('http'):
        DATABRICKS_WORKSPACE_URL = f"https://{DATABRICKS_WORKSPACE_URL}"
    DATABRICKS_ORG_ID = db_context['tags']['orgId']
    DATABRICKS_CLUSTER_ID = db_context['tags']['clusterId']
    print("✅ Databricks context loaded dynamically")
except Exception as e:
    print(f"⚠️ Could not get Databricks context: {e}")
    # Fallback to hardcoded values
    DATABRICKS_WORKSPACE_URL = "https://dbc-4a93b454-f17b.cloud.databricks.com"
    DATABRICKS_ORG_ID = "1978110925405963"
    DATABRICKS_CLUSTER_ID = "1017-190030-sow9d43h"
    print("⚠️ Using fallback hardcoded values")

print(f"Workspace: {DATABRICKS_WORKSPACE_URL}")
print(f"Org ID: {DATABRICKS_ORG_ID}")
print(f"Cluster ID: {DATABRICKS_CLUSTER_ID}")

# COMMAND ----------

# ================================================================
# 3️⃣ Storage Paths
# ================================================================
def get_storage_paths():
    if os.path.exists("/Volumes/hackathon/default/hackathon_chatbot_data"):
        return "/Volumes/hackathon/default/hackathon_chatbot_data"
    os.makedirs("hackathon_chatbot_data", exist_ok=True)
    return "hackathon_chatbot_data"

DATA_DIR = get_storage_paths()
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print(f"📂 Using data dir: {DATA_DIR}")


# COMMAND ----------

# ================================================================
# 4️⃣ Document Processor
# ================================================================
class DocumentProcessor:
    def __init__(self, chunk_size=1000, overlap=200):
        self.chunk_size, self.overlap = chunk_size, overlap

    def _extract_pdf_text(self, path):
        text = ""
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for p in reader.pages:
                text += p.extract_text() + "\n"
        return text

    def _extract_docx_text(self, path):
        doc = DocxDocument(path)
        return "\n".join([p.text for p in doc.paragraphs])

    def process_document(self, path):
        ext = Path(path).suffix.lower()
        if ext == ".pdf":
            text = self._extract_pdf_text(path)
        elif ext in [".doc", ".docx"]:
            text = self._extract_docx_text(path)
        else:
            raise ValueError(f"Unsupported format: {ext}")
        text = " ".join(text.split())
        chunks, start = [], 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.overlap
        return chunks

document_processor = DocumentProcessor()


# COMMAND ----------

# ================================================================
# 5️⃣ Knowledge Base
# ================================================================
class KnowledgeBase:
    def __init__(self, storage_dir):
        self.dir = Path(storage_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.docs_file = self.dir / "documents.json"
        self.emb_file = self.dir / "embeddings.pkl"
        self.documents = {}
        self.embeddings = {}
        if self.docs_file.exists():
            self.documents = json.load(open(self.docs_file))
        if self.emb_file.exists():
            import pickle; self.embeddings = pickle.load(open(self.emb_file, "rb"))
        print("📥 Loading model...")
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Embedding model ready")

    def add_document(self, filename, chunks):
        import pickle
        embs = self.model.encode(chunks)
        for i, chunk in enumerate(chunks):
            cid = f"{filename}_{i}"
            self.documents[cid] = {"filename": filename, "text": chunk}
            self.embeddings[cid] = embs[i]
        json.dump(self.documents, open(self.docs_file, "w"))
        pickle.dump(self.embeddings, open(self.emb_file, "wb"))
        print(f"✅ Added {len(chunks)} chunks from {filename}")

    def search_similar(self, query, n=5):
        if not self.documents:
            return [], [], []
        q = self.model.encode([query])
        sims, ids = [], []
        for cid, e in self.embeddings.items():
            sims.append(cosine_similarity(q, e.reshape(1, -1))[0][0])
            ids.append(cid)
        idx = np.argsort(sims)[::-1][:n]
        docs, srcs, dist = [], [], []
        for i in idx:
            cid = ids[i]
            docs.append(self.documents[cid]["text"])
            srcs.append(self.documents[cid]["filename"])
            dist.append(1 - sims[i])
        return docs, srcs, dist

knowledge_base = KnowledgeBase(DATA_DIR)


# COMMAND ----------

# ================================================================
# 6️⃣ Chat Handler (Databricks LLM)
# ================================================================
class ChatHandler:
    def __init__(self, kb, endpoint, token):
        self.kb, self.endpoint, self.token = kb, endpoint, token
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def generate_response(self, query):
        docs, srcs, dist = self.kb.search_similar(query)
        if not docs:
            return "No documents found", []
        context = "\n\n".join(docs[:3])
        payload = {"messages": [{"role": "user", "content": f"Context:\n{context}\n\nQ: {query}"}],
                   "max_tokens": 300}
        try:
            r = requests.post(self.endpoint, headers=self.headers, json=payload, timeout=30)
            if r.ok:
                j = r.json()
                return j["choices"][0]["message"]["content"], srcs
            else:
                return f"LLM error {r.status_code}", []
        except Exception as e:
            return f"Error calling LLM: {e}", []

chat_handler = ChatHandler(knowledge_base,
    f"{DATABRICKS_WORKSPACE_URL}/serving-endpoints/databricks-llama-4-maverick/invocations",
    os.getenv("DATABRICKS_TOKEN", "token-not-set"))



# COMMAND ----------

# ================================================================
# 7️⃣ FastAPI App
# ================================================================
app = FastAPI(title="Hackathon Chatbot", version="3.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(msg: ChatMessage):
    r, s = await chat_handler.generate_response(msg.message)
    return {"response": r, "sources": s}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".doc", ".docx"]:
        raise HTTPException(400, f"Unsupported file: {ext}")
    fp = Path(UPLOAD_DIR) / file.filename
    with open(fp, "wb") as f:
        shutil.copyfileobj(file.file, f)
    chunks = document_processor.process_document(str(fp))
    knowledge_base.add_document(file.filename, chunks)
    return {"status": "ok", "chunks": len(chunks)}

@app.get("/health")
async def health():
    return {"status": "ok", "docs": len(knowledge_base.documents)}


# COMMAND ----------


# ================================================================
# 8️⃣ Frontend Serving (Databricks-safe MIME)
# ================================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"
assets_dir = os.path.join(frontend_path, "assets")

# --- Mount FIRST ---
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir, html=False), name="assets")
    print("✅ Mounted /assets")
else:
    print("⚠️ Assets dir not found:", assets_dir)

# --- Then your root route ---
@app.get("/", response_class=FileResponse)
async def serve_index():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response("Frontend not found", media_type="text/plain")

@app.get("/hack-ai-thon.png", response_class=FileResponse)
async def serve_logo():
    logo = os.path.join(frontend_path, "hack-ai-thon.png")
    if os.path.exists(logo):
        return FileResponse(logo, media_type="image/png")
    return Response(status_code=404, content="Logo not found")

print("✅ Frontend static routes configured (Databricks-safe MIME)")

# COMMAND ----------

# ================================================================
# ✅ FINAL FRONTEND FIX (Databricks + FastAPI)
# ================================================================
import os, mimetypes
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import uvicorn

# --- 1️⃣ Explicit MIME type registration (defensive for Databricks proxy)
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")

# --- 2️⃣ Paths
frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"
assets_dir = os.path.join(frontend_path, "assets")

# --- 3️⃣ Initialize FastAPI
app = FastAPI(title="Hackathon Chatbot Frontend")

# --- 4️⃣ Mount Static Assets FIRST
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir, html=False), name="assets")
    print(f"✅ Mounted /assets from: {assets_dir}")
else:
    print(f"⚠️ Assets folder missing: {assets_dir}")

# --- 5️⃣ Serve index.html (Frontend entry point)
@app.get("/", response_class=FileResponse)
async def serve_index():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return Response("❌ index.html not found", media_type="text/plain")

# --- 6️⃣ Serve vite.svg (favicon)
@app.get("/vite.svg", response_class=FileResponse)
async def serve_vite():
    svg_path = os.path.join(frontend_path, "vite.svg")
    if os.path.exists(svg_path):
        return FileResponse(svg_path, media_type="image/svg+xml")
    return Response(status_code=404, content="vite.svg not found")

# --- 7️⃣ (Optional) Health route
@app.get("/health")
async def health():
    return {"status": "ok", "frontend": os.path.exists(os.path.join(frontend_path, 'index.html'))}

# --- 8️⃣ Print access URL for Databricks driver proxy (using dynamic context from above)
proxy_url = f"{DATABRICKS_WORKSPACE_URL}/driver-proxy/o/{DATABRICKS_ORG_ID}/{DATABRICKS_CLUSTER_ID}/8088/"
print(f"\n🌐 Access frontend at:\n{proxy_url}\n")




# COMMAND ----------



# ================================================================
# 9️⃣ Server
# ================================================================
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8088, log_level="info")

Thread(target=run_server, daemon=True).start()
print("🌐 Access app via driver proxy URL below:\n")
print(f"{DATABRICKS_WORKSPACE_URL}/driver-proxy/o/{DATABRICKS_ORG_ID}/{DATABRICKS_CLUSTER_ID}/8088/")
print("✅ Server started successfully!")

# Databricks notebook source
# MAGIC %md
# MAGIC # Hackathon Chatbot - Databricks Optimized
# MAGIC
# MAGIC **Fully Databricks-Native Implementation**
# MAGIC
# MAGIC Features:
# MAGIC - ✅ Auto-detects workspace paths
# MAGIC - ✅ Native Databricks Secrets integration
# MAGIC - ✅ Unity Catalog Volumes
# MAGIC - ✅ Interactive widgets for configuration
# MAGIC - ✅ Optimized for Databricks environment
# MAGIC
# MAGIC ## Quick Start:
# MAGIC 1. Create Unity Catalog Volumes (see cell below)
# MAGIC 2. Set up Databricks Secrets (or use widget)
# MAGIC 3. Run All Cells
# MAGIC 4. Get your API URL from output

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup: Create Unity Catalog Volumes
# MAGIC
# MAGIC Run this SQL first (one-time setup):

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create volumes for data storage
# MAGIC CREATE VOLUME IF NOT EXISTS hackathon.default.hackathon_chatbot_uploads
# MAGIC COMMENT 'Uploaded documents storage (PDF, DOCX)';
# MAGIC
# MAGIC CREATE VOLUME IF NOT EXISTS hackathon.default.hackathon_chatbot_data
# MAGIC COMMENT 'Knowledge base vector embeddings storage';
# MAGIC
# MAGIC -- Verify
# MAGIC SHOW VOLUMES IN hackathon.default;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Dependencies

# COMMAND ----------

# MAGIC %pip install --upgrade "huggingface_hub>=0.14.1" "sentence-transformers>=2.3.1,<5.2.0" fastapi==0.104.1 uvicorn[standard]==0.24.0 python-multipart==0.0.6 PyPDF2==3.0.1 python-docx==1.1.0 requests==2.31.0 scikit-learn==1.3.2

# COMMAND ----------

# Restart Python
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Configuration (Databricks-Native)

# COMMAND ----------

import os
import sys
from pathlib import Path

# ====================
# ⚙️ CONFIGURATION - Your Databricks Environment
# ====================

# 🔧 Set your Databricks details here
DATABRICKS_WORKSPACE_URL = "https://dbc-4a93b454-f17b.cloud.databricks.com"
DATABRICKS_ORG_ID = "1978110925405963"
DATABRICKS_CLUSTER_ID = "1017-190030-sow9d43h"

# ====================
# Databricks Context Detection
# ====================

def get_databricks_context():
    """Get Databricks workspace context (uses configured values)"""
    try:
        import os
        
        # Priority 1: Use hardcoded configuration values
        if DATABRICKS_ORG_ID and DATABRICKS_CLUSTER_ID:
            return {
                "workspace_url": DATABRICKS_WORKSPACE_URL,
                "org_id": DATABRICKS_ORG_ID,
                "cluster_id": DATABRICKS_CLUSTER_ID,
                "user": os.getenv("USER", "unknown"),
                "browser_host_name": DATABRICKS_WORKSPACE_URL.replace("https://", "")
            }
        
        # Priority 2: Try to get from dbutils (works in notebooks)
        try:
            # Get notebook context
            notebook_context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
            
            return {
                "workspace_url": notebook_context.apiUrl().getOrElse(DATABRICKS_WORKSPACE_URL),
                "org_id": notebook_context.tags().get("orgId").getOrElse("unknown"),
                "cluster_id": notebook_context.tags().get("clusterId").getOrElse("unknown"),
                "user": notebook_context.tags().get("user").getOrElse("unknown"),
                "browser_host_name": notebook_context.browserHostName().getOrElse("dbc-4a93b454-f17b.cloud.databricks.com")
            }
        except:
            pass
        
        # Priority 3: Use environment variables (Spark Connect compatible)
        workspace_url = os.getenv("DATABRICKS_HOST", DATABRICKS_WORKSPACE_URL)
        org_id = os.getenv("DATABRICKS_ORG_ID", "unknown")
        cluster_id = os.getenv("DATABRICKS_CLUSTER_ID", "unknown")
        user = os.getenv("USER", "unknown")
        
        return {
            "workspace_url": workspace_url,
            "org_id": org_id,
            "cluster_id": cluster_id,
            "user": user,
            "browser_host_name": workspace_url.replace("https://", "")
        }
        
    except Exception as e:
        print(f"ℹ️ Using default workspace configuration")
        # Return defaults
        return {
            "workspace_url": "https://dbc-4a93b454-f17b.cloud.databricks.com",
            "org_id": "unknown",
            "cluster_id": "unknown",
            "user": "unknown",
            "browser_host_name": "dbc-4a93b454-f17b.cloud.databricks.com"
        }

# Get context
db_context = get_databricks_context()

if db_context:
    print("✅ Databricks Environment Detected")
    print(f"   Workspace: {db_context['workspace_url']}")
    print(f"   User: {db_context['user']}")
    print(f"   Cluster: {db_context['cluster_id']}")
else:
    print("⚠️ Running in local/test environment")

# ====================
# Storage Path Configuration
# ====================

def get_storage_paths():
    """Auto-detect and configure storage paths"""
    
    # Unity Catalog Volumes (Priority 1 - Modern)
    if os.path.exists("/Volumes/hackathon/default/hackathon_chatbot_uploads"):
        return {
            "uploads": "/Volumes/hackathon/default/hackathon_chatbot_uploads",
            "data": "/Volumes/hackathon/default/hackathon_chatbot_data",
            "type": "Unity Catalog Volumes"
        }
    
    # DBFS (Priority 2 - Legacy)
    elif os.path.exists("/dbfs"):
        uploads_path = "/dbfs/FileStore/hackathon-chatbot/uploads"
        data_path = "/dbfs/FileStore/hackathon-chatbot/simple_db"
        os.makedirs(uploads_path, exist_ok=True)
        os.makedirs(data_path, exist_ok=True)
        return {
            "uploads": uploads_path,
            "data": data_path,
            "type": "DBFS (Legacy)"
        }
    
    # Local (Priority 3 - Development)
    else:
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("simple_db", exist_ok=True)
        return {
            "uploads": "uploads",
            "data": "simple_db",
            "type": "Local"
        }

storage = get_storage_paths()
UPLOAD_DIR = storage["uploads"]
DATA_DIR = storage["data"]

print(f"✅ Storage Type: {storage['type']}")
print(f"   Uploads: {UPLOAD_DIR}")
print(f"   Data: {DATA_DIR}")

# ====================
# Token Configuration (Databricks Secrets)
# ====================

def get_databricks_token():
    """Get Databricks token from multiple sources (priority order)"""
    
    # Priority 1: Databricks Secrets (Production)
    try:
        token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")
        print("✅ Using Databricks Secrets for authentication")
        return token
    except:
        pass
    
    # Priority 2: Widget (Interactive)
    try:
        token = dbutils.widgets.get("databricks_token")
        if token and token.strip():
            print("✅ Using token from widget")
            return token
    except:
        pass
    
    # Priority 3: Environment Variable (Fallback)
    token = os.getenv("DATABRICKS_TOKEN")
    if token:
        print("✅ Using token from environment variable")
        return token
    
    print("⚠️ WARNING: No Databricks token found!")
    print("📝 Set up token using ONE of these methods:")
    print("   1. Databricks Secrets: dbutils.secrets.put('hackathon-chatbot', 'databricks-token')")
    print("   2. Widget: Create a text widget named 'databricks_token'")
    print("   3. Environment: os.environ['DATABRICKS_TOKEN'] = 'your-token'")
    return None

# Create widget for token input (optional - for easy testing)
try:
    dbutils.widgets.text("databricks_token", "", "Databricks Token (optional)")
except:
    pass

# Get token
DATABRICKS_TOKEN = get_databricks_token()

# ====================
# LLM Endpoint Configuration
# ====================

# Auto-detect endpoint from context or use default
if db_context:
    DATABRICKS_ENDPOINT = f"{db_context['workspace_url']}/serving-endpoints/databricks-llama-4-maverick/invocations"
else:
    DATABRICKS_ENDPOINT = "https://dbc-4a93b454-f17b.cloud.databricks.com/serving-endpoints/databricks-llama-4-maverick/invocations"

print(f"✅ LLM Endpoint: {DATABRICKS_ENDPOINT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Document Processor (Optimized)

# COMMAND ----------

import PyPDF2
from docx import Document as DocxDocument
from typing import List, Dict
import re

class DocumentProcessor:
    """Databricks-optimized document processor"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        print(f"✅ DocumentProcessor initialized (chunk_size={chunk_size}, overlap={overlap})")
    
    def process_document(self, file_path: str) -> List[str]:
        """Process document and return chunks"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported format: {file_extension}")
            
            cleaned_text = self._clean_text(text)
            chunks = self._create_chunks(cleaned_text)
            
            return chunks
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF"""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        doc = DocxDocument(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()\-\'""]', ' ', text)
        return ' '.join(text.split()).strip()
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                # Find sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Find word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap
            if start >= len(text):
                break
        
        return chunks
    
    def process_folder(self, folder_path: str, knowledge_base) -> Dict:
        """Process all documents in folder"""
        results = {
            "processed": [],
            "skipped": [],
            "errors": [],
            "total_chunks": 0
        }
        
        supported_exts = ['.pdf', '.docx', '.doc']
        folder = Path(folder_path)
        
        if not folder.exists():
            return results
        
        existing_docs = [doc["filename"] for doc in knowledge_base.list_documents()]
        
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_exts:
                try:
                    filename = file_path.name
                    
                    if filename in existing_docs:
                        results["skipped"].append(filename)
                        continue
                    
                    chunks = self.process_document(str(file_path))
                    knowledge_base.add_document(filename, chunks)
                    
                    results["processed"].append(filename)
                    results["total_chunks"] += len(chunks)
                    
                except Exception as e:
                    results["errors"].append(f"{file_path.name}: {str(e)}")
        
        return results

# Initialize
document_processor = DocumentProcessor()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Knowledge Base (Databricks-Optimized)

# COMMAND ----------

import pickle
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Dict

class KnowledgeBase:
    """Databricks-optimized knowledge base with Unity Catalog Volumes"""
    
    def __init__(self, storage_dir: str):
        self.storage_directory = Path(storage_dir)
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.storage_directory / "documents.json"
        self.embeddings_file = self.storage_directory / "embeddings.pkl"
        
        # Load existing data
        self.documents_data = self._load_documents()
        self.embeddings_data = self._load_embeddings()
        
        # Initialize embedding model
        print("📥 Loading embedding model...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        print("✅ Embedding model loaded")
    
    def _load_documents(self) -> Dict:
        """Load documents from JSON"""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_embeddings(self) -> Dict:
        """Load embeddings from pickle"""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_documents(self):
        """Save documents to JSON"""
        with open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents_data, f, ensure_ascii=False, indent=2)
    
    def _save_embeddings(self):
        """Save embeddings to pickle"""
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings_data, f)
    
    def add_document(self, filename: str, text_chunks: List[str]) -> None:
        """Add document to knowledge base"""
        embeddings = self.embedding_model.encode(text_chunks, show_progress_bar=False)
        
        for i, chunk in enumerate(text_chunks):
            chunk_id = f"{filename}_chunk_{i}"
            self.documents_data[chunk_id] = {
                "filename": filename,
                "chunk_index": i,
                "text": chunk,
                "chunk_size": len(chunk)
            }
            self.embeddings_data[chunk_id] = embeddings[i]
        
        self._save_documents()
        self._save_embeddings()
        
        print(f"✅ Added {len(text_chunks)} chunks from {filename}")
    
    def search_similar(self, query: str, n_results: int = 5) -> Tuple[List[str], List[str], List[float]]:
        """Search for similar documents"""
        if not self.documents_data or not self.embeddings_data:
            return [], [], []
        
        query_embedding = self.embedding_model.encode([query], show_progress_bar=False)
        
        similarities = []
        chunk_ids = []
        
        for chunk_id, embedding in self.embeddings_data.items():
            if chunk_id in self.documents_data:
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    embedding.reshape(1, -1)
                )[0][0]
                similarities.append(similarity)
                chunk_ids.append(chunk_id)
        
        sorted_indices = np.argsort(similarities)[::-1][:n_results]
        
        documents = []
        sources = []
        distances = []
        
        for idx in sorted_indices:
            chunk_id = chunk_ids[idx]
            doc_data = self.documents_data[chunk_id]
            
            documents.append(doc_data["text"])
            sources.append(doc_data["filename"])
            distances.append(1 - similarities[idx])
        
        return documents, sources, distances
    
    def remove_document(self, filename: str) -> None:
        """Remove document from knowledge base"""
        chunk_ids_to_remove = [
            chunk_id for chunk_id, doc_data in self.documents_data.items()
            if doc_data.get("filename") == filename
        ]
        
        for chunk_id in chunk_ids_to_remove:
            if chunk_id in self.documents_data:
                del self.documents_data[chunk_id]
            if chunk_id in self.embeddings_data:
                del self.embeddings_data[chunk_id]
        
        if chunk_ids_to_remove:
            self._save_documents()
            self._save_embeddings()
            print(f"✅ Removed {len(chunk_ids_to_remove)} chunks for {filename}")
    
    def list_documents(self) -> List[Dict]:
        """List all documents"""
        doc_stats = {}
        for chunk_id, doc_data in self.documents_data.items():
            filename = doc_data.get("filename", "Unknown")
            if filename not in doc_stats:
                doc_stats[filename] = {
                    "filename": filename,
                    "chunk_count": 0,
                    "total_size": 0
                }
            doc_stats[filename]["chunk_count"] += 1
            doc_stats[filename]["total_size"] += doc_data.get("chunk_size", 0)
        
        return list(doc_stats.values())
    
    def clear_all(self) -> None:
        """Clear all documents"""
        self.documents_data = {}
        self.embeddings_data = {}
        self._save_documents()
        self._save_embeddings()
        print("✅ Knowledge base cleared")

# Initialize
knowledge_base = KnowledgeBase(DATA_DIR)

print(f"📊 Current knowledge base status:")
print(f"   Total documents: {len(knowledge_base.list_documents())}")
print(f"   Total chunks: {len(knowledge_base.documents_data)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Chat Handler (Databricks LLM Integration)

# COMMAND ----------

import requests
from typing import List, Tuple

class ChatHandler:
    """Databricks-native chat handler"""
    
    def __init__(self, knowledge_base, endpoint: str, token: str):
        self.knowledge_base = knowledge_base
        self.endpoint = endpoint
        self.token = token
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("✅ Chat handler initialized")
    
    async def generate_response(self, query: str, use_llm: bool = True) -> Tuple[str, List[str]]:
        """Generate response to query"""
        
        # Search knowledge base
        documents, sources, distances = self.knowledge_base.search_similar(query, n_results=5)
        
        if not documents:
            return "No documents found. Please upload some documents first.", []
        
        # Filter by relevance
        relevant_docs = []
        relevant_sources = []
        threshold = 1.0
        
        for doc, source, distance in zip(documents, sources, distances):
            if distance < threshold:
                relevant_docs.append(doc)
                relevant_sources.append(source)
        
        if not relevant_docs:
            return "No relevant information found in the uploaded documents.", []
        
        # Generate LLM response
        if use_llm and self.token:
            try:
                response = await self._call_databricks_llm(query, relevant_docs)
            except Exception as e:
                print(f"⚠️ LLM error: {e}")
                response = self._fallback_response(relevant_docs)
        else:
            response = self._fallback_response(relevant_docs)
        
        return response, list(set(relevant_sources))
    
    async def _call_databricks_llm(self, query: str, documents: List[str]) -> str:
        """Call Databricks LLM endpoint"""
        
        context = "\n\n".join(documents[:3])
        
        prompt = f"""You are a helpful AI assistant. Answer the question based on the provided context.

Context:
{context}

Question: {query}

Provide a concise, helpful answer in markdown format."""

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
        
        raise Exception(f"LLM API error: {response.status_code}")
    
    def _fallback_response(self, documents: List[str]) -> str:
        """Fallback response without LLM"""
        return f"Based on the documents:\n\n{documents[0][:500]}..."

# Initialize
chat_handler = ChatHandler(knowledge_base, DATABRICKS_ENDPOINT, DATABRICKS_TOKEN)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. FastAPI Application (Databricks-Optimized)

# COMMAND ----------

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil

# Initialize FastAPI
app = FastAPI(
    title="Hackathon Chatbot API",
    version="2.0.0",
    description="Databricks-native RAG chatbot"
)

# CORS - Allow all origins for Databricks driver proxy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    use_llm: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

# Startup event
@app.on_event("startup")
async def startup_event():
    """Process existing documents on startup"""
    print("🚀 Starting Hackathon Chatbot API...")
    
    results = document_processor.process_folder(UPLOAD_DIR, knowledge_base)
    
    if results["processed"]:
        print(f"✅ Processed {len(results['processed'])} documents")
    if results["skipped"]:
        print(f"⏭️ Skipped {len(results['skipped'])} documents (already processed)")
    if results["errors"]:
        print(f"❌ Errors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"   - {error}")
    
    print(f"📊 Total chunks: {results['total_chunks']}")
    print("✅ API Ready!")
    
    app.state.startup_complete = True

# Routes
@app.get("/")
async def root():
    return {
        "message": "Hackathon Chatbot API - Databricks Native",
        "version": "2.0.0",
        "environment": "Databricks" if db_context else "Local",
        "storage": storage["type"]
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process document"""
    try:
        allowed_exts = ['.pdf', '.docx', '.doc']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_exts:
            raise HTTPException(400, f"Unsupported file type: {file_ext}")
        
        file_path = Path(UPLOAD_DIR) / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        chunks = document_processor.process_document(str(file_path))
        knowledge_base.add_document(file.filename, chunks)
        
        return {
            "message": f"Document '{file.filename}' uploaded successfully",
            "chunks_created": len(chunks)
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat message"""
    try:
        response, sources = await chat_handler.generate_response(
            message.message,
            use_llm=message.use_llm
        )
        return ChatResponse(response=response, sources=sources)
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/documents")
async def list_documents():
    """List all documents"""
    return {"documents": knowledge_base.list_documents()}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a document"""
    try:
        knowledge_base.remove_document(filename)
        
        file_path = Path(UPLOAD_DIR) / filename
        if file_path.exists():
            file_path.unlink()
        
        return {"message": f"Document '{filename}' deleted"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "environment": "Databricks" if db_context else "Local",
        "storage_type": storage["type"],
        "documents_count": len(knowledge_base.list_documents()),
        "databricks_context": db_context is not None
    }

print("✅ FastAPI application configured")

# COMMAND ----------

# COMMAND ----------

# Override the root endpoint to serve frontend
from fastapi.responses import FileResponse

# Remove the old root route
routes_to_keep = []
for route in app.routes:
    if hasattr(route, 'path') and route.path == "/" and hasattr(route, 'methods'):
        print(f"🗑️ Removing old route: {route.methods} {route.path}")
        continue  # Skip this route
    routes_to_keep.append(route)

# Update routes
app.router.routes = routes_to_keep

# Add frontend root route
frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

@app.get("/", response_class=FileResponse)
async def serve_frontend():
    """Serve the frontend application"""
    return FileResponse(f"{frontend_path}/index.html")

print("✅ Root endpoint updated to serve frontend")
print("\nNew routes:")
for route in app.routes:
    if hasattr(route, 'path') and route.path == "/":
        print(f"  ✓ {route.methods if hasattr(route, 'methods') else 'MOUNT'} {route.path} -> Frontend HTML")

# COMMAND ----------

# COMMAND ----------

# Manual asset serving (works better with Unity Catalog Volumes)
from fastapi import Response
import mimetypes
import os

frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

# Remove the StaticFiles mount (doesn't work well with Volumes)
routes_to_keep = []
for route in app.routes:
    # Keep all routes except the /assets mount
    if hasattr(route, 'path') and route.path == "/assets":
        print(f"🗑️ Removing StaticFiles mount for /assets")
        continue
    routes_to_keep.append(route)

app.router.routes = routes_to_keep

# Add manual asset routes
@app.get("/assets/{file_path:path}")
async def serve_assets(file_path: str):
    """Serve static assets"""
    file_full_path = os.path.join(frontend_path, "assets", file_path)
    
    if not os.path.exists(file_full_path):
        return Response(status_code=404, content="File not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(file_full_path)
    if mime_type is None:
        if file_path.endswith('.js'):
            mime_type = 'application/javascript'
        elif file_path.endswith('.css'):
            mime_type = 'text/css'
        else:
            mime_type = 'application/octet-stream'
    
    # Read and return file
    with open(file_full_path, 'rb') as f:
        content = f.read()
    
    return Response(content=content, media_type=mime_type)

print("✅ Manual asset serving configured")
print(f"📁 Serving from: {frontend_path}/assets/")
print(f"✓ CSS files will use MIME type: text/css")
print(f"✓ JS files will use MIME type: application/javascript")

# COMMAND ----------

# COMMAND ----------

# Full diagnostic and fix
import os

frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

print("="*80)
print("🔍 DIAGNOSTIC CHECK")
print("="*80)

# Check files exist
print("\n1️⃣ Checking files:")
index_exists = os.path.exists(f"{frontend_path}/index.html")
css_exists = os.path.exists(f"{frontend_path}/assets/index-CTtEJaLV.css")
js_exists = os.path.exists(f"{frontend_path}/assets/index-K_8xONh4.js")

print(f"   index.html: {'✅' if index_exists else '❌'}")
print(f"   CSS file: {'✅' if css_exists else '❌'}")
print(f"   JS file: {'✅' if js_exists else '❌'}")

# Check current routes
print("\n2️⃣ Current app routes:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['MOUNT'])
        if route.path in ['/', '/assets', '/assets/{file_path:path}']:
            print(f"   {list(methods)} {route.path}")

# Test reading files
print("\n3️⃣ Testing file access:")
try:
    with open(f"{frontend_path}/assets/index-CTtEJaLV.css", 'r') as f:
        css_content = f.read()[:100]
        print(f"   CSS size: {len(css_content)} bytes (sample read)")
except Exception as e:
    print(f"   ❌ Error reading CSS: {e}")

print("\n" + "="*80)
print("💡 RECOMMENDATION: We need to restart Python kernel")
print("="*80)
print("\n📋 Next steps:")
print("   1. Click 'Detach & Re-attach' or 'Restart Python'")
print("   2. Run all cells from the top")
print("   3. This ensures clean route registration")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Start Server

# COMMAND ----------

import uvicorn
from threading import Thread
import time

def run_server():
    """Run FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8088, log_level="info")

# Start server in background
server_thread = Thread(target=run_server, daemon=True)
server_thread.start()

print("=" * 80)
print("✅ HACKATHON CHATBOT API STARTED!")
print("=" * 80)
print()

if db_context:
    driver_proxy_url = f"{db_context['workspace_url']}/driver-proxy/o/{db_context['org_id']}/{db_context['cluster_id']}/8088"
    print("🌐 YOUR API URL:")
    print(driver_proxy_url)
    print()
    print("📚 API Documentation:")
    print(f"{driver_proxy_url}/docs")
    print()
    print("🔍 Health Check:")
    print(f"{driver_proxy_url}/health")
else:
    print("🌐 API URL: http://localhost:8088")
    print("📚 Documentation: http://localhost:8088/docs")

print()
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Keep Server Running

# COMMAND ----------

# Heartbeat to keep server alive
try:
    while True:
        time.sleep(60)
        docs_count = len(knowledge_base.list_documents())
        print(f"⏰ {time.strftime('%H:%M:%S')} - Server running - Documents: {docs_count}")
except KeyboardInterrupt:
    print("🛑 Server stopped")

# COMMAND ----------

# COMMAND ----------

# MAGIC %md
# MAGIC ## Extract and Prepare Frontend

# COMMAND ----------

# Extract frontend files
import zipfile
import os
from pathlib import Path

# Paths
zip_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend_dist.zip"
extract_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

# Create frontend directory
Path(extract_path).mkdir(parents=True, exist_ok=True)

# Extract zip file
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)

print(f"✅ Frontend extracted to: {extract_path}")
print(f"📁 Files:")
for root, dirs, files in os.walk(extract_path):
    for file in files[:10]:
        rel_path = os.path.relpath(os.path.join(root, file), extract_path)
        print(f"   - {rel_path}")

# COMMAND ----------

# COMMAND ----------

# Check actual file structure
import os
from pathlib import Path

frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

print("📂 Actual directory structure:")
for root, dirs, files in os.walk(frontend_path):
    level = root.replace(frontend_path, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')

print("\n" + "="*80)

# Check if assets directory exists
assets_path = f"{frontend_path}/assets"
if os.path.exists(assets_path):
    print(f"✅ Assets directory exists: {assets_path}")
else:
    print(f"❌ Assets directory NOT found: {assets_path}")
    print("\n🔧 Fixing the structure...")
    
    # Re-extract with proper handling
    import zipfile
    import shutil
    
    # Clear and recreate
    if os.path.exists(frontend_path):
        shutil.rmtree(frontend_path)
    os.makedirs(frontend_path, exist_ok=True)
    
    # Extract properly
    zip_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend_dist.zip"
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Convert Windows paths to Unix paths
            member_path = member.replace('\\', '/')
            target_path = os.path.join(frontend_path, member_path)
            
            # Create directories if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Extract file
            if not member.endswith('/'):
                with zip_ref.open(member) as source, open(target_path, 'wb') as target:
                    target.write(source.read())
    
    print("✅ Files re-extracted with proper structure")
    
    # List again
    print("\n📂 New structure:")
    for root, dirs, files in os.walk(frontend_path):
        level = root.replace(frontend_path, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Show first 5 files per directory
            print(f'{subindent}{file}')

# COMMAND ----------

# COMMAND ----------

# Add static file serving to the FastAPI app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount frontend static files
frontend_path = "/Volumes/hackathon/default/hackathon_chatbot_data/frontend"

# Verify paths exist
import os
print(f"Frontend path exists: {os.path.exists(frontend_path)}")
print(f"Assets path exists: {os.path.exists(f'{frontend_path}/assets')}")
print(f"Index.html exists: {os.path.exists(f'{frontend_path}/index.html')}")

# Serve static files (assets folder)
app.mount("/assets", StaticFiles(directory=f"{frontend_path}/assets"), name="assets")

# Serve index.html at root
@app.get("/", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(f"{frontend_path}/index.html")

# Serve logo
@app.get("/hack-ai-thon.png", response_class=FileResponse)
async def serve_logo():
    return FileResponse(f"{frontend_path}/hack-ai-thon.png")

print("\n✅ Frontend routes added to FastAPI app")
print("🌐 Frontend will be available at the API URL root")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Test Your API

# COMMAND ----------

# Test the API
import requests

base_url = "http://localhost:8088"

# Health check
response = requests.get(f"{base_url}/health")
print("Health Check:")
print(response.json())

# List documents
response = requests.get(f"{base_url}/documents")
print("\nDocuments:")
print(response.json())

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Deployment Complete!
# MAGIC
# MAGIC Your chatbot is now running on Databricks with:
# MAGIC - ✅ Unity Catalog Volumes
# MAGIC - ✅ Databricks Secrets
# MAGIC - ✅ Auto-detected workspace configuration
# MAGIC - ✅ FastAPI REST API
# MAGIC - ✅ RAG with Databricks LLM
# MAGIC
# MAGIC Use the driver proxy URL above to access from your frontend!
# MAGIC
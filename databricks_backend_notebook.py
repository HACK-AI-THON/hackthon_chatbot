# Databricks notebook source
# MAGIC %md
# MAGIC # Hackathon Chatbot Backend - Databricks Deployment
# MAGIC 
# MAGIC This notebook deploys the Hackathon Chatbot backend on Databricks.
# MAGIC 
# MAGIC ## Prerequisites
# MAGIC - Upload all backend Python files to Databricks workspace
# MAGIC - Ensure you have access to Databricks LLM endpoint
# MAGIC - Create necessary DBFS directories

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Dependencies

# COMMAND ----------

# MAGIC %pip install fastapi uvicorn[standard] python-multipart PyPDF2 python-docx sentence-transformers requests python-dotenv scikit-learn

# COMMAND ----------

# Restart Python to load new packages
dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Import Required Libraries

# COMMAND ----------

import os
import sys
import uvicorn
from pathlib import Path
from threading import Thread
import time

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Configure Paths for Databricks

# COMMAND ----------

# Check if running on Databricks
IS_DATABRICKS = os.path.exists("/dbfs") or os.path.exists("/Volumes")
print(f"Running on Databricks: {IS_DATABRICKS}")

# Set up paths - Use Unity Catalog Volumes (modern best practice)
if os.path.exists("/Volumes"):
    UPLOAD_DIR = "/Volumes/main/default/hackathon_chatbot_uploads"
    SIMPLE_DB_DIR = "/Volumes/main/default/hackathon_chatbot_data"
    BACKEND_PATH = "/Workspace/Repos/{your-username}/Hackthon_Chatbot/backend"
    print("✅ Using Unity Catalog Volumes")
elif os.path.exists("/dbfs"):
    # Fallback to DBFS if volumes not available
    UPLOAD_DIR = "/dbfs/FileStore/hackathon-chatbot/uploads"
    SIMPLE_DB_DIR = "/dbfs/FileStore/hackathon-chatbot/simple_db"
    BACKEND_PATH = "/Workspace/Repos/{your-username}/Hackthon_Chatbot/backend"
    print("⚠️ Using DBFS (consider migrating to Unity Catalog Volumes)")
else:
    UPLOAD_DIR = "uploads"
    SIMPLE_DB_DIR = "../simple_db"
    BACKEND_PATH = "."

# Create directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SIMPLE_DB_DIR, exist_ok=True)

print(f"✅ Upload directory: {UPLOAD_DIR}")
print(f"✅ Knowledge base directory: {SIMPLE_DB_DIR}")

# Add backend path to sys.path
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Copy Backend Files (Inline)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.1 Document Processor

# COMMAND ----------

# document_processor.py
import PyPDF2
from docx import Document
from pathlib import Path
from typing import List, Dict
import re

class DocumentProcessor:
    """Handles document text extraction and chunking"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def process_document(self, file_path: str) -> List[str]:
        """Process a document and return text chunks"""
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.pdf':
            text = self._extract_pdf_text(file_path)
        elif file_extension in ['.docx', '.doc']:
            text = self._extract_docx_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        cleaned_text = self._clean_text(text)
        chunks = self._create_chunks(cleaned_text)
        
        return chunks
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error extracting Word document text: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()\-\'""]', ' ', text)
        text = ' '.join(text.split())
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
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
    
    def process_upload_folder(self, folder_path: str, knowledge_base) -> Dict[str, any]:
        """Process all documents in the upload folder"""
        results = {
            "processed_files": [],
            "skipped_files": [],
            "errors": [],
            "total_chunks": 0
        }
        
        supported_extensions = ['.pdf', '.docx', '.doc']
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"Upload folder does not exist: {folder_path}")
            return results
        
        document_files = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                document_files.append(str(file_path))
        
        if not document_files:
            print(f"No supported documents found in {folder_path}")
            return results
        
        print(f"Found {len(document_files)} documents to process...")
        
        for file_path in document_files:
            try:
                file_name = Path(file_path).name
                existing_docs = [doc["filename"] for doc in knowledge_base.list_documents()]
                
                if file_name in existing_docs:
                    print(f"Skipping {file_name} - already in knowledge base")
                    results["skipped_files"].append(file_name)
                    continue
                
                print(f"Processing {file_name}...")
                text_chunks = self.process_document(file_path)
                knowledge_base.add_document(file_name, text_chunks)
                
                results["processed_files"].append(file_name)
                results["total_chunks"] += len(text_chunks)
                
                print(f"SUCCESS: Processed {file_name} ({len(text_chunks)} chunks)")
                
            except Exception as e:
                error_msg = f"Error processing {Path(file_path).name}: {str(e)}"
                print(f"ERROR: {error_msg}")
                results["errors"].append(error_msg)
        
        return results

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.2 Knowledge Base

# COMMAND ----------

# knowledge_base.py
import pickle
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

class KnowledgeBase:
    """Manages document storage and retrieval using simple file-based vector storage"""
    
    def __init__(self, collection_name: str = "documents"):
        # Use Unity Catalog Volume (modern best practice)
        if os.path.exists("/Volumes"):
            self.storage_directory = Path("/Volumes/main/default/hackathon_chatbot_data")
        elif os.path.exists("/dbfs"):
            # Fallback to DBFS if volumes not available
            self.storage_directory = Path("/dbfs/FileStore/hackathon-chatbot/simple_db")
        else:
            self.storage_directory = Path("../simple_db")
        
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        self.documents_file = self.storage_directory / "documents.json"
        self.embeddings_file = self.storage_directory / "embeddings.pkl"
        
        self.documents_data = self._load_documents()
        self.embeddings_data = self._load_embeddings()
        
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        print(f"Loading embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        print("✅ Embedding model loaded")
    
    def _load_documents(self) -> Dict:
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_embeddings(self) -> Dict:
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_documents(self):
        with open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents_data, f, ensure_ascii=False, indent=2)
    
    def _save_embeddings(self):
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings_data, f)
    
    def add_document(self, filename: str, text_chunks: List[str]) -> None:
        try:
            embeddings = self.embedding_model.encode(text_chunks)
            
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
            
            print(f"Added {len(text_chunks)} chunks from {filename} to knowledge base")
            
        except Exception as e:
            raise Exception(f"Error adding document to knowledge base: {str(e)}")
    
    def search_similar(self, query: str, n_results: int = 5) -> Tuple[List[str], List[str], List[float]]:
        try:
            if not self.documents_data or not self.embeddings_data:
                return [], [], []
            
            query_embedding = self.embedding_model.encode([query])
            
            similarities = []
            chunk_ids = []
            
            for chunk_id, embedding in self.embeddings_data.items():
                if chunk_id in self.documents_data:
                    similarity = cosine_similarity(query_embedding.reshape(1, -1), 
                                                 embedding.reshape(1, -1))[0][0]
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
            
        except Exception as e:
            print(f"Error searching knowledge base: {str(e)}")
            return [], [], []
    
    def remove_document(self, filename: str) -> None:
        try:
            chunk_ids_to_remove = []
            for chunk_id, doc_data in self.documents_data.items():
                if doc_data.get("filename") == filename:
                    chunk_ids_to_remove.append(chunk_id)
            
            for chunk_id in chunk_ids_to_remove:
                if chunk_id in self.documents_data:
                    del self.documents_data[chunk_id]
                if chunk_id in self.embeddings_data:
                    del self.embeddings_data[chunk_id]
            
            if chunk_ids_to_remove:
                self._save_documents()
                self._save_embeddings()
                print(f"Removed {len(chunk_ids_to_remove)} chunks for document {filename}")
            
        except Exception as e:
            raise Exception(f"Error removing document from knowledge base: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, any]]:
        try:
            document_stats = {}
            for chunk_id, doc_data in self.documents_data.items():
                filename = doc_data.get("filename", "Unknown")
                if filename not in document_stats:
                    document_stats[filename] = {
                        "filename": filename,
                        "chunk_count": 0,
                        "total_size": 0
                    }
                document_stats[filename]["chunk_count"] += 1
                document_stats[filename]["total_size"] += doc_data.get("chunk_size", 0)
            
            return list(document_stats.values())
            
        except Exception as e:
            print(f"Error listing documents: {str(e)}")
            return []
    
    def clear_all(self) -> None:
        try:
            self.documents_data = {}
            self.embeddings_data = {}
            self._save_documents()
            self._save_embeddings()
            print("Knowledge base cleared successfully")
        except Exception as e:
            raise Exception(f"Error clearing knowledge base: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.3 Chat Handler

# COMMAND ----------

# chat_handler.py
import requests
import json
from typing import List, Tuple

class ChatHandler:
    """Handles chat interactions and response generation"""
    
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.databricks_endpoint = "https://dbc-4a93b454-f17b.cloud.databricks.com/serving-endpoints/databricks-llama-4-maverick/invocations"
        
        # Get token from Databricks secrets (SECURE METHOD)
        try:
            # Try to get from Databricks secrets first (when running in Databricks)
            self.access_token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")
            print("✅ Using Databricks Secrets for authentication")
        except:
            # Fall back to environment variable (for local development)
            self.access_token = os.getenv("DATABRICKS_TOKEN")
            if not self.access_token:
                print("⚠️ WARNING: No DATABRICKS_TOKEN found!")
                print("📝 Set up Databricks Secrets:")
                print("   1. Create secret scope: databricks secrets create-scope hackathon-chatbot")
                print("   2. Add token: databricks secrets put-secret hackathon-chatbot databricks-token")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        print("✅ Databricks LLM endpoint configured")
    
    async def generate_response(self, query: str, use_openai: bool = False) -> Tuple[str, List[str]]:
        documents, sources, distances = self.knowledge_base.search_similar(query, n_results=5)
        
        if not documents:
            return self._generate_no_content_response(), []
        
        relevant_docs = []
        relevant_sources = []
        distance_threshold = 1.0
        
        for doc, source, distance in zip(documents, sources, distances):
            if distance < distance_threshold:
                relevant_docs.append(doc)
                relevant_sources.append(source)
        
        if not relevant_docs:
            return self._generate_no_relevant_content_response(), []
        
        if use_openai:
            try:
                response = await self._generate_databricks_response(query, relevant_docs)
                print(f"✅ Databricks LLM response generated")
            except Exception as e:
                print(f"❌ Databricks LLM error: {str(e)}")
                response = "Error generating response from LLM"
        else:
            response = "LLM not enabled for this request"
        
        unique_sources = list(set(relevant_sources))
        return response, unique_sources
    
    async def _generate_databricks_response(self, query: str, documents: List[str]) -> str:
        context = "\n\n".join(documents[:3])
        
        prompt = f"""You are a helpful AI assistant that answers questions based on provided documents.

Guidelines:
- Answer questions using only the information provided in the context
- Format the entire response as a markdown document, with proper headings and subheadings
- If the context doesn't contain relevant information, say so clearly
- Be concise but comprehensive
- Keep the response as short as possible

Context from documents:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.databricks_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return result.get('response', result.get('content', 'No response received'))
            else:
                print(f"Databricks API error: Status {response.status_code}, Response: {response.text}")
                raise Exception(f"API returned status code {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("Databricks API timeout")
            raise Exception("Request timeout")
        except Exception as e:
            print(f"Databricks LLM error: {str(e)}")
            raise e
    
    def _generate_no_content_response(self) -> str:
        return "I don't have any documents uploaded yet to answer your question. Please upload some documents first."
    
    def _generate_no_relevant_content_response(self) -> str:
        return "I couldn't find relevant information in the uploaded documents to answer your question."

# COMMAND ----------

# MAGIC %md
# MAGIC ### 4.4 Main FastAPI Application

# COMMAND ----------

# main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil
from pathlib import Path

# Initialize components
document_processor = DocumentProcessor()
knowledge_base = KnowledgeBase()
chat_handler = ChatHandler(knowledge_base)

# Initialize FastAPI app
app = FastAPI(title="AI Knowledge Assistant", version="1.0.0")

# Add CORS middleware - Allow all origins for Databricks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use Unity Catalog Volume (modern best practice)
if os.path.exists("/Volumes"):
    UPLOAD_DIR = Path("/Volumes/main/default/hackathon_chatbot_uploads")
elif os.path.exists("/dbfs"):
    UPLOAD_DIR = Path("/dbfs/FileStore/hackathon-chatbot/uploads")
else:
    UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting AI Knowledge Assistant...")
    print("📂 Scanning uploads folder for existing documents...")
    
    results = document_processor.process_upload_folder(str(UPLOAD_DIR), knowledge_base)
    
    if results["processed_files"]:
        print(f"✅ Processed {len(results['processed_files'])} documents")
    
    print(f"📊 Total chunks in knowledge base: {results['total_chunks']}")
    print("✅ AI Knowledge Assistant is ready!")
    
    app.state.startup_complete = True

class ChatMessage(BaseModel):
    message: str
    use_openai: bool = False

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

@app.get("/")
async def root():
    return {"message": "AI Knowledge Assistant API is running on Databricks!"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        allowed_extensions = ['.pdf', '.docx', '.doc']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported"
            )
        
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        text_chunks = document_processor.process_document(str(file_path))
        knowledge_base.add_document(file.filename, text_chunks)
        
        return {
            "message": f"Document '{file.filename}' uploaded and processed successfully",
            "chunks_created": len(text_chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        response, sources = await chat_handler.generate_response(
            message.message, 
            use_openai=message.use_openai
        )
        return ChatResponse(response=response, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.get("/documents")
async def list_documents():
    try:
        documents = knowledge_base.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    try:
        knowledge_base.remove_document(filename)
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()
        return {"message": f"Document '{filename}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.delete("/clear")
async def clear_all_documents():
    try:
        knowledge_base.clear_all()
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.get("/health")
async def health_check():
    startup_complete = getattr(app.state, 'startup_complete', False)
    return {
        "status": "healthy" if startup_complete else "starting",
        "documents_count": len(knowledge_base.list_documents()),
        "knowledge_base_status": "ready" if startup_complete else "initializing",
        "upload_folder": str(UPLOAD_DIR.absolute()),
        "environment": "Databricks",
        "supported_formats": [".pdf", ".docx", ".doc"]
    }

print("✅ FastAPI application initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Start the FastAPI Server

# COMMAND ----------

# Define server function
def run_server():
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

# Start server in background thread
server_thread = Thread(target=run_server, daemon=True)
server_thread.start()

print("=" * 80)
print("✅ Backend server started successfully!")
print("=" * 80)
print("")
print("📍 Access the API using Databricks driver proxy URL:")
print("   https://<your-workspace>.cloud.databricks.com/driver-proxy/o/<org-id>/<cluster-id>/8000/")
print("")
print("📚 API Documentation:")
print("   Swagger UI: /docs")
print("   ReDoc: /redoc")
print("")
print("🔍 Health Check: /health")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Keep Server Running

# COMMAND ----------

# Keep the notebook cell running to maintain the server
try:
    while True:
        time.sleep(60)
        # Print heartbeat message every minute
        docs_count = len(knowledge_base.list_documents())
        print(f"⏰ Server heartbeat - {time.strftime('%Y-%m-%d %H:%M:%S')} - Documents: {docs_count}")
except KeyboardInterrupt:
    print("🛑 Server stopped by user")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Server Management Commands
# MAGIC 
# MAGIC Run these cells as needed to manage the server:

# COMMAND ----------

# Test health endpoint
import requests

try:
    response = requests.get("http://localhost:8000/health")
    print("✅ Health check response:")
    print(response.json())
except Exception as e:
    print(f"❌ Health check failed: {str(e)}")

# COMMAND ----------

# List uploaded documents
print("📚 Uploaded documents:")
docs = knowledge_base.list_documents()
for doc in docs:
    print(f"  - {doc['filename']} ({doc['chunk_count']} chunks, {doc['total_size']} bytes)")

# COMMAND ----------

# Test chat functionality
test_query = "What is this hackathon about?"
print(f"🤖 Testing chat with query: '{test_query}'")

response, sources = await chat_handler.generate_response(test_query, use_openai=True)
print(f"\n✅ Response:\n{response}")
print(f"\n📄 Sources: {sources}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Get Driver Proxy URL
# MAGIC 
# MAGIC Use this cell to get the exact URL for your backend API:

# COMMAND ----------

# Get cluster information
import json

# Get workspace URL
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()

# Get organization ID
org_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("orgId").get()

# Get cluster ID
cluster_id = dbutils.notebook.entry_point.getDbutils().notebook().getContext().tags().get("clusterId").get()

# Construct driver proxy URL
driver_proxy_url = f"{workspace_url}/driver-proxy/o/{org_id}/{cluster_id}/8000"

print("=" * 80)
print("🌐 YOUR BACKEND API URL:")
print("=" * 80)
print(f"\n{driver_proxy_url}\n")
print("=" * 80)
print("\n📋 Update your frontend with this URL:")
print(f"\nconst API_BASE_URL = '{driver_proxy_url}';")
print("\n=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Test API Endpoints

# COMMAND ----------

# Test all endpoints
base_url = "http://localhost:8000"

print("🧪 Testing API Endpoints...")
print("=" * 80)

# Test root endpoint
try:
    response = requests.get(f"{base_url}/")
    print(f"✅ GET /")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ GET / - Error: {str(e)}")

print()

# Test health endpoint
try:
    response = requests.get(f"{base_url}/health")
    print(f"✅ GET /health")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ GET /health - Error: {str(e)}")

print()

# Test documents endpoint
try:
    response = requests.get(f"{base_url}/documents")
    print(f"✅ GET /documents")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"❌ GET /documents - Error: {str(e)}")

print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📝 Notes
# MAGIC 
# MAGIC - The server runs in a background thread
# MAGIC - The notebook must remain running to keep the server active
# MAGIC - Use the driver proxy URL to access the API from external applications
# MAGIC - All uploaded files are stored in Unity Catalog Volumes at `/Volumes/main/default/hackathon_chatbot_uploads`
# MAGIC - The knowledge base is stored at `/Volumes/main/default/hackathon_chatbot_data`
# MAGIC - Falls back to DBFS if volumes are not available


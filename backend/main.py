import os
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import shutil
from pathlib import Path

from document_processor import DocumentProcessor
from knowledge_base import KnowledgeBase
from chat_handler import ChatHandler

# Initialize FastAPI app
app = FastAPI(title="AI Knowledge Assistant", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://10.120.85.106:3000", "http://192.168.1.68:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
knowledge_base = KnowledgeBase()
chat_handler = ChatHandler(knowledge_base)

# Configure upload directory - Use Unity Catalog Volumes if available
if os.path.exists("/Volumes"):
    # Unity Catalog Volumes (Databricks modern approach)
    UPLOAD_DIR = Path("/Volumes/main/default/hackathon_chatbot_uploads")
elif os.path.exists("/dbfs"):
    # DBFS (Databricks legacy approach)
    UPLOAD_DIR = Path("/dbfs/FileStore/hackathon-chatbot/uploads")
else:
    # Local development
    UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.on_event("startup")
async def startup_event():
    """Process any existing documents in uploads folder on startup"""
    print("Starting AI Knowledge Assistant...")
    print("Scanning uploads folder for existing documents...")
    
    results = document_processor.process_upload_folder(str(UPLOAD_DIR), knowledge_base)
    
    if results["processed_files"]:
        print(f"SUCCESS: Processed {len(results['processed_files'])} documents:")
        for file_name in results["processed_files"]:
            print(f"   - {file_name}")
    
    if results["skipped_files"]:
        print(f"SKIPPED: {len(results['skipped_files'])} documents (already processed):")
        for file_name in results["skipped_files"]:
            print(f"   - {file_name}")
    
    if results["errors"]:
        print(f"ERRORS: Processing {len(results['errors'])} documents:")
        for error in results["errors"]:
            print(f"   - {error}")
    
    print(f"STATS: Total chunks in knowledge base: {results['total_chunks']}")
    print("AI Knowledge Assistant is ready!")
    
    # Update health status
    app.state.startup_complete = True

class ChatMessage(BaseModel):
    message: str
    use_openai: bool = False

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []

@app.get("/")
async def root():
    return {"message": "AI Knowledge Assistant API is running!"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        text_chunks = document_processor.process_document(str(file_path))
        
        # Add to knowledge base
        knowledge_base.add_document(file.filename, text_chunks)
        
        return {
            "message": f"Document '{file.filename}' uploaded and processed successfully",
            "chunks_created": len(text_chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Handle chat messages"""
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
    """List all uploaded documents"""
    try:
        documents = knowledge_base.list_documents()
        return {"documents": documents}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """Delete a specific document"""
    try:
        # Remove from knowledge base
        knowledge_base.remove_document(filename)
        
        # Remove physical file
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            file_path.unlink()
        
        return {"message": f"Document '{filename}' deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@app.delete("/clear")
async def clear_all_documents():
    """Clear all documents and reset knowledge base"""
    try:
        # Clear knowledge base
        knowledge_base.clear_all()
        
        # Remove all uploaded files
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        
        return {"message": "All documents cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")

@app.post("/scan-uploads")
async def scan_uploads():
    """Manually scan and process documents in uploads folder"""
    try:
        print("Manual scan requested for uploads folder...")
        results = document_processor.process_upload_folder(str(UPLOAD_DIR), knowledge_base)
        
        return {
            "message": "Upload folder scan completed",
            "processed_files": results["processed_files"],
            "skipped_files": results["skipped_files"],
            "errors": results["errors"],
            "total_chunks_added": results["total_chunks"],
            "total_documents": len(knowledge_base.list_documents())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scanning uploads folder: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    startup_complete = getattr(app.state, 'startup_complete', False)
    return {
        "status": "healthy" if startup_complete else "starting",
        "documents_count": len(knowledge_base.list_documents()),
        "knowledge_base_status": "ready" if startup_complete else "initializing",
        "upload_folder": str(UPLOAD_DIR.absolute()),
        "supported_formats": [".pdf", ".docx", ".doc"]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)


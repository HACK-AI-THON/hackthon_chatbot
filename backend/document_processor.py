import PyPDF2
from docx import Document
from pathlib import Path
from typing import List, Dict, Tuple
import re
import os

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
        
        # Clean and chunk the text
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
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'""]', ' ', text)
        
        # Remove extra spaces
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
            
            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence endings
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundaries
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.overlap
            
            # Avoid infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    def scan_upload_folder(self, folder_path: str) -> List[str]:
        """Scan upload folder for supported document files"""
        supported_extensions = ['.pdf', '.docx', '.doc']
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"Upload folder does not exist: {folder_path}")
            return []
        
        document_files = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                document_files.append(str(file_path))
        
        return document_files
    
    def process_upload_folder(self, folder_path: str, knowledge_base) -> Dict[str, any]:
        """Process all documents in the upload folder"""
        results = {
            "processed_files": [],
            "skipped_files": [],
            "errors": [],
            "total_chunks": 0
        }
        
        # Get all document files in the folder
        document_files = self.scan_upload_folder(folder_path)
        
        if not document_files:
            print(f"No supported documents found in {folder_path}")
            return results
        
        print(f"Found {len(document_files)} documents to process...")
        
        for file_path in document_files:
            try:
                file_name = Path(file_path).name
                
                # Check if document is already in knowledge base
                existing_docs = knowledge_base.list_documents()
                if file_name in existing_docs:
                    print(f"Skipping {file_name} - already in knowledge base")
                    results["skipped_files"].append(file_name)
                    continue
                
                # Process the document
                print(f"Processing {file_name}...")
                text_chunks = self.process_document(file_path)
                
                # Add to knowledge base
                knowledge_base.add_document(file_name, text_chunks)
                
                results["processed_files"].append(file_name)
                results["total_chunks"] += len(text_chunks)
                
                print(f"SUCCESS: Processed {file_name} ({len(text_chunks)} chunks)")
                
            except Exception as e:
                error_msg = f"Error processing {Path(file_path).name}: {str(e)}"
                print(f"ERROR: {error_msg}")
                results["errors"].append(error_msg)
        
        return results
    
    def get_document_stats(self, file_path: str) -> dict:
        """Get basic statistics about a document"""
        try:
            text = ""
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.pdf':
                text = self._extract_pdf_text(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_docx_text(file_path)
            
            cleaned_text = self._clean_text(text)
            chunks = self._create_chunks(cleaned_text)
            
            return {
                "file_name": Path(file_path).name,
                "file_type": file_extension,
                "character_count": len(text),
                "word_count": len(text.split()),
                "chunk_count": len(chunks),
                "avg_chunk_size": sum(len(chunk) for chunk in chunks) // len(chunks) if chunks else 0
            }
            
        except Exception as e:
            return {"error": str(e)}


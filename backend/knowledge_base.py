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
        # Use Unity Catalog Volume (modern best practice) or fallback
        if os.path.exists("/Volumes"):
            # Unity Catalog Volumes (Databricks modern approach)
            self.storage_directory = Path("/Volumes/main/default/hackathon_chatbot_data")
        elif os.path.exists("/dbfs"):
            # DBFS (Databricks legacy approach)
            self.storage_directory = Path("/dbfs/FileStore/hackathon-chatbot/simple_db")
        else:
            # Local development
            self.storage_directory = Path("../simple_db")
        
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.documents_file = self.storage_directory / "documents.json"
        self.embeddings_file = self.storage_directory / "embeddings.pkl"
        
        # Load existing data
        self.documents_data = self._load_documents()
        self.embeddings_data = self._load_embeddings()
        
        # Initialize embedding model
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer(model_name)
        
    def _load_documents(self) -> Dict:
        """Load documents from JSON file"""
        if self.documents_file.exists():
            try:
                with open(self.documents_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_embeddings(self) -> Dict:
        """Load embeddings from pickle file"""
        if self.embeddings_file.exists():
            try:
                with open(self.embeddings_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return {}
        return {}
    
    def _save_documents(self):
        """Save documents to JSON file"""
        with open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents_data, f, ensure_ascii=False, indent=2)
    
    def _save_embeddings(self):
        """Save embeddings to pickle file"""
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings_data, f)
    
    def add_document(self, filename: str, text_chunks: List[str]) -> None:
        """Add document chunks to the knowledge base"""
        try:
            # Generate embeddings for all chunks
            embeddings = self.embedding_model.encode(text_chunks)
            
            # Store document chunks
            for i, chunk in enumerate(text_chunks):
                chunk_id = f"{filename}_chunk_{i}"
                self.documents_data[chunk_id] = {
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk,
                    "chunk_size": len(chunk)
                }
                self.embeddings_data[chunk_id] = embeddings[i]
            
            # Save to files
            self._save_documents()
            self._save_embeddings()
            
            print(f"Added {len(text_chunks)} chunks from {filename} to knowledge base")
            
        except Exception as e:
            raise Exception(f"Error adding document to knowledge base: {str(e)}")
    
    def search_similar(self, query: str, n_results: int = 5) -> Tuple[List[str], List[str], List[float]]:
        """Search for similar content using vector similarity"""
        try:
            if not self.documents_data or not self.embeddings_data:
                return [], [], []
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Calculate similarities with all stored embeddings
            similarities = []
            chunk_ids = []
            
            for chunk_id, embedding in self.embeddings_data.items():
                if chunk_id in self.documents_data:
                    similarity = cosine_similarity(query_embedding.reshape(1, -1), 
                                                 embedding.reshape(1, -1))[0][0]
                    similarities.append(similarity)
                    chunk_ids.append(chunk_id)
            
            # Sort by similarity (descending)
            sorted_indices = np.argsort(similarities)[::-1][:n_results]
            
            # Extract results
            documents = []
            sources = []
            distances = []
            
            for idx in sorted_indices:
                chunk_id = chunk_ids[idx]
                doc_data = self.documents_data[chunk_id]
                
                documents.append(doc_data["text"])
                sources.append(doc_data["filename"])
                distances.append(1 - similarities[idx])  # Convert similarity to distance
            
            return documents, sources, distances
            
        except Exception as e:
            print(f"Error searching knowledge base: {str(e)}")
            return [], [], []
    
    def remove_document(self, filename: str) -> None:
        """Remove all chunks of a specific document"""
        try:
            # Find chunk IDs that belong to this document
            chunk_ids_to_remove = []
            for chunk_id, doc_data in self.documents_data.items():
                if doc_data.get("filename") == filename:
                    chunk_ids_to_remove.append(chunk_id)
            
            # Remove the chunks
            for chunk_id in chunk_ids_to_remove:
                if chunk_id in self.documents_data:
                    del self.documents_data[chunk_id]
                if chunk_id in self.embeddings_data:
                    del self.embeddings_data[chunk_id]
            
            # Save updated data
            if chunk_ids_to_remove:
                self._save_documents()
                self._save_embeddings()
                print(f"Removed {len(chunk_ids_to_remove)} chunks for document {filename}")
            
        except Exception as e:
            raise Exception(f"Error removing document from knowledge base: {str(e)}")
    
    def list_documents(self) -> List[Dict[str, any]]:
        """List all documents in the knowledge base"""
        try:
            # Group by filename
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
        """Clear all documents from the knowledge base"""
        try:
            # Clear all data
            self.documents_data = {}
            self.embeddings_data = {}
            
            # Save empty data to files
            self._save_documents()
            self._save_embeddings()
            
            print("Knowledge base cleared successfully")
            
        except Exception as e:
            raise Exception(f"Error clearing knowledge base: {str(e)}")
    
    def get_collection_info(self) -> Dict[str, any]:
        """Get information about the current collection"""
        try:
            count = len(self.documents_data)
            documents = self.list_documents()
            
            return {
                "total_chunks": count,
                "total_documents": len(documents),
                "storage_type": "file_based",
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            }
            
        except Exception as e:
            return {"error": str(e)}


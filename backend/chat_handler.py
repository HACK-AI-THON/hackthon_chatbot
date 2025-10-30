import os
import requests
import json
from typing import List, Tuple

# ====================
# ⚙️ CONFIGURATION - Databricks Environment
# ====================
DATABRICKS_WORKSPACE_URL = "https://dbc-4a93b454-f17b.cloud.databricks.com"
DATABRICKS_ORG_ID = "1978110925405963"
DATABRICKS_CLUSTER_ID = "1017-190030-sow9d43h"

class ChatHandler:
    """Handles chat interactions and response generation (Databricks-compatible)"""
    
    def __init__(self, knowledge_base, endpoint: str = None, token: str = None):
        self.knowledge_base = knowledge_base
        
        # Auto-detect Databricks environment
        self.is_databricks = self._is_databricks_env()
        
        # Get token (priority: parameter → dbutils → environment)
        self.access_token = token or self._get_token()
        
        # Get endpoint (priority: parameter → environment → default)
        self.databricks_endpoint = endpoint or os.getenv(
            "DATABRICKS_ENDPOINT",
            self._get_default_endpoint()
        )
        
        # Headers for API calls
        self.headers = {
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
            "Content-Type": "application/json"
        }
        
        # Status logging
        if self.access_token:
            print(f"✅ Chat handler initialized (Databricks: {self.is_databricks})")
        else:
            print("⚠️ WARNING: No Databricks token found!")
            print("   Set DATABRICKS_TOKEN environment variable or use dbutils.secrets")
    
    def _is_databricks_env(self) -> bool:
        """Detect if running in Databricks"""
        return os.path.exists("/dbfs") or os.path.exists("/Volumes") or "DATABRICKS_RUNTIME_VERSION" in os.environ
    
    def _get_token(self) -> str:
        """Get token from multiple sources (priority order)"""
        # Priority 1: Environment variable
        token = os.getenv("DATABRICKS_TOKEN")
        if token:
            return token
        
        # Priority 2: Databricks secrets (if available)
        if self.is_databricks:
            try:
                from pyspark.dbutils import DBUtils
                from pyspark.sql import SparkSession
                spark = SparkSession.builder.getOrCreate()
                dbutils = DBUtils(spark)
                token = dbutils.secrets.get(scope="hackathon-chatbot", key="databricks-token")
                print("✅ Using Databricks Secrets")
                return token
            except:
                pass
        
        return None
    
    def _get_default_endpoint(self) -> str:
        """Get default endpoint based on environment"""
        # Use configured workspace URL with fallback to environment variable
        workspace_url = os.getenv("DATABRICKS_HOST", DATABRICKS_WORKSPACE_URL)
        return f"{workspace_url}/serving-endpoints/databricks-llama-4-maverick/invocations"
    
    async def generate_response(self, query: str, use_openai: bool = False) -> Tuple[str, List[str]]:
        """Generate a response to user query"""
        
        # Search for relevant content
        documents, sources, distances = self.knowledge_base.search_similar(query, n_results=5)
        
        if not documents:
            return self._generate_no_content_response(), []
        
        # Filter documents by relevance (distance threshold)
        relevant_docs = []
        relevant_sources = []
        distance_threshold = 1.0  # Adjust based on testing
        
        for doc, source, distance in zip(documents, sources, distances):
            if distance < distance_threshold:
                relevant_docs.append(doc)
                relevant_sources.append(source)
        
        if not relevant_docs:
            return self._generate_no_relevant_content_response(), []
        
        # Generate response using Databricks LLM (use_openai parameter now means "use LLM")
        if use_openai:  # Using this flag to enable/disable LLM vs fallback
            try:
                response = await self._generate_databricks_response(query, relevant_docs)
                print(f"Databricks LLM response: {response}")
            except Exception as e:
                print(f"Databricks LLM error: {str(e)}")
                #response = self._generate_fallback_response(query, relevant_docs)
                response = "Exception in Databricks LLM response generation"
        else:
            #response = self._generate_fallback_response(query, relevant_docs)
            response = "No fallback method used"
            print(f"Fallback method not used")
        
        # Remove duplicate sources
        unique_sources = list(set(relevant_sources))
        
        return response, unique_sources
    
    async def _generate_databricks_response(self, query: str, documents: List[str]) -> str:
        """Generate response using Databricks LLM endpoint"""
        
        # Prepare context from documents
        context = "\n\n".join(documents[:3])  # Use top 3 most relevant documents
        
        # Create the prompt for the LLM
        prompt = f"""You are a helpful AI assistant that answers questions based on provided documents.

Guidelines:
- Answer questions using only the information provided in the context
- Format the entire response as a markdown document, with proper headings and subheadings
- If the context doesn't contain relevant information, say so clearly
- Be concise but comprehensive
- Quote relevant parts of the documents when appropriate
- If you're uncertain about something, express that uncertainty
- Always be helpful and professional
- Keep the response as short as possible


Context from documents:
{context}

Question: {query}

Please provide a helpful answer based on the context above."""

        # Prepare the request payload for Databricks
        payload = {
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            # Make the API call to Databricks
            response = requests.post(
                self.databricks_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                # Extract the response content from Databricks format
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    # Try alternative response format
                    return result.get('response', result.get('content', 'No response received'))
            else:
                print(f"Databricks API error: Status {response.status_code}, Response: {response.text}")
                raise Exception(f"API returned status code {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("Databricks API timeout")
            raise Exception("Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"Databricks API request error: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")
        except Exception as e:
            print(f"Databricks LLM error: {str(e)}")
            raise e
    
    def _generate_fallback_response(self, query: str, documents: List[str]) -> str:
        """Generate response using simple text matching (fallback)"""
        
        # Combine relevant documents
        context = " ".join(documents[:3])  # Use top 3 documents
        
        # Simple keyword matching and context extraction
        query_words = query.lower().split()
        context_lower = context.lower()
        
        # Find sentences containing query keywords
        sentences = context.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in query_words):
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            # Return the most relevant sentences
            response = ". ".join(relevant_sentences[:3])  # Top 3 sentences
            return f"Based on the uploaded documents: {response}."
        else:
            # Return a portion of the most relevant document
            first_doc = documents[0]
            if len(first_doc) > 300:
                first_doc = first_doc[:300] + "..."
            return f"Based on the uploaded documents, here's relevant information: {first_doc}"
    
    def _generate_no_content_response(self) -> str:
        """Response when no documents are found"""
        return """I don't have any documents uploaded yet to answer your question. 
        
Please upload some PDF or Word documents first using the Documents tab, then ask your question again."""
    
    def _generate_no_relevant_content_response(self) -> str:
        """Response when documents exist but none are relevant"""
        return """I couldn't find relevant information in the uploaded documents to answer your question. 
        
This could mean:
- The documents don't contain information about your topic
- Try rephrasing your question with different keywords
- Upload additional documents that might contain the information you're looking for"""
    
    def get_chat_suggestions(self) -> List[str]:
        """Get suggested questions based on available documents"""
        documents = self.knowledge_base.list_documents()
        
        if not documents:
            return [
                "Upload some documents first to get started!",
                "Try uploading PDF or Word files with content you'd like to explore"
            ]
        
        return [
            "What is the main topic discussed in the documents?",
            "Can you summarize the key points?",
            "What are the important details mentioned?",
            "Are there any specific procedures or steps outlined?",
            "What conclusions or recommendations are made?"
        ]


from dotenv import load_dotenv
import time
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredRTFLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import requests
import os
import logging
from time import time as current_time
from glob import glob
from django.core.cache import caches
from .models import Conversation, Message
from django.utils.html import strip_tags
from rest_framework.response import Response
from rest_framework import status
from typing import Dict, Generator, Optional, List, Any, Union
import json
from ratelimit import limits, sleep_and_retry
from functools import lru_cache
from datetime import datetime
from .knowledge_base.processor import KnowledgeBaseProcessor
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import groq
from unstructured.partition.auto import partition
import mimetypes
import magic

from django.conf import settings
CONFIG = settings.CHATBOT_CONFIG

# Initialize cache and logging
cache = caches["default"]
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='llm_integration.log'
)
load_dotenv()

# Enhanced Configuration
CONFIG = {
    "embedding_model": "BAAI/bge-small-en",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "search_k": 3,
    "similarity_threshold": 0.7,
    "api_timeout": 15,
    "max_retries": 3,
    "retry_delay": 1,
    "fallback_response": "I'm unable to answer right now. Please try again later.",
    "supported_files": {
        '*.pdf': PyPDFLoader,
        '*.docx': Docx2txtLoader,
        '*.txt': TextLoader,
        '*.csv': CSVLoader,
        '*.pptx': UnstructuredPowerPointLoader,
        '*.xlsx': UnstructuredExcelLoader,
        '*.html': UnstructuredHTMLLoader,
        '*.md': UnstructuredMarkdownLoader,
        '*.rtf': UnstructuredRTFLoader
    },
    "max_message_length": 2000,
    "cache_ttl": 3600,  # 1 hour
    "rate_limit": 10,  # requests per minute
    "rate_limit_window": 60,  # seconds
    "knowledge_base_dir": "knowledge_base",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "min_chunk_size": 100,
    "max_chunk_size": 2000,
}

# Initialize components
try:
    # Initialize embeddings
    embeddings = SentenceTransformer(CONFIG["embedding_model"])
    
    # Initialize ChromaDB
    chroma_client = chromadb.Client(Settings(
        persist_directory="chroma_db",
        anonymized_telemetry=False
    ))
    collection = chroma_client.get_or_create_collection("university_docs")
    
    # Initialize Groq client (if API key is available)
    groq_client = None
    if os.getenv("GROQ_API_KEY"):
        groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    logging.info("Successfully initialized all components")
except Exception as e:
    logging.error(f"Failed to initialize components: {e}")
    raise

# Rate limiting decorator
@sleep_and_retry
@limits(calls=CONFIG["rate_limit"], period=CONFIG["rate_limit_window"])
def rate_limited_api_call(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class KnowledgeBaseHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in CONFIG["supported_files"].keys()):
            logging.info(f"Detected file change: {event.src_path}")
            load_knowledge_base(force=True)

def initialize_file_watcher():
    """Initialize file watcher for knowledge base directory."""
    observer = Observer()
    observer.schedule(
        KnowledgeBaseHandler(),
        path=CONFIG["knowledge_base_dir"],
        recursive=True
    )
    observer.start()
    return observer

def get_file_type(file_path: str) -> Optional[str]:
    """Get file type using python-magic."""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        return file_type
    except Exception as e:
        logging.error(f"Error detecting file type: {e}")
        return None

def validate_file(file_path: str) -> bool:
    """Validate file size and type."""
    try:
        # Check file size
        if os.path.getsize(file_path) > CONFIG["max_file_size"]:
            logging.error(f"File too large: {file_path}")
            return False

        # Check file type
        file_type = get_file_type(file_path)
        if not file_type:
            return False

        # Check if file type is supported
        supported_mimes = {
            'application/pdf': '*.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '*.docx',
            'text/plain': '*.txt',
            'text/csv': '*.csv',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '*.pptx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '*.xlsx',
            'text/html': '*.html',
            'text/markdown': '*.md',
            'application/rtf': '*.rtf'
        }

        if file_type not in supported_mimes:
            logging.error(f"Unsupported file type: {file_type}")
            return False

        return True
    except Exception as e:
        logging.error(f"Error validating file: {e}")
        return False

def process_document(file_path: str) -> List[Dict]:
    """Process a document and return chunks with metadata."""
    try:
        if not validate_file(file_path):
            return []

        # Get file type and appropriate loader
        file_type = get_file_type(file_path)
        loader_class = CONFIG["supported_files"].get(f"*.{file_path.split('.')[-1]}")
        
        if not loader_class:
            # Fallback to unstructured
            elements = partition(filename=file_path)
            chunks = []
            current_chunk = []
            current_size = 0

            for element in elements:
                text = str(element)
                if current_size + len(text) > CONFIG["chunk_size"]:
                    if current_chunk:
                        chunks.append({
                            "content": " ".join(current_chunk),
                            "metadata": {
                                "source": file_path,
                                "type": file_type,
                                "page": getattr(element, "page_number", None)
                            }
                        })
                    current_chunk = [text]
                    current_size = len(text)
                else:
                    current_chunk.append(text)
                    current_size += len(text)

            if current_chunk:
                chunks.append({
                    "content": " ".join(current_chunk),
                    "metadata": {
                        "source": file_path,
                        "type": file_type
                    }
                })
        else:
            # Use LangChain loader
            loader = loader_class(file_path)
            documents = loader.load()
            
            # Split documents into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=CONFIG["chunk_size"],
                chunk_overlap=CONFIG["chunk_overlap"]
            )
            chunks = splitter.split_documents(documents)
            
            # Convert to our format
            chunks = [{
                "content": chunk.page_content,
                "metadata": {
                    **chunk.metadata,
                    "source": file_path,
                    "type": file_type
                }
            } for chunk in chunks]

        return chunks

    except Exception as e:
        logging.error(f"Error processing document {file_path}: {e}")
        return []

def load_knowledge_base(force=False):
    """Load documents into ChromaDB with enhanced processing."""
    try:
        os.makedirs(CONFIG["knowledge_base_dir"], exist_ok=True)
        
        # Check cache
        if not force and cache.get("knowledge_base_loaded"):
            return
            
        all_chunks = []
        for pattern in CONFIG["supported_files"].keys():
            for file_path in Path(CONFIG["knowledge_base_dir"]).glob(pattern):
                try:
                    chunks = process_document(str(file_path))
                    if chunks:
                        all_chunks.extend(chunks)
                        logging.info(f"Processed: {file_path} ({len(chunks)} chunks)")
                except Exception as e:
                    logging.error(f"Failed to process {file_path}: {e}")

        if not all_chunks:
            logging.warning("No valid documents found")
            return

        # Add to ChromaDB
        collection.add(
            documents=[chunk["content"] for chunk in all_chunks],
            metadatas=[chunk["metadata"] for chunk in all_chunks],
            ids=[f"doc_{i}" for i in range(len(all_chunks))]
        )
        
        cache.set("knowledge_base_loaded", True, timeout=CONFIG["cache_ttl"])
        logging.info(f"Loaded {len(all_chunks)} chunks from knowledge base")

    except Exception as e:
        logging.error(f"Knowledge base loading failed: {e}")

def search_knowledge_base(query: str, k: int = 3) -> List[Dict]:
    """Search the knowledge base for relevant documents."""
    try:
        # Get query embedding
        query_embedding = embeddings.encode(query).tolist()
        
        # Search in ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        return [
            {
                "content": doc,
                "metadata": meta
            }
            for doc, meta in zip(results["documents"][0], results["metadatas"][0])
        ]
    except Exception as e:
        logging.error(f"Knowledge base search failed: {e}")
        return []

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not text:
        return ""
    # Remove HTML tags and escape special characters
    text = strip_tags(text)
    # Limit message length
    if len(text) > CONFIG["max_message_length"]:
        text = text[:CONFIG["max_message_length"]] + "..."
    return text

@lru_cache(maxsize=100)
def get_cached_response(query: str) -> Optional[Dict]:
    """Get cached response for a query."""
    cache_key = f"chat_response_{hash(query)}"
    return cache.get(cache_key)

def cache_response(query: str, response: Dict) -> None:
    """Cache a response for a query."""
    cache_key = f"chat_response_{hash(query)}"
    cache.set(cache_key, response, timeout=CONFIG["cache_ttl"])

def query_deepseek(prompt: str) -> Optional[str]:
    """Query the DeepSeek API for a response."""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            logging.warning("DeepSeek API key not found")
            return None

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"DeepSeek API error: {e}")
        return None

def get_recent_messages(conversation_id: int, limit: int = 5) -> List[Message]:
    """Get recent messages for context with error handling."""
    try:
        return list(Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False
        ).order_by('-created_at')[:limit])
    except Exception as e:
        logging.error(f"Error fetching recent messages: {e}")
        return []

def generate_response(user_query: str, conversation_id: Optional[int] = None) -> Dict:
    """Generate a response with enhanced context and error handling."""
    try:
        # Sanitize input
        user_query = sanitize_input(user_query)
        if not user_query:
            return {
                "response": "Please enter a valid question.",
                "source_hint": None,
                "status": "error"
            }

        # Check cache first
        if cached_response := get_cached_response(user_query):
            return {**cached_response, "cached": True}

        # Get context from recent messages
        context = ""
        if conversation_id:
            recent_messages = get_recent_messages(conversation_id)
            context = "\n".join([
                f"{'User' if msg.is_user else 'Bot'}: {msg.content}"
                for msg in reversed(recent_messages)
            ])

        # Handle common greetings
        greetings = ["hi", "hello", "hey", "greetings", "hola"]
        if user_query.lower() in greetings:
            response = {
                "response": "Hello! How can I help you today?",
                "source_hint": None,
                "status": "success"
            }
            cache_response(user_query, response)
            return response

        if any(word in user_query.lower() for word in ["thank", "thanks"]):
            response = {
                "response": "You're welcome! Is there anything else I can help with?",
                "source_hint": None,
                "status": "success"
            }
            cache_response(user_query, response)
            return response

        # Try knowledge base first
        docs = search_knowledge_base(user_query)
        if not docs:
            load_knowledge_base()
            docs = search_knowledge_base(user_query)

        if docs:
            context = "\n".join([
                f"[Source {i+1}]: {doc['content']}" 
                for i, doc in enumerate(docs)
            ])
            
            prompt = f"""Context from previous messages:
{context}

Current question: {user_query}

Using these sources, answer the question concisely:
Guidelines:
- Be precise and helpful
- Reference sources like [1], [2] when applicable
- If unsure, say so"""
            
            response = query_deepseek(prompt) if os.getenv("DEEPSEEK_API_KEY") else context
            result = {
                "response": response or context,
                "source_hint": "University knowledge base",
                "status": "success"
            }
            
            cache_response(user_query, result)
            return result

        # Fallback to general knowledge
        if os.getenv("DEEPSEEK_API_KEY"):
            if response := query_deepseek(user_query):
                result = {
                    "response": response,
                    "source_hint": None,
                    "status": "success"
                }
                cache_response(user_query, result)
                return result

        return {
            "response": CONFIG["fallback_response"],
            "source_hint": None,
            "status": "success"
        }

    except Exception as e:
        logging.error(f"Error generating response: {e}", exc_info=True)
        return {
            "response": "I apologize, but I encountered an error. Please try again.",
            "source_hint": None,
            "status": "error"
        }

def stream_response(query: str, conversation=None) -> Generator:
    """Enhanced streaming with better error handling and rate limiting."""
    try:
        # Validate input
        if not query.strip():
            yield {
                "type": "error",
                "message": "Please enter a valid question",
                "conversation_id": conversation.id if conversation else None
            }
            return

        # Process message
        if conversation:
            Message.objects.create(
                conversation=conversation,
                content=query,
                is_user=True
            )
            yield {
                "type": "status", 
                "status": "typing",
                "conversation_id": conversation.id
            }

        # Generate response
        response_data = generate_response(query, conversation.id if conversation else None)
        
        if conversation:
            Message.objects.create(
                conversation=conversation,
                content=response_data["response"],
                is_user=False,
                source_hint=response_data.get("source_hint")
            )
            
        yield {
            "type": "message",
            "content": response_data["response"],
            "source_hint": response_data.get("source_hint"),
            "status": response_data["status"],
            "conversation_id": conversation.id if conversation else None
        }

    except Exception as e:
        logging.error(f"Stream error: {e}", exc_info=True)
        yield {
            "type": "error",
            "message": "An error occurred. Please try again.",
            "conversation_id": conversation.id if conversation else None
        }

from django.utils import timezone

def edit_message(message_id: int, new_content: str) -> dict:
    """Edit a user message and regenerate bot response."""
    try:
        message = Message.objects.get(id=message_id)
        message.content = new_content
        message.edited_at = timezone.now()
        message.save()

        # Delete the bot's previous response
        Message.objects.filter(
            conversation=message.conversation,
            is_user=False,
            created_at__gt=message.created_at
        ).delete()
        for event in stream_response(new_content, message.conversation):
            yield event  # Forward SSE events

        # Generate new response
        return stream_response(new_content, message.conversation)
    except Exception as e:
        yield {"type": "error", "message": str(e)}
        return {"error": str(e)}

# Initialize on startup
try:
    load_knowledge_base()
    initialize_file_watcher()
except Exception as e:
    logging.critical(f"Startup initialization failed: {e}")

if __name__ == "__main__":
    load_knowledge_base()
    initialize_file_watcher()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if observer:
            observer.stop()
    if observer:
        observer.join()

def get_ollama_response(prompt: str) -> Generator[str, None, None]:
    """Get response from local Ollama instance."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mixtral",  # or "llama2" based on preference
                "prompt": prompt,
                "stream": True
            },
            timeout=30
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    json_response = json.loads(line)
                    if 'response' in json_response:
                        yield json_response['response']
                except json.JSONDecodeError:
                    continue
                    
    except Exception as e:
        logging.error(f"Ollama API error: {e}")
        yield "I apologize, but I'm having trouble connecting to the local model."

def get_llm_response(
    query: str,
    context: Optional[List[Dict]] = None,
    use_groq: bool = True
) -> Generator[str, None, None]:
    """Get response from LLM (Groq or Ollama)."""
    try:
        # Prepare prompt with context if available
        prompt = query
        if context:
            context_text = "\n".join([doc["content"] for doc in context])
            prompt = f"""Context information:
{context_text}

Question: {query}

Answer based on the context if possible, otherwise provide a general response:"""

        if use_groq and groq_client:
            try:
                # Use Groq
                response = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama2-70b-4096",
                    temperature=0.7,
                    max_tokens=1000,
                    stream=True
                )
                
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            except Exception as e:
                logging.warning(f"Groq API error, falling back to Ollama: {e}")
                yield from get_ollama_response(prompt)
        else:
            # Use Ollama
            yield from get_ollama_response(prompt)

    except Exception as e:
        logging.error(f"LLM response generation failed: {e}")
        yield "I apologize, but I'm having trouble generating a response right now."

def process_message(
    message: str,
    conversation_id: Optional[int] = None
) -> Generator[str, None, None]:
    """Process a user message and generate a response."""
    try:
        # Create or get conversation
        conversation = None
        if conversation_id:
            conversation = Conversation.objects.get(id=conversation_id)
        else:
            conversation = Conversation.objects.create(title=message[:50])

        # Save user message
        Message.objects.create(
            conversation=conversation,
            content=message,
            is_user=True
        )

        # Search knowledge base
        relevant_docs = search_knowledge_base(message)
        
        # Generate response
        response_text = ""
        for chunk in get_llm_response(message, relevant_docs):
            response_text += chunk
            yield chunk

        # Save bot response
        Message.objects.create(
            conversation=conversation,
            content=response_text,
            is_user=False,
            source_documents=[doc["metadata"] for doc in relevant_docs] if relevant_docs else None
        )

    except Exception as e:
        logging.error(f"Message processing failed: {e}")
        yield "I apologize, but I encountered an error while processing your message."

# Rate limiting configuration
CALLS = 60  # Number of calls allowed
RATE_LIMIT_PERIOD = 60  # Time period in seconds

class LLMIntegration:
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')
        self.knowledge_base = KnowledgeBaseProcessor()
        
    @sleep_and_retry
    @limits(calls=CALLS, period=RATE_LIMIT_PERIOD)
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Generate a response using DeepSeek's API."""
        try:
            # Prepare the prompt with context if available
            if context:
                context_text = "\n\n".join([
                    f"Context {i+1} (Similarity: {c['similarity']:.2f}):\n{c['text']}"
                    for i, c in enumerate(context)
                ])
                system_message = {
                    "role": "system",
                    "content": f"You are a helpful AI assistant. Use the following context to inform your response:\n\n{context_text}"
                }
                messages = [system_message] + messages

            # Prepare the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            # Parse and return the response
            result = response.json()
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": result["model"],
                "usage": result["usage"],
                "created_at": datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid API response format: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")

    def process_message(
        self,
        message: str,
        conversation_history: List[Dict[str, str]],
        search_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """Process a message and generate a response."""
        try:
            # Search knowledge base if enabled
            context = None
            if search_knowledge_base:
                context = self.knowledge_base.search(message)

            # Generate response
            response = self.generate_response(
                messages=conversation_history + [{"role": "user", "content": message}],
                context=context
            )

            return {
                "status": "success",
                "response": response,
                "context_used": bool(context)
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "created_at": datetime.now().isoformat()
            }

    def add_to_knowledge_base(self, file_path: str) -> Dict[str, Any]:
        """Add a document to the knowledge base."""
        try:
            chunks = self.knowledge_base.process_document(file_path)
            return {
                "status": "success",
                "chunks_added": len(chunks),
                "file": file_path
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "file": file_path
            }
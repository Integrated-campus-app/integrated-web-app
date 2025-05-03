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
    UnstructuredPowerPointLoader
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

cache = caches["default"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='llm_integration.log'
)

load_dotenv()

# Configuration
CONFIG = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "search_k": 3,
    "api_timeout": 15,
    "fallback_response": "I'm unable to answer right now. Please try again later.",
    "supported_files": {
        '*.pdf': PyPDFLoader,
        '*.docx': Docx2txtLoader,
        '*.txt': TextLoader,
        '*.csv': CSVLoader,
        '*.pptx': UnstructuredPowerPointLoader
    }
}

class KnowledgeBaseHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in CONFIG["supported_files"]):
            logging.info(f"Detected file change: {event.src_path}")
            load_knowledge_base(force=True)

# Initialize embeddings with proper error handling
try:
    embeddings = HuggingFaceEmbeddings(
        model_name=CONFIG["embedding_model"],
        model_kwargs={"device": "cpu"}
    )
    logging.info("Embeddings initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize embeddings: {e}")
    raise RuntimeError("Embedding system initialization failed")

vector_store = None
last_load_time = 0
observer = None

def initialize_file_watcher():
    global observer
    try:
        observer = Observer()
        observer.schedule(KnowledgeBaseHandler(), path='knowledge_base', recursive=True)
        observer.start()
        logging.info("File watcher initialized")
    except Exception as e:
        logging.error(f"Failed to initialize file watcher: {e}")

def load_knowledge_base(force=False):
    global vector_store, last_load_time
    cached_store = cache.get("vector_store")
    if cached_store and not force:
        vector_store = cached_store
        return
    
    try:
        # Create knowledge_base directory if it doesn't exist
        os.makedirs("knowledge_base", exist_ok=True)
        
        if vector_store and (current_time() - last_load_time) < 3600 and not force:
            return
            
        documents = []        
        # Load all supported files from knowledge_base folder
        for pattern, loader_class in CONFIG["supported_files"].items():
            for file_path in glob(os.path.join("knowledge_base", pattern)):
                try:
                    loader = loader_class(file_path)
                    documents.extend(loader.load())
                    logging.info(f"Successfully loaded: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to load {file_path}: {e}")

        if not documents:
            logging.warning("No valid documents found in knowledge_base folder")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["chunk_size"],
            chunk_overlap=CONFIG["chunk_overlap"]
        )
        chunks = splitter.split_documents(documents)

        vector_store = FAISS.from_documents(chunks, embeddings)
        last_load_time = current_time()
        logging.info(f"Knowledge base reloaded with {len(chunks)} chunks from {len(documents)} documents")
        cache.set("vector_store", vector_store, timeout=3600)

    except Exception as e:
        logging.error(f"Knowledge base loading failed: {e}")
        vector_store = None

def check_file_changes():
    current_files = {f: os.path.getmtime(f) for f in glob("knowledge_base/*")}
    cached_files = cache.get("cached_files", {})
    return current_files != cached_files

def query_deepseek(prompt: str) -> str:
    """Call DeepSeek API with proper error handling"""
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
            },
            timeout=CONFIG["api_timeout"]
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"DeepSeek API call failed: {e}")
        return None
    
def stream_response(query: str, conversation=None):
    """Handles SSE streaming and saves messages to DB."""
    try:
        # Save user message if conversation is provided
        if conversation:
            Message.objects.create(
                conversation=conversation,
                content=query,
                is_user=True
            )

        yield {"type": "status", "status": "typing"}
        
        # Generate AI response
        ai_response = generate_response(query)  # Reuse existing function

        # Save AI response if conversation exists
        if conversation:
            Message.objects.create(
                conversation=conversation,
                content=ai_response,
                is_user=False
            )

        yield {"type": "message", "content": ai_response}

    except Exception as e:
        yield {"type": "error", "message": str(e)}


def generate_response(user_query: str) -> str:
    # Handle greetings
    greetings = ["hi", "hello", "hey", "greetings"]
    if user_query.lower().strip() in greetings:
        return "Hello! I can help you with information from various university documents. What would you like to know?"
    
    # Handle thanks
    if any(word in user_query.lower() for word in ["thank", "thanks", "appreciate"]):
        return "You're welcome! Let me know if you have any other questions."

    # Validate input
    if not user_query.strip():
        return "Please enter a valid question."

    try:
        # Ensure knowledge base is loaded
        if not vector_store:
            load_knowledge_base()
            if not vector_store:
                return CONFIG["fallback_response"]

        # Get context from all documents
        docs = vector_store.similarity_search(user_query, k=CONFIG["search_k"])
        
        # Format context with source information
        context = ""
        if docs:
            context = "\n\n".join(
                f"From {os.path.basename(doc.metadata['source'])}:\n{doc.page_content}"
                for doc in docs
            )

        # Build prompt
        prompt = (
            f"User Question: {user_query}\n\n"
            f"Relevant Context from University Documents:\n{context}\n\n"
            "Instructions:\n"
            "1. Answer concisely (1-3 sentences)\n"
            "2. Specify which document the information comes from when possible\n"
            "3. If unsure, say 'I couldn't find definitive information about this'\n"
            "4. For complex questions, suggest looking at the full document"
        )

        # Try DeepSeek API
        if os.getenv("DEEPSEEK_API_KEY"):
            response = query_deepseek(prompt)
            if response:
                return response

        # Fallback response with context
        if context:
            return (
                "Based on university documents:\n\n" + 
                context +
                "\n\nFor more details, please check the full documents."
            )
        return "I couldn't find relevant information in our documents. Could you rephrase your question?"

    except Exception as e:
        logging.error(f"Response generation failed: {e}")
        return CONFIG["fallback_response"]

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
        observer.stop()
    observer.join()
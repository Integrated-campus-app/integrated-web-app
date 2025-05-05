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
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
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
        '*.pptx': UnstructuredPowerPointLoader
    }
}

class KnowledgeBaseHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if any(event.src_path.endswith(ext) for ext in CONFIG["supported_files"]):
            logging.info(f"Detected file change: {event.src_path}")
            load_knowledge_base(force=True)

# Initialize embeddings
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
    if cached_store := cache.get("vector_store"):
        if not force:
            vector_store = cached_store
            return

    try:
        os.makedirs("knowledge_base", exist_ok=True)
        
        if vector_store and (current_time() - last_load_time) < 3600 and not force:
            return
            
        documents = []
        for pattern, loader_class in CONFIG["supported_files"].items():
            for file_path in glob(os.path.join("knowledge_base", pattern)):
                try:
                    documents.extend(loader_class(file_path).load())
                    logging.info(f"Loaded: {file_path}")
                except Exception as e:
                    logging.error(f"Failed to load {file_path}: {e}")

        if not documents:
            logging.warning("No valid documents found")
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CONFIG["chunk_size"],
            chunk_overlap=CONFIG["chunk_overlap"]
        )
        chunks = splitter.split_documents(documents)
        vector_store = FAISS.from_documents(chunks, embeddings)
        last_load_time = current_time()
        cache.set("vector_store", vector_store, timeout=3600)
        logging.info(f"Loaded {len(chunks)} chunks from {len(documents)} documents")

    except Exception as e:
        logging.error(f"Knowledge base loading failed: {e}")
        vector_store = None

def query_deepseek(prompt: str) -> str:
    """Enhanced DeepSeek API query with retries and rate limiting"""
    for attempt in range(CONFIG["max_retries"]):
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 512,
                    "stream": False
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}"
                },
                timeout=CONFIG["api_timeout"]
            )
            
            if response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', CONFIG["retry_delay"]))
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < CONFIG["max_retries"] - 1:
                time.sleep(CONFIG["retry_delay"] * (attempt + 1))
    return None


def generate_response(user_query: str) -> dict:
    """Optimized response generation with better context handling"""
    user_query = user_query.strip()
    if not user_query:
        return {"response": "Please enter a valid question.", "source_hint": None}

    # Handle common greetings
    greetings = ["hi", "hello", "hey", "greetings", "hola"]
    if user_query.lower() in greetings:
        return {"response": "Hello! How can I help you today?", "source_hint": None}
    if any(word in user_query.lower() for word in ["thank", "thanks"]):
        return {"response": "You're welcome! Is there anything else I can help with?", "source_hint": None}

    try:
        # Try knowledge base first
        if not vector_store:
            load_knowledge_base()

        if vector_store:
            docs = vector_store.similarity_search_with_score(
                user_query, 
                k=CONFIG["search_k"]
            )
            
            if docs and docs[0][1] > CONFIG["similarity_threshold"]:
                context = "\n".join([
                    f"[Source {i+1}]: {doc[0].page_content}" 
                    for i, doc in enumerate(docs)
                ])
                
                prompt = f"""Using these sources, answer the question concisely:
{context}

Question: {user_query}
Guidelines:
- Be precise and helpful
- Reference sources like [1], [2] when applicable
- If unsure, say so"""
                
                response = query_deepseek(prompt) if os.getenv("DEEPSEEK_API_KEY") else context
                return {
                    "response": response or context,
                    "source_hint": "University knowledge base"
                }

        # Fallback to general knowledge
        if os.getenv("DEEPSEEK_API_KEY"):
            if response := query_deepseek(user_query):
                return {"response": response, "source_hint": None}

        return {"response": CONFIG["fallback_response"], "source_hint": None}

    except Exception as e:
        logging.error(f"Response generation error: {e}")
        return {"response": CONFIG["fallback_response"], "source_hint": None}

def stream_response(query: str, conversation=None):
    """Enhanced streaming with better state management"""
    try:
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

        response_data = generate_response(query)
        
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
            "conversation_id": conversation.id if conversation else None
        }

    except Exception as e:
        logging.error(f"Stream error: {e}")
        yield {
            "type": "error",
            "message": str(e),
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
from pathlib import Path
import os

# Base directory for the knowledge base
KB_BASE_DIR = Path(__file__).parent.parent / 'knowledge_base'

# Directory for storing document chunks
CHUNKS_DIR = KB_BASE_DIR / 'chunks'

# Directory for storing embeddings
EMBEDDINGS_DIR = KB_BASE_DIR / 'embeddings'

# Directory for storing raw documents
DOCUMENTS_DIR = KB_BASE_DIR / 'documents'

# Create directories if they don't exist
for directory in [KB_BASE_DIR, CHUNKS_DIR, EMBEDDINGS_DIR, DOCUMENTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Chunking configuration
CHUNK_SIZE = 1000  # Number of characters per chunk
CHUNK_OVERLAP = 200  # Number of characters to overlap between chunks

# Embedding configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Similarity threshold for KB search
SIMILARITY_THRESHOLD = 0.7

# File types supported for document processing
SUPPORTED_FILE_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.txt': 'text/plain',
    '.md': 'text/markdown'
}

# Maximum file size (in bytes) for document processing
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB 
import os
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import json
from .config import (
    CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL,
    EMBEDDING_DIMENSION, CHUNKS_DIR, EMBEDDINGS_DIR,
    SUPPORTED_FILE_TYPES, MAX_FILE_SIZE
)

class KnowledgeBaseProcessor:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = None
        self.chunks = []
        self.load_or_create_index()

    def load_or_create_index(self):
        """Load existing index or create a new one."""
        index_path = EMBEDDINGS_DIR / 'faiss_index.bin'
        chunks_path = CHUNKS_DIR / 'chunks.json'

        if index_path.exists() and chunks_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(chunks_path, 'r', encoding='utf-8') as f:
                self.chunks = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            self.chunks = []

    def save_index(self):
        """Save the current index and chunks."""
        index_path = EMBEDDINGS_DIR / 'faiss_index.bin'
        chunks_path = CHUNKS_DIR / 'chunks.json'

        faiss.write_index(self.index, str(index_path))
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

    def process_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a document and return its chunks."""
        if not self._validate_file(file_path):
            raise ValueError(f"Invalid file: {file_path}")

        # Extract text based on file type
        text = self._extract_text(file_path)
        
        # Split text into chunks
        chunks = self._split_text(text)
        
        # Create embeddings for chunks
        embeddings = self.model.encode(chunks)
        
        # Add to index
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Store chunks with metadata
        chunk_data = [
            {
                'text': chunk,
                'source': str(file_path),
                'chunk_index': i
            }
            for i, chunk in enumerate(chunks)
        ]
        self.chunks.extend(chunk_data)
        
        # Save updated index and chunks
        self.save_index()
        
        return chunk_data

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant chunks."""
        # Create query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search index
        distances, indices = self.index.search(
            np.array([query_embedding]).astype('float32'), k
        )
        
        # Return results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                result = self.chunks[idx].copy()
                result['similarity'] = 1 - (distance / 2)  # Convert distance to similarity
                results.append(result)
        
        return results

    def _validate_file(self, file_path: Path) -> bool:
        """Validate file type and size."""
        if not file_path.exists():
            return False
            
        if file_path.suffix.lower() not in SUPPORTED_FILE_TYPES:
            return False
            
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False
            
        return True

    def _extract_text(self, file_path: Path) -> str:
        """Extract text from different file types."""
        suffix = file_path.suffix.lower()
        
        if suffix == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif suffix == '.pdf':
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                return ' '.join(page.extract_text() for page in pdf.pages)
        elif suffix in ['.docx', '.doc']:
            import docx
            doc = docx.Document(file_path)
            return ' '.join(paragraph.text for paragraph in doc.paragraphs)
        elif suffix == '.md':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + CHUNK_SIZE
            if end > text_length:
                end = text_length
            chunks.append(text[start:end])
            start = end - CHUNK_OVERLAP

        return chunks 
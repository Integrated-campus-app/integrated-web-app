from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFaceHub
from langchain_huggingface import HuggingFaceEmbeddings
import os

load_dotenv()

# Verify token exists
if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
    raise ValueError("Missing HuggingFace API token")

# Initialize with specific model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",  # Lightweight alternative
    model_kwargs={"device": "cpu"},
    encode_kwargs={
        "normalize_embeddings": True,
        "batch_size": 4  # Reduce if memory issues occur
    }
)
vector_store = None

def load_knowledge_base():
    global vector_store
    try:
        loader = PyPDFLoader("knowledge_base/ASTUlegislation2017.pdf")
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
        texts = text_splitter.split_documents(documents)
        vector_store = FAISS.from_documents(texts, embeddings)
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        vector_store = None

def generate_response(query):
    if not vector_store:
        load_knowledge_base()
    
    try:
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-large",
            model_kwargs={
                "temperature": 0.5,
                "max_length": 256,
                "do_sample": True
            }
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            return_source_documents=True  # Add this to debug
        )
        
        result = qa_chain({"query": query})
        return result["result"]
        
    except Exception as e:
        print(f"Full error details: {str(e)}")
        return "I encountered an error processing your request. Please try again."

# Pre-load knowledge base
load_knowledge_base()
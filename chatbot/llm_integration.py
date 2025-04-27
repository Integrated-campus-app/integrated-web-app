from langchain.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub
from langchain_huggingface import HuggingFaceEmbeddings
import os

# Initialize the knowledge base once when the server starts
embeddings = HuggingFaceEmbeddings()
vector_store = None
qa_chain = None

def initialize_knowledge_base():
    global vector_store, qa_chain
    
    # Load all documents from the knowledge_base folder
    documents = []
    for filename in os.listdir('knowledge_base'):
        filepath = os.path.join('knowledge_base', filename)
        
        if filename.endswith('.pdf'):
            loader = PyPDFLoader(filepath)
        elif filename.endswith('.docx'):
            loader = Docx2txtLoader(filepath)
        else:
            loader = TextLoader(filepath)
            
        documents.extend(loader.load())
    
    # Split documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    
    # Create vector store
    vector_store = FAISS.from_documents(texts, embeddings)
    
    # Initialize QA chain with a free LLM
    llm = HuggingFaceHub(
        repo_id="google/flan-t5-base",  # Free model
        model_kwargs={"temperature":0.5, "max_length":512}
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )

def generate_response(query):
    if qa_chain is None:
        return "The knowledge base is not initialized yet. Please contact the administrator."
    
    try:
        result = qa_chain.run(query)
        return result
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

# Initialize the knowledge base when this module is imported
initialize_knowledge_base()
"""
RAG Pipeline Module

Handles document loading, chunking, embedding, and retrieval.
Uses ChromaDB as the vector store and LangChain for orchestration.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


@dataclass
class RetrievalResult:
    """Result of a retrieval query"""
    query: str
    chunks: List[str]
    documents: List[Document]
    scores: List[float]
    metadata: List[Dict[str, Any]]


class DocumentLoader:
    """Handles loading documents from various sources"""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': PyPDFLoader,
        '.txt': TextLoader,
        '.md': TextLoader,
    }
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the document loader.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_file(self, file_path: str) -> List[Document]:
        """Load a single file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        loader_class = self.SUPPORTED_EXTENSIONS[ext]
        loader = loader_class(str(path))
        documents = loader.load()
        
        # Add source metadata
        for doc in documents:
            doc.metadata['source'] = str(path)
            doc.metadata['filename'] = path.name
        
        return documents
    
    def load_directory(self, dir_path: str, glob: str = "**/*") -> List[Document]:
        """Load all supported files from a directory"""
        all_docs = []
        path = Path(dir_path)
        
        for ext in self.SUPPORTED_EXTENSIONS.keys():
            pattern = f"{glob}{ext}"
            for file_path in path.glob(pattern):
                try:
                    docs = self.load_file(str(file_path))
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"Warning: Failed to load {file_path}: {e}")
        
        return all_docs
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        return self.text_splitter.split_documents(documents)


class VectorStore:
    """Manages the ChromaDB vector store for document retrieval"""
    
    def __init__(
        self,
        persist_directory: str = "./data/embeddings",
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "sentinel_rag"
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Where to store the ChromaDB data
            embedding_model: HuggingFace model for embeddings
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings
        print(f"Loading embedding model: {embedding_model}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'}  # Use 'cuda' if available
        )
        
        # Initialize or load ChromaDB
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
        
        print(f"Vector store initialized at {persist_directory}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Returns:
            List of document IDs
        """
        ids = self.vectorstore.add_documents(documents)
        return ids
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of (Document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter
        )
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.vectorstore.delete_collection()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        collection = self.vectorstore._collection
        return {
            "name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory
        }


class RAGPipeline:
    """
    Complete RAG pipeline for document retrieval.
    
    This is the "victim" system that Sentinel protects.
    Without Sentinel, this pipeline is vulnerable to indirect prompt injection.
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/embeddings",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        top_k: int = 5
    ):
        """
        Initialize the RAG pipeline.
        
        Args:
            persist_directory: ChromaDB storage location
            embedding_model: Model for document embeddings
            chunk_size: Size of document chunks
            chunk_overlap: Overlap between chunks
            top_k: Default number of results to retrieve
        """
        self.document_loader = DocumentLoader(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.vector_store = VectorStore(
            persist_directory=persist_directory,
            embedding_model=embedding_model
        )
        self.top_k = top_k
    
    def ingest_file(self, file_path: str) -> int:
        """
        Ingest a single file into the RAG system.
        
        Returns:
            Number of chunks added
        """
        documents = self.document_loader.load_file(file_path)
        chunks = self.document_loader.chunk_documents(documents)
        self.vector_store.add_documents(chunks)
        return len(chunks)
    
    def ingest_directory(self, dir_path: str) -> int:
        """
        Ingest all files from a directory.
        
        Returns:
            Number of chunks added
        """
        documents = self.document_loader.load_directory(dir_path)
        chunks = self.document_loader.chunk_documents(documents)
        self.vector_store.add_documents(chunks)
        return len(chunks)
    
    def retrieve(self, query: str, k: Optional[int] = None) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.
        
        This is where Sentinel should intercept and sanitize results.
        
        Args:
            query: User's question
            k: Number of results (default: self.top_k)
            
        Returns:
            RetrievalResult with chunks and metadata
        """
        k = k or self.top_k
        results = self.vector_store.search(query, k=k)
        
        documents = [doc for doc, _ in results]
        scores = [score for _, score in results]
        chunks = [doc.page_content for doc in documents]
        metadata = [doc.metadata for doc in documents]
        
        return RetrievalResult(
            query=query,
            chunks=chunks,
            documents=documents,
            scores=scores,
            metadata=metadata
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return self.vector_store.get_collection_stats()
    
    def clear(self):
        """Clear all documents from the store"""
        self.vector_store.delete_collection()
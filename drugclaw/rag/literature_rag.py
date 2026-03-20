#!/usr/bin/env python3
"""
Literature RAG - Private and public literature knowledge base retrieval
Supports:
- PDF ingestion and embedding
- Vector search over private literature
- Hybrid retrieval: public database + private RAG
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import os
import re
import logging
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from openai import OpenAI as OpenAIClient

logger = logging.getLogger(__name__)

@dataclass
class RetrievedDocument:
    """Retrieved document from RAG"""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str  # "private" or "public"

class LiteratureRAG:
    """Literature RAG system for private and public literature"""
    
    def __init__(self, 
                 db_path: str = "./data/chroma_db",
                 embedding_model: str = "BAAI/bge-base-en-v1.5",
                 openai_api_key: Optional[str] = None,
                 openai_base_url: Optional[str] = None,
                 openai_model: str = "gpt-4o"):
        """
        Initialize Literature RAG
        
        Args:
            db_path: Path to ChromaDB persistent storage
            embedding_model: HuggingFace embedding model name
            openai_api_key: OpenAI API key for LLM
        """
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.openai_model = openai_model
        self.openai_base_url = openai_base_url
        self.openai_api_key = openai_api_key
        
        # Lazy initialization - only load when actually needed
        self.embeddings = None
        self.vector_store = None
        self.client = None
        
        # OpenAI client can be initialized immediately
        if openai_api_key:
            self.client = OpenAIClient(
                api_key=openai_api_key,
                base_url=openai_base_url
            )
    
    def _ensure_initialized(self):
        """Ensure embeddings and vector store are initialized"""
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma
        
        if self.embeddings is None:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'}
            )
        
        if self.vector_store is None:
            if os.path.exists(self.db_path) and os.listdir(self.db_path):
                self.vector_store = Chroma(
                    persist_directory=self.db_path,
                    embedding_function=self.embeddings
                )
            else:
                self.vector_store = Chroma(
                    persist_directory=self.db_path,
                    embedding_function=self.embeddings
                )
    
    def ingest_pdf(self, pdf_path: str, metadata: Optional[Dict] = None) -> int:
        """
        Ingest a single PDF file into RAG
        
        Args:
            pdf_path: Path to PDF file
            metadata: Additional metadata (title, authors, year, etc.)
        
        Returns:
            Number of chunks ingested
        """
        self._ensure_initialized()
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return 0
        
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Add metadata
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)
        
        doc = documents[0]
        if 'source' not in doc.metadata:
            doc.metadata['source'] = os.path.basename(pdf_path)
        doc.metadata['file_type'] = 'pdf'
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vector_store.add_documents(chunks)
        self.vector_store.persist()
        
        logger.info(f"Ingested {len(chunks)} chunks from {pdf_path}")
        return len(chunks)
    
    def ingest_directory(self, dir_path: str, glob_pattern: str = "*.pdf") -> int:
        """
        Ingest all PDF files in a directory
        
        Args:
            dir_path: Directory containing PDF files
            glob_pattern: File pattern to match
        
        Returns:
            Total number of chunks ingested
        """
        total_chunks = 0
        dir_path = Path(dir_path)
        
        for pdf_file in dir_path.glob(glob_pattern):
            metadata = {
                'filename': pdf_file.name,
                'directory': str(dir_path)
            }
            chunks = self.ingest_pdf(str(pdf_file), metadata)
            total_chunks += chunks
        
        return total_chunks
    
    def search(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        """
        Similarity search for documents
        
        Args:
            query: Search query
            top_k: Number of top results to return
        
        Returns:
            List of retrieved documents
        """
        self._ensure_initialized()
        
        if self.vector_store._collection.count() == 0:
            logger.warning("Vector store is empty, no documents to search")
            return []
        
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        retrieved = []
        for doc, score in results:
            retrieved.append(RetrievedDocument(
                content=doc.page_content,
                metadata=doc.metadata,
                score=score,
                source=doc.metadata.get('source', 'unknown')
            ))
        
        return retrieved
    
    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        End-to-end question answering over RAG
        
        Args:
            question: User question
            top_k: Number of documents to retrieve
        
        Returns:
            Answer with retrieved context
        """
        self._ensure_initialized()
        
        if self.client is None:
            logger.error("LLM not initialized, cannot answer question")
            return {
                'answer': "Error: LLM not configured. Please provide OpenAI API key.",
                'retrieved': self.search(question, top_k)
            }
        
        retrieved = self.search(question, top_k)
        
        # Build context from retrieved documents
        context = "\n\n".join([f"--- Document: {r.source} ---\n{r.content}" for r in retrieved])
        
        # Build prompt
        prompt = f"""Answer the question based on the context provided below.

Question: {question}

Context:
{context}

Answer:"""
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip()
        
        return {
            'answer': answer,
            'retrieved': [
                {
                    'content': r.content,
                    'metadata': r.metadata,
                    'score': r.score,
                    'source': r.source
                } for r in retrieved
            ]
        }
    
    def delete_document(self, source: str) -> bool:
        """Delete a document from vector store by source"""
        self._ensure_initialized()
        
        # Chroma doesn't support direct deletion by metadata easily
        # This is a simplified implementation
        try:
            self.vector_store.delete(filter={'source': source})
            self.vector_store.persist()
            logger.info(f"Deleted document: {source}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG collection"""
        self._ensure_initialized()
        
        return {
            'total_documents': self.vector_store._collection.count(),
            'db_path': self.db_path,
            'embedding_model': self.embedding_model
        }

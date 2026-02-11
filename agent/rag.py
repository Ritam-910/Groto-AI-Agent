import chromadb
from chromadb.utils import embedding_functions
import uuid
from typing import List, Dict, Any

PERSIST_DIRECTORY = "./chroma_db"

class RAGEngine:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_fn
        )

    def ingest(self, text: str, source: str) -> str:
        """
        Ingest text into the vector store.
        Returns the ID of the inserted document.
        """
        doc_id = str(uuid.uuid4())
        chunks = self._chunk_text(text)
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source, "chunk_index": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        return doc_id

    def search(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Search for relevant documents.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        output = []
        if results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results['metadatas'] else {}
                output.append({
                    "content": doc,
                    "source": meta.get("source", "Unknown"),
                    "score": results['distances'][0][i] if results['distances'] else 0
                })
        return output

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Simple text chunking
        """
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks


rag_engine = RAGEngine()

import io
import pypdf
import docx

def process_file_content(file_content: bytes, filename: str) -> str:
    """Extract text from file content based on extension"""
    filename = filename.lower()
    text = ""
    
    try:
        if filename.endswith('.pdf'):
            pdf = pypdf.PdfReader(io.BytesIO(file_content))
            for page in pdf.pages:
                text += page.extract_text() + "\n"
                
        elif filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif filename.endswith('.txt') or filename.endswith('.md'):
            text = file_content.decode('utf-8', errors='ignore')
            
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        return ""
        
    return text

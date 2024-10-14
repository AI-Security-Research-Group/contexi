import os
from typing import List
from langchain_community.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from transformers import AutoTokenizer, AutoModel
from .utils import logger
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

def create_vector_store(documents: List[Document], model_name: str = "sentence-transformers/all-MiniLM-L12-v2", persist_directory: str = "./qdrant_data") -> Qdrant:
    logger.info(f"Creating embeddings using {model_name}")
    
    if not documents:
        logger.error("No documents provided to create_vector_store")
        raise ValueError("No documents provided to create_vector_store")
    
    AutoTokenizer.from_pretrained(model_name, clean_up_tokenization_spaces=True)
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    
    # Get the embedding dimension
    temp_model = AutoModel.from_pretrained(model_name)
    embedding_dimension = temp_model.config.hidden_size
    del temp_model  # Free up memory
    
    # Initialize Qdrant client
    client = QdrantClient(path=persist_directory)
    
    # Check if the collection already exists
    collection_name = "contexi_collection"
    collections = client.get_collections().collections
    if not any(collection.name == collection_name for collection in collections):
        # Create a new collection if it doesn't exist
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=embedding_dimension, distance=Distance.COSINE),
        )
        logger.info(f"Created new Qdrant collection: {collection_name}")
        
        # Create Qdrant vector store and add documents
        vector_store = Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=embeddings,
        )
        vector_store.add_documents(documents)
        logger.info("Added documents to Qdrant vector store")
    else:
        # Load existing vector store
        vector_store = Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=embeddings,
        )
        logger.info(f"Loaded existing Qdrant collection: {collection_name}")
    
    return vector_store
    
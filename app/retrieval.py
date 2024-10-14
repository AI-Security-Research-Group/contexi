from langchain_community.vectorstores import Qdrant
from utils import logger

def setup_retriever(vector_store: Qdrant, k: int = 10):
    logger.info(f"Setting up retriever with k={k}")
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
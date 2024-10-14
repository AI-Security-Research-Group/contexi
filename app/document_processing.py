from typing import List
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.docstore.document import Document
from utils import logger
import yaml
import os

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

def load_documents_files(directory: str) -> List[Document]:
    logger.info(f"Loading files from {directory}")
    loader = DirectoryLoader(
        directory,
        glob=config['file_extension'],
        loader_cls=TextLoader
    )
    documents = loader.load()
    logger.info(f"Loaded {len(documents)} files")
    return documents

def split_documents_into_chunks(documents: List[Document]) -> List[Document]:
    logger.info("Splitting documents into chunks")
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config['chunk_size'],
        chunk_overlap=config['chunk_overlap'],
    )
    split_docs = text_splitter.split_documents(documents)
    logger.info(f"Split documents into {len(split_docs)} chunks")
    return split_docs
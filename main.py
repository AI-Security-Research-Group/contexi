import sys
import os
import tempfile
import git
import shutil
import yaml
from typing import Literal

# Add the current directory and app directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "app")
sys.path.extend([current_dir, app_dir])

from app.document_processing import load_documents_files, split_documents_into_chunks
from app.embedding import create_vector_store
from app.retrieval import setup_retriever
from app.llm import initialize_llm
from app.rag import start_interactive_session, perform_cgrag
from app.utils import logger, get_directory_hash
from app.re_ranking import configure_reranker


def load_config():
    with open('config.yml', 'r') as file:
        return yaml.safe_load(file)

config = load_config()

def ensure_temp_dir_exists():
    temp_dir = os.path.join(current_dir, "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir

def clone_repository(repo_url):
    temp_dir = ensure_temp_dir_exists()
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    clone_dir = os.path.join(temp_dir, repo_name)
    
    # Remove the directory if it already exists
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir)
    
    try:
        git.Repo.clone_from(repo_url, clone_dir)
        return clone_dir
    except git.GitCommandError as e:
        logger.error(f"Git cloning error: {str(e)}")
        raise Exception(f"Failed to clone repository: {str(e)}")

def initialize_contexi(code_path, is_git_repo, chain_type: Literal["smart", "fast"] = "fast"):
    logger.info("Initializing Contexi components")
    logger.info(f"Initializing re-ranker with config: {config.get('reranking', {})}")
    try:
        import importlib
        if importlib.util.find_spec("sentence_transformers") is None:
            logger.info("Installing sentence-transformers...")
            os.system("pip install sentence-transformers")
        
        reranker = configure_reranker(config)                    

        if is_git_repo:
            code_path = clone_repository(code_path)
            logger.info(f"Cloned repository to: {code_path}")
        
        file_documents = load_documents_files(code_path)
        if not file_documents:
            logger.error(f"No document files found in {code_path}")
            raise ValueError(f"No document files found in {code_path}")
        
        split_docs = split_documents_into_chunks(file_documents)
        if not split_docs:
            logger.error("No documents after splitting")
            raise ValueError("No documents after splitting")
        
        vector_store = create_vector_store(split_docs)
        retriever = setup_retriever(vector_store)
        llm = initialize_llm()
        
        return retriever, llm, code_path, chain_type
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        if is_git_repo and os.path.exists(code_path):
            shutil.rmtree(code_path)  # Clean up the temp directory if an error occurs
        raise

def run_interactive_session(code_path, is_git_repo=False, chain_type: Literal["smart", "fast"] = "fast"):
    retriever, llm, final_code_path, _ = initialize_contexi(code_path, is_git_repo, chain_type)
    start_interactive_session(final_code_path, retriever, llm, chain_type)

def run_streamlit_ui():
    os.system("streamlit run app_ui.py")

def run_fastapi():
    os.system("uvicorn app.api:app --host 0.0.0.0 --port 8000")

def main():
    print("Welcome to Contexi!")
    print("Please select a mode to run:")
    print("1. Interactive session")
    print("2. UI")
    print("3. API")

    while True:
        choice = input("Enter your choice (1, 2, or 3): ")
        if choice in ['1', '2', '3']:
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    if choice == '1':
        code_path = input("Enter the path to your document directory or a Git URL: ")
        is_git_repo = code_path.startswith("http://") or code_path.startswith("https://")
        
        chain_type = input("Select LLM Chain Type (smart/fast): ").lower()
        while chain_type not in ["smart", "fast"]:
            chain_type = input("Invalid input. Please enter 'smart' or 'fast': ").lower()
        
        run_interactive_session(code_path, is_git_repo, chain_type)
    elif choice == '2':
        run_streamlit_ui()
    elif choice == '3':
        run_fastapi()

if __name__ == "__main__":
    main()


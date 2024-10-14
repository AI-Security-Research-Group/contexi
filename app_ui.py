import streamlit as st
import sys
import os
from typing import Literal
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from main import initialize_contexi
from rag import perform_cgrag
from utils import logger, load_config

# Load configuration
config = load_config()

def clear_session_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# select LLM chain type smart or fast
def get_chain_type() -> Literal["smart", "fast"]:
    if "chain_type" not in st.session_state:
        st.session_state.chain_type = "fast"  # Default to fast
    return st.session_state.chain_type

#delete vector index function
def delete_vector_index():
    try:
        persist_directory = config.get('vector_store', {}).get('persist_directory', './qdrant_data')
        collection_name = config.get('vector_store', {}).get('collection_name', 'contexi_collection')
        
        client = QdrantClient(path=persist_directory)
        
        # Check if the collection exists
        collections = client.get_collections().collections
        if any(collection.name == collection_name for collection in collections):
            client.delete_collection(collection_name=collection_name)
            st.success(f"Vector index '{collection_name}' has been deleted successfully.")
            logger.info(f"Vector index '{collection_name}' deleted.")
        else:
            st.info(f"No vector index named '{collection_name}' found.")
            logger.info(f"No vector index named '{collection_name}' found for deletion.")
    except Exception as e:
        st.error(f"An error occurred while trying to delete the vector index: {str(e)}")
        logger.error(f"Error during vector index deletion: {str(e)}")

#initalize streamlit ui
def run_streamlit_app():
    logger.debug("Starting Streamlit app")
    st.set_page_config(page_title="Contexi", page_icon="🔍")
    st.title("CONTEXI 💬")

    if st.sidebar.button("Delete Existing Vector Index"):
        delete_vector_index()

    # Sidebar for configuration
    st.sidebar.header("Configuration")
    
    # Radio button for selecting input type
    input_type = st.sidebar.radio("Select input type", ("Local Directory", "Git Repository"))
    
    if input_type == "Local Directory":
        code_path = st.sidebar.text_input("Data Path", "enter/your/data/code/path")
    else:
        code_path = st.sidebar.text_input("Git Repository URL", "https://github.com/username/repo.git")
    
    # LLM Chain Configuration
    st.sidebar.header("LLM Chain Configuration")
    chain_type = st.sidebar.radio(
        "Select LLM Chain Type",
        ("SmartLLM", "Faster"),
        index=0 if get_chain_type() == "smart" else 1,
        help="SmartLLM: Improved results but takes more time. Faster: Generic results with quicker response.",
    )
    st.session_state.chain_type = "smart" if chain_type == "SmartLLM" else "fast"

    # Initialize components
    if st.sidebar.button("Initialize Assistant"):
        logger.debug("Initialize Assistant button clicked")
        clear_session_state()  # Clear the session state before initializing
        st.session_state.chain_type = "smart" if chain_type == "SmartLLM" else "fast"  # Re-initialize chain_type
        try:
            with st.spinner("Initializing... This may take a few minutes."):
                retriever, llm, final_code_path, _ = initialize_contexi(code_path, input_type == "Git Repository", st.session_state.chain_type)
                st.session_state.retriever = retriever
                st.session_state.llm = llm
                st.session_state.current_code_path = final_code_path
                st.session_state.chat_history = []
                st.session_state.assistant_initialized = True
            st.success("Assistant initialized successfully with new data source!")
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            st.error(f"An error occurred during initialization: {str(e)}")
    
    # Chat interface
    st.header("Chat:")
    
    if 'assistant_initialized' not in st.session_state or not st.session_state.assistant_initialized:
        st.warning("Please initialize the assistant first using the sidebar.")
    else:
        st.info(f"Current code path: {st.session_state.current_code_path}")
        user_input = st.text_input("Ask a question about the code:")

        if st.button("Submit"):
            if user_input:
                logger.debug(f"Received user input: {user_input}")
                
                # Add the user's question to the chat history immediately
                st.session_state.chat_history.insert(0, ("Human", user_input))
                
                try:
                    with st.spinner("Analyzing..."):
                        answer, _ = perform_cgrag(user_input, st.session_state.retriever, st.session_state.llm, chain_type=st.session_state.chain_type)
                    logger.debug("Generated answer")
                    
                    # Add the AI's answer to the chat history
                    st.session_state.chat_history.insert(0, ("AI", answer))
                except Exception as e:
                    logger.error(f"Error during question answering: {str(e)}")
                    st.error(f"An error occurred while processing your question: {str(e)}")
                    # Remove the user's question if there was an error
                    st.session_state.chat_history.pop(0)
            else:
                st.warning("Please enter a question before submitting.")

        # Display chat history
        for i in range(0, len(st.session_state.chat_history), 2):
            if i+1 < len(st.session_state.chat_history):
                human_msg = st.session_state.chat_history[i+1][1]
                ai_msg = st.session_state.chat_history[i][1]
                
                st.text_input("You:", value=human_msg, key=f"human_{i}", disabled=True)
                st.markdown(f"**Assistant:** {ai_msg}")
                st.markdown("---")  # Add a separator between conversations

        # Option to clear chat history
        if st.button("Clear Chat History"):
            logger.debug("Clearing chat history")
            st.session_state.chat_history = []
            st.experimental_rerun()

if __name__ == "__main__":
    run_streamlit_app()
    
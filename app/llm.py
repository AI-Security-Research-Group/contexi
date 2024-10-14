from langchain_community.llms import Ollama
from utils import logger
import yaml
import os

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

def initialize_llm(base_url: str = "http://localhost:11434"):
    logger.info(f"Initializing Ollama LLM with model {config['llm']['model']}")
    return Ollama(
        base_url=base_url,
        model=config['llm']['model'],
        num_ctx=config['llm']['num_ctx'],
        temperature=config['llm']['temperature'],
        top_p=config['llm']['top_p']
    )
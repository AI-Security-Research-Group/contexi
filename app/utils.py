import logging
import hashlib
import os
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_directory_hash(directory):
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


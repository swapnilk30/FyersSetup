import yaml
from logzero import logger
import json
import os

def load_config(config_path="Config.yaml"):
    """
    Load the configuration from a YAML file.
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None
    

def save_auth_tokens(auth_code, access_token, file_path='auth_tokens.json'):
    """Save the auth_code and access_token to a JSON file."""
    tokens = {
        "auth_code": auth_code,
        "access_token": access_token
    }
    
    with open(file_path, 'w') as file:
        json.dump(tokens, file, indent=4)
    print(f"Auth tokens saved to {file_path}")


def read_auth_tokens(file_path='auth_tokens.json'):
    """Read the auth_code and access_token from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            tokens = json.load(file)
        return tokens.get('auth_code'), tokens.get('access_token')
    else:
        raise FileNotFoundError(f"File not found: {file_path}")

'''
        # Step 2: Try reading saved auth_code and access_token from file
        try:
            auth_code, access_token = read_auth_tokens()
            print("Auth Code and Access Token loaded from file.")
        except FileNotFoundError:
            print("Auth tokens not found. Proceeding with login process.")
'''

import yaml
from logzero import logger

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
import os
import yaml
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    
        logger.info(f"Successfully loaded configuration from {config_path}")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise


def expand_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    expand environment variables in configuration values
    """
    expanded = {}
    
    for key, value in config.items():
        if isinstance(value, str) and value.startswith('$'):
            env_name = value[1:]  # remove $ prefix
            env_value = os.getenv(env_name)
            if env_value:
                expanded[key] = env_value
                logger.debug(f"Expanded {key} from environment variable {env_name}")
            else:
                logger.warning(f"Environment variable {env_name} not found for key {key}")
                expanded[key] = value
        elif isinstance(value, dict):
            expanded[key] = expand_env_vars(value)
        else:
            expanded[key] = value
    
    return expanded


def validate_config(config: Dict[str, Any], required_fields: list) -> bool:
    missing_fields = []
    
    for field in required_fields:
        if field not in config or not config[field]:
            missing_fields.append(field)
  
    if missing_fields:
        logger.error(f"Missing required configuration fields: {', '.join(missing_fields)}")
        return False
    
    return True

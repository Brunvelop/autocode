"""
Utilities for interacting with OpenRouter API.
"""
import os
import logging
import httpx
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1"

def get_openrouter_api_key() -> Optional[str]:
    """Get OpenRouter API key from environment."""
    return os.getenv("OPENROUTER_API_KEY")

def fetch_openrouter_model_info(model_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metadata for a specific model from OpenRouter API.
    
    Since OpenRouter API /models endpoint returns all models, we fetch the list
    and find the requested model_id.
    
    Args:
        model_id: The ID of the model to look up (e.g. 'openai/gpt-4')
        
    Returns:
        Dict with model metadata or None if not found/error.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not found. Cannot fetch model info.")
        return None

    try:
        # Use sync Client
        with httpx.Client() as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/brunvelop/autocode", # Recommended by OpenRouter
            }
            response = client.get(f"{OPENROUTER_API_URL}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            models_list = data.get("data", [])
            
            # Find the specific model
            for model in models_list:
                if model.get("id") == model_id:
                    return model
            
            logger.warning(f"Model {model_id} not found in OpenRouter list.")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching OpenRouter model info: {e}")
        return None

def fetch_models_info(model_ids: List[str]) -> Dict[str, Any]:
    """
    Fetch metadata for a list of models efficiently.
    
    Args:
        model_ids: List of model IDs to look up
        
    Returns:
        Dict mapping model_id to its metadata.
    """
    api_key = get_openrouter_api_key()
    if not api_key:
        return {}

    try:
        # Use sync Client
        with httpx.Client() as client:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/brunvelop/autocode",
            }
            # We fetch the full list once
            response = client.get(f"{OPENROUTER_API_URL}/models", headers=headers)
            response.raise_for_status()
            
            data = response.json()
            all_models = data.get("data", [])
            
            result = {}
            # Index all models by ID for faster lookup
            models_map = {m.get("id"): m for m in all_models}
            
            for mid in model_ids:
                # Try exact match
                if mid in models_map:
                    result[mid] = models_map[mid]
                    continue
                
                # Try stripping 'openrouter/' prefix (common in this project)
                clean_id = mid.replace('openrouter/', '')
                if clean_id in models_map:
                    result[mid] = models_map[clean_id]
            
            return result
            
    except Exception as e:
        logger.error(f"Error fetching OpenRouter models: {e}")
        return {}

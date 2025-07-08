"""
Prompt templates for OpenCode integration.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


def get_prompts_dir() -> Path:
    """Get the prompts directory path."""
    return Path(__file__).parent


def list_available_prompts() -> List[str]:
    """List all available prompt files."""
    prompts_dir = get_prompts_dir()
    prompt_files = []
    
    for file in prompts_dir.glob("*.md"):
        prompt_files.append(file.stem)
    
    return sorted(prompt_files)


def load_prompt(prompt_name: str) -> Optional[str]:
    """Load a prompt file by name.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        
    Returns:
        Content of the prompt file or None if not found
    """
    prompts_dir = get_prompts_dir()
    prompt_file = prompts_dir / f"{prompt_name}.md"
    
    if not prompt_file.exists():
        return None
    
    try:
        return prompt_file.read_text(encoding='utf-8')
    except Exception:
        return None


def get_prompt_info() -> Dict[str, str]:
    """Get information about all available prompts."""
    prompts_dir = get_prompts_dir()
    prompt_info = {}
    
    for file in prompts_dir.glob("*.md"):
        prompt_name = file.stem
        try:
            content = file.read_text(encoding='utf-8')
            # Extract first line as description
            lines = content.strip().split('\n')
            description = lines[0].strip('#').strip() if lines else "No description"
            prompt_info[prompt_name] = description
        except Exception:
            prompt_info[prompt_name] = "Error reading file"
    
    return prompt_info

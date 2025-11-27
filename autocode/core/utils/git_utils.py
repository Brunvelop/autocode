"""
Utilities for interacting with Git.
"""
import subprocess
import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

from autocode.interfaces.registry import register_function
from autocode.interfaces.models import GenericOutput

logger = logging.getLogger(__name__)

class GitNode(BaseModel):
    """Node representing a file or directory in the git tree."""
    name: str = Field(description="Name of the file or directory")
    type: Literal["file", "directory"] = Field(description="Type of the node")
    children: Optional[List['GitNode']] = Field(default=None, description="List of children nodes if directory")

class GitTreeOutput(GenericOutput):
    """Specific output for git tree structure."""
    result: Optional[GitNode] = Field(default=None, description="Root node of the git tree")

@register_function(http_methods=["GET"])
def get_git_tree() -> GitTreeOutput:
    """
    Retrieves the project structure from git index.
    
    Returns:
        GitTreeOutput containing the file tree structure.
    """
    try:
        # Get all files tracked by git
        # -r: recursive
        # --name-only: show only filenames
        cmd = ["git", "ls-tree", "-r", "HEAD", "--name-only"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        files = result.stdout.strip().split('\n')
        files = [f for f in files if f] # Filter empty strings
        
        # Build tree structure
        # We use a dict initially for easy construction, then convert to GitNode
        tree_dict = {
            "name": "root",
            "type": "directory",
            "children": []
        }
        
        for file_path in files:
            parts = file_path.split('/')
            current_level = tree_dict["children"]
            
            for i, part in enumerate(parts):
                is_file = (i == len(parts) - 1)
                
                # Check if this part already exists in current level
                existing_node = next((node for node in current_level if node["name"] == part), None)
                
                if existing_node:
                    if not is_file:
                        current_level = existing_node["children"]
                else:
                    new_node = {
                        "name": part,
                        "type": "file" if is_file else "directory"
                    }
                    if not is_file:
                        new_node["children"] = []
                    
                    current_level.append(new_node)
                    
                    if not is_file:
                        current_level = new_node["children"]
        
        # Convert dict to Pydantic model
        root_node = GitNode(**tree_dict)
                        
        return GitTreeOutput(
            success=True,
            result=root_node,
            message="Git tree retrieved successfully"
        )
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Git error: {e.stderr.strip() if e.stderr else str(e)}"
        logger.error(error_msg)
        return GitTreeOutput(
            success=False,
            result=None,
            message=error_msg
        )
    except Exception as e:
        error_msg = f"Unexpected error retrieving git tree: {str(e)}"
        logger.error(error_msg)
        return GitTreeOutput(
            success=False,
            result=None,
            message=error_msg
        )

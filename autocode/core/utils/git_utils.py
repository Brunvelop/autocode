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
    size: Optional[int] = Field(default=0, description="Size in bytes (files only)")
    children: Optional[List['GitNode']] = Field(default=None, description="List of children nodes if directory")

class GitTreeOutput(GenericOutput):
    """Specific output for git tree structure."""
    result: Optional[GitNode] = Field(default=None, description="Root node of the git tree")

@register_function(http_methods=["GET"])
def get_git_tree() -> GitTreeOutput:
    """
    Retrieves the project structure from git index including file sizes.
    
    Returns:
        GitTreeOutput containing the file tree structure.
    """
    try:
        # Get all files tracked by git
        # -r: recursive
        # -l: long format (shows size)
        # HEAD: current commit
        cmd = ["git", "ls-tree", "-r", "-l", "HEAD"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        lines = [line for line in lines if line] # Filter empty strings
        
        # Build tree structure
        tree_dict = {
            "name": "root",
            "type": "directory",
            "children": [],
            "size": 0
        }
        
        for line in lines:
            try:
                # Format: "100644 blob <sha> <size_padded>\t<path>"
                # Split by tab to separate metadata from path (handles spaces in path)
                if '\t' in line:
                    metadata, file_path = line.split('\t', 1)
                else:
                    # Fallback for weird output, splitting by spaces
                    parts = line.split()
                    file_path = parts[-1]
                    metadata = " ".join(parts[:-1])

                meta_parts = metadata.split()
                # 4th element is size (after mode, type, sha)
                # It might be "-" for some objects, treat as 0
                size_str = meta_parts[3] if len(meta_parts) > 3 else "0"
                size = int(size_str) if size_str.isdigit() else 0
                
                parts = file_path.split('/')
                current_level = tree_dict["children"]
                
                for i, part in enumerate(parts):
                    is_file = (i == len(parts) - 1)
                    
                    # Check if this part already exists in current level
                    existing_node = next((node for node in current_level if node["name"] == part), None)
                    
                    if existing_node:
                        if not is_file:
                            current_level = existing_node["children"]
                            # Accumulate directory size logic could be placed here if we wanted
                            # but usually visualization calculates it.
                    else:
                        new_node = {
                            "name": part,
                            "type": "file" if is_file else "directory",
                            "size": size if is_file else 0
                        }
                        if not is_file:
                            new_node["children"] = []
                        
                        current_level.append(new_node)
                        
                        if not is_file:
                            current_level = new_node["children"]
            except Exception as loop_e:
                logger.warning(f"Error parsing line '{line}': {loop_e}")
                continue
        
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

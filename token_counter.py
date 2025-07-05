"""
Token counter for LLM analysis.
Provides functionality to count tokens in text and files for various LLM models.
"""

import tiktoken
from pathlib import Path
from typing import Dict, Optional


class TokenCounter:
    """Token counter for LLM models using tiktoken."""
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize with specific model encoding.
        
        Args:
            model: LLM model name for encoding (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        self.model = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens_in_text(self, text: str) -> int:
        """Count tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if not text:
            return 0
        
        try:
            return len(self.encoding.encode(text))
        except Exception:
            return 0
    
    def count_tokens_in_file(self, file_path: Path) -> int:
        """Count tokens in a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of tokens in the file
        """
        if not file_path.exists():
            return 0
        
        try:
            content = file_path.read_text(encoding='utf-8')
            return self.count_tokens_in_text(content)
        except Exception:
            return 0
    
    def get_token_statistics(self, file_path: Path) -> Dict:
        """Get detailed token statistics for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with token statistics
        """
        token_count = self.count_tokens_in_file(file_path)
        
        # Get file size
        file_size_bytes = 0
        if file_path.exists():
            try:
                file_size_bytes = file_path.stat().st_size
            except Exception:
                pass
        
        return {
            "file_path": str(file_path),
            "token_count": token_count,
            "model": self.model,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_bytes / (1024 * 1024),
            "tokens_per_kb": token_count / (file_size_bytes / 1024) if file_size_bytes > 0 else 0
        }
    
    def estimate_cost(self, token_count: int, input_cost_per_1k: float = 0.03, output_cost_per_1k: float = 0.06) -> Dict:
        """Estimate cost for token count based on typical pricing.
        
        Args:
            token_count: Number of tokens
            input_cost_per_1k: Cost per 1000 input tokens (default: GPT-4 pricing)
            output_cost_per_1k: Cost per 1000 output tokens (default: GPT-4 pricing)
            
        Returns:
            Dictionary with cost estimates
        """
        input_cost = (token_count / 1000) * input_cost_per_1k
        output_cost = (token_count / 1000) * output_cost_per_1k
        
        return {
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "token_count": token_count,
            "cost_per_1k_input": input_cost_per_1k,
            "cost_per_1k_output": output_cost_per_1k
        }
    
    def check_threshold(self, token_count: int, threshold: int = 50000) -> Dict:
        """Check if token count exceeds a threshold.
        
        Args:
            token_count: Number of tokens
            threshold: Token threshold
            
        Returns:
            Dictionary with threshold check results
        """
        exceeds_threshold = token_count > threshold
        percentage = (token_count / threshold) * 100 if threshold > 0 else 0
        
        return {
            "token_count": token_count,
            "threshold": threshold,
            "exceeds_threshold": exceeds_threshold,
            "percentage": percentage,
            "tokens_over": max(0, token_count - threshold),
            "tokens_remaining": max(0, threshold - token_count)
        }


def count_tokens_in_multiple_files(file_paths: list[Path], model: str = "gpt-4") -> Dict:
    """Count tokens in multiple files.
    
    Args:
        file_paths: List of file paths
        model: LLM model name for encoding
        
    Returns:
        Dictionary with aggregated token statistics
    """
    token_counter = TokenCounter(model)
    
    total_tokens = 0
    file_stats = []
    
    for file_path in file_paths:
        stats = token_counter.get_token_statistics(file_path)
        file_stats.append(stats)
        total_tokens += stats["token_count"]
    
    return {
        "total_tokens": total_tokens,
        "file_count": len(file_paths),
        "model": model,
        "file_statistics": file_stats,
        "average_tokens_per_file": total_tokens / len(file_paths) if file_paths else 0
    }

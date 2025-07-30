"""
Core configuration types for autocode modules.
These types define the domain configuration without external dependencies.
"""

from pydantic import BaseModel, Field
from typing import List


class DocsConfig(BaseModel):
    """Configuration for documentation checking module."""
    enabled: bool = True
    directories: List[str] = Field(default_factory=lambda: ["autocode/"])
    file_extensions: List[str] = Field(default_factory=lambda: [".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx"])
    exclude: List[str] = Field(default_factory=lambda: ["__pycache__/", "*.pyc", "__init__.py"])
    docs_directory: str = "docs"


class TestConfig(BaseModel):
    """Configuration for test checking module."""
    enabled: bool = True
    directories: List[str] = Field(default_factory=lambda: ["autocode/"])
    exclude: List[str] = Field(default_factory=lambda: ["__pycache__/", "*.pyc", "__init__.py"])
    test_frameworks: List[str] = Field(default_factory=lambda: ["pytest"])
    auto_execute: bool = True


class GitConfig(BaseModel):
    """Configuration for git analysis module."""
    enabled: bool = True
    exclude_paths: List[str] = Field(default_factory=lambda: [".git/", "__pycache__/", "*.pyc"])
    max_diff_size: int = Field(default=10000, description="Maximum diff size in characters")
    include_staged: bool = True
    include_unstaged: bool = True


class OpenCodeConfig(BaseModel):
    """Configuration for OpenCode integration."""
    enabled: bool = True
    model: str = "claude-4-sonnet"
    max_tokens: int = 64000
    debug: bool = True
    config_path: str = ".opencode.json"
    quiet_mode: bool = True
    json_output: bool = True


class CodeToDesignConfig(BaseModel):
    """Configuration for code-to-design transformation."""
    enabled: bool = True
    output_dir: str = "design"
    language: str = "python"  # Kept for backward compatibility
    languages: List[str] = Field(default_factory=lambda: ["python", "javascript", "html", "css"])
    diagrams: List[str] = Field(default_factory=lambda: ["classes", "components"])
    directories: List[str] = Field(default_factory=lambda: ["autocode/"])


class TokenConfig(BaseModel):
    """Configuration for token counting and alerts."""
    enabled: bool = True
    threshold: int = 50000
    model: str = "gpt-4"


class CheckConfig(BaseModel):
    """Configuration for a daemon check."""
    enabled: bool = True
    interval_minutes: int = 5


class DaemonConfig(BaseModel):
    """Configuration for the daemon."""
    doc_check: CheckConfig = Field(default_factory=lambda: CheckConfig(enabled=True, interval_minutes=10))
    git_check: CheckConfig = Field(default_factory=lambda: CheckConfig(enabled=True, interval_minutes=5))
    test_check: CheckConfig = Field(default_factory=lambda: CheckConfig(enabled=True, interval_minutes=5))
    token_alerts: TokenConfig = Field(default_factory=TokenConfig)


class ApiConfig(BaseModel):
    """Configuration for the API."""
    port: int = 8080
    host: str = "127.0.0.1"


class DocIndexConfig(BaseModel):
    """Configuration for documentation indexing."""
    enabled: bool = True
    output_path: str = ".clinerules/docs_index.json"
    auto_generate: bool = True
    update_on_docs_change: bool = True


class AutocodeConfig(BaseModel):
    """Complete configuration for autocode system."""
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    opencode: OpenCodeConfig = Field(default_factory=OpenCodeConfig)
    doc_index: DocIndexConfig = Field(default_factory=DocIndexConfig)
    docs: DocsConfig = Field(default_factory=DocsConfig)
    tests: TestConfig = Field(default_factory=TestConfig)
    code_to_design: CodeToDesignConfig = Field(default_factory=CodeToDesignConfig)

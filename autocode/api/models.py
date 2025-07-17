"""
Pydantic models for the autocode API.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CheckResult(BaseModel):
    """Result of a check execution."""
    check_name: str
    status: str  # 'success', 'warning', 'error'
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    duration_seconds: Optional[float] = None


class DaemonStatus(BaseModel):
    """Status of the daemon."""
    is_running: bool
    uptime_seconds: Optional[float] = None
    last_check_run: Optional[datetime] = None
    total_checks_run: int = 0


class CheckConfig(BaseModel):
    """Configuration for a check."""
    enabled: bool = True
    interval_minutes: int = 5


class TokenConfig(BaseModel):
    """Configuration for token counting and alerts."""
    enabled: bool = True
    threshold: int = 50000  # 50k tokens by default
    model: str = "gpt-4"    # Model for encoding


class DaemonConfig(BaseModel):
    """Configuration for the daemon."""
    doc_check: CheckConfig = CheckConfig(enabled=True, interval_minutes=10)
    git_check: CheckConfig = CheckConfig(enabled=True, interval_minutes=5)
    test_check: CheckConfig = CheckConfig(enabled=True, interval_minutes=5)
    token_alerts: TokenConfig = TokenConfig()


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


class DocsConfig(BaseModel):
    """Configuration for documentation checking."""
    enabled: bool = True
    directories: List[str] = ["vidi/", "autocode/"]
    file_extensions: List[str] = [".py", ".js", ".html", ".css", ".ts", ".jsx", ".tsx"]
    exclude: List[str] = ["__pycache__/", "*.pyc", "__init__.py"]


class TestConfig(BaseModel):
    """Configuration for test checking."""
    enabled: bool = True
    directories: List[str] = ["vidi/", "autocode/", "tools/"]
    exclude: List[str] = ["__pycache__/", "*.pyc", "__init__.py"]
    test_frameworks: List[str] = ["pytest"]
    auto_execute: bool = True


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
    languages: List[str] = ["python", "javascript", "html", "css"]  # New multi-language support
    diagrams: List[str] = ["classes", "components"]  # Support both diagram types
    directories: List[str] = ["autocode/"]


class AutocodeConfig(BaseModel):
    """Complete configuration for autocode daemon."""
    daemon: DaemonConfig = DaemonConfig()
    api: ApiConfig = ApiConfig()
    opencode: OpenCodeConfig = OpenCodeConfig()
    doc_index: DocIndexConfig = DocIndexConfig()
    docs: DocsConfig = DocsConfig()
    tests: TestConfig = TestConfig()
    code_to_design: CodeToDesignConfig = CodeToDesignConfig()


class StatusResponse(BaseModel):
    """Response for the status endpoint."""
    daemon: DaemonStatus
    checks: Dict[str, CheckResult]
    config: AutocodeConfig


class CheckExecutionRequest(BaseModel):
    """Request to execute a specific check."""
    check_name: str
    force: bool = False


class CheckExecutionResponse(BaseModel):
    """Response from executing a check."""
    success: bool
    result: Optional[CheckResult] = None
    error: Optional[str] = None

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


class DaemonConfig(BaseModel):
    """Configuration for the daemon."""
    doc_check: CheckConfig = CheckConfig(enabled=True, interval_minutes=10)
    git_check: CheckConfig = CheckConfig(enabled=True, interval_minutes=5)


class ApiConfig(BaseModel):
    """Configuration for the API."""
    port: int = 8080
    host: str = "127.0.0.1"


class AutocodeConfig(BaseModel):
    """Complete configuration for autocode daemon."""
    daemon: DaemonConfig = DaemonConfig()
    api: ApiConfig = ApiConfig()


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

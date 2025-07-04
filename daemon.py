"""
Autocode daemon for continuous monitoring.
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .doc_checker import DocChecker
from .git_analyzer import GitAnalyzer
from .scheduler import Scheduler
from .models import CheckResult, DaemonStatus, AutocodeConfig


class AutocodeDaemon:
    """Daemon that runs periodic checks using existing DocChecker and GitAnalyzer."""
    
    def __init__(self, project_root: Path = None, config: AutocodeConfig = None):
        """Initialize the daemon.
        
        Args:
            project_root: Project root directory
            config: Daemon configuration
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or AutocodeConfig()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.doc_checker = DocChecker(self.project_root)
        self.git_analyzer = GitAnalyzer(self.project_root)
        self.scheduler = Scheduler()
        
        # State
        self.start_time = None
        self.total_checks_run = 0
        self.results: Dict[str, CheckResult] = {}
        
        # Setup tasks
        self._setup_tasks()
    
    def _setup_tasks(self):
        """Setup scheduled tasks."""
        # Add doc check task
        if self.config.daemon.doc_check.enabled:
            self.scheduler.add_task(
                name="doc_check",
                func=self.run_doc_check,
                interval_seconds=self.config.daemon.doc_check.interval_minutes * 60,
                enabled=True
            )
        
        # Add git check task
        if self.config.daemon.git_check.enabled:
            self.scheduler.add_task(
                name="git_check",
                func=self.run_git_check,
                interval_seconds=self.config.daemon.git_check.interval_minutes * 60,
                enabled=True
            )
    
    def run_doc_check(self) -> CheckResult:
        """Run documentation check using existing DocChecker."""
        start_time = time.time()
        
        try:
            self.logger.info("Running documentation check")
            
            # Use existing DocChecker
            outdated_docs = self.doc_checker.get_outdated_docs()
            
            if not outdated_docs:
                result = CheckResult(
                    check_name="doc_check",
                    status="success",
                    message="✅ All documentation is up to date!",
                    details={"outdated_count": 0, "files": []},
                    timestamp=datetime.now(),
                    duration_seconds=time.time() - start_time
                )
            else:
                # Format the same way as CLI
                formatted_output = self.doc_checker.format_results(outdated_docs)
                
                result = CheckResult(
                    check_name="doc_check",
                    status="warning",
                    message=f"⚠️  {len(outdated_docs)} documents need attention",
                    details={
                        "outdated_count": len(outdated_docs),
                        "files": [
                            {
                                "code_file": str(doc.code_file.relative_to(self.project_root)),
                                "doc_file": str(doc.doc_file.relative_to(self.project_root)),
                                "status": doc.status,
                                "doc_type": doc.doc_type
                            } for doc in outdated_docs
                        ],
                        "formatted_output": formatted_output
                    },
                    timestamp=datetime.now(),
                    duration_seconds=time.time() - start_time
                )
            
            self.results["doc_check"] = result
            self.total_checks_run += 1
            
            self.logger.info(f"Doc check completed: {result.status} - {result.message}")
            return result
            
        except Exception as e:
            self.logger.error(f"Doc check failed: {e}")
            result = CheckResult(
                check_name="doc_check",
                status="error",
                message=f"❌ Error running documentation check: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                duration_seconds=time.time() - start_time
            )
            self.results["doc_check"] = result
            self.total_checks_run += 1
            return result
    
    def run_git_check(self) -> CheckResult:
        """Run git analysis using existing GitAnalyzer."""
        start_time = time.time()
        
        try:
            self.logger.info("Running git analysis")
            
            # Use existing GitAnalyzer
            changes_data = self.git_analyzer.analyze_changes()
            
            status = changes_data["repository_status"]
            total_files = status["total_files"]
            
            if total_files == 0:
                result = CheckResult(
                    check_name="git_check",
                    status="success",
                    message="✅ No changes detected",
                    details=changes_data,
                    timestamp=datetime.now(),
                    duration_seconds=time.time() - start_time
                )
            else:
                result = CheckResult(
                    check_name="git_check",
                    status="warning",
                    message=f"📊 {total_files} files changed (M:{status['modified']} A:{status['added']} D:{status['deleted']})",
                    details=changes_data,
                    timestamp=datetime.now(),
                    duration_seconds=time.time() - start_time
                )
            
            self.results["git_check"] = result
            self.total_checks_run += 1
            
            self.logger.info(f"Git check completed: {result.status} - {result.message}")
            return result
            
        except Exception as e:
            self.logger.error(f"Git check failed: {e}")
            result = CheckResult(
                check_name="git_check",
                status="error",
                message=f"❌ Error running git analysis: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                duration_seconds=time.time() - start_time
            )
            self.results["git_check"] = result
            self.total_checks_run += 1
            return result
    
    def run_check_manually(self, check_name: str) -> CheckResult:
        """Run a specific check manually.
        
        Args:
            check_name: Name of the check to run
            
        Returns:
            CheckResult object
        """
        if check_name == "doc_check":
            return self.run_doc_check()
        elif check_name == "git_check":
            return self.run_git_check()
        else:
            raise ValueError(f"Unknown check: {check_name}")
    
    def get_daemon_status(self) -> DaemonStatus:
        """Get current daemon status."""
        uptime = None
        if self.start_time:
            uptime = time.time() - self.start_time
        
        last_check_run = None
        if self.results:
            last_check_run = max(result.timestamp for result in self.results.values())
        
        return DaemonStatus(
            is_running=self.scheduler.is_running(),
            uptime_seconds=uptime,
            last_check_run=last_check_run,
            total_checks_run=self.total_checks_run
        )
    
    def get_all_results(self) -> Dict[str, CheckResult]:
        """Get all check results."""
        return self.results.copy()
    
    def update_config(self, config: AutocodeConfig):
        """Update daemon configuration."""
        self.config = config
        
        # Update scheduler tasks
        if "doc_check" in self.scheduler.tasks:
            self.scheduler.update_task_interval(
                "doc_check",
                config.daemon.doc_check.interval_minutes * 60
            )
            if config.daemon.doc_check.enabled:
                self.scheduler.enable_task("doc_check")
            else:
                self.scheduler.disable_task("doc_check")
        
        if "git_check" in self.scheduler.tasks:
            self.scheduler.update_task_interval(
                "git_check",
                config.daemon.git_check.interval_minutes * 60
            )
            if config.daemon.git_check.enabled:
                self.scheduler.enable_task("git_check")
            else:
                self.scheduler.disable_task("git_check")
    
    async def start(self):
        """Start the daemon."""
        self.logger.info("Starting autocode daemon")
        self.start_time = time.time()
        
        # Run initial checks
        self.logger.info("Running initial checks")
        self.run_doc_check()
        self.run_git_check()
        
        # Start scheduler
        await self.scheduler.start()
    
    def stop(self):
        """Stop the daemon."""
        self.logger.info("Stopping autocode daemon")
        self.scheduler.stop()
        self.start_time = None
    
    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self.scheduler.is_running()

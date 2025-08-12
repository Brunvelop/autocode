"""
Simple scheduler for periodic task execution.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.next_run is None:
            self.next_run = datetime.now() + timedelta(seconds=self.interval_seconds)


class Scheduler:
    """Simple scheduler for periodic tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        self._stop_event = asyncio.Event()
    
    def add_task(self, name: str, func: Callable, interval_seconds: int, enabled: bool = True):
        """Add a task to the scheduler.
        
        Args:
            name: Task name
            func: Function to execute
            interval_seconds: Interval between executions
            enabled: Whether task is enabled
        """
        task = ScheduledTask(
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            enabled=enabled
        )
        self.tasks[name] = task
        self.logger.info(f"Added task '{name}' with {interval_seconds}s interval")
    
    def remove_task(self, name: str):
        """Remove a task from the scheduler."""
        if name in self.tasks:
            del self.tasks[name]
            self.logger.info(f"Removed task '{name}'")
    
    def enable_task(self, name: str):
        """Enable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = True
            self.logger.info(f"Enabled task '{name}'")
    
    def disable_task(self, name: str):
        """Disable a task."""
        if name in self.tasks:
            self.tasks[name].enabled = False
            self.logger.info(f"Disabled task '{name}'")
    
    def update_task_interval(self, name: str, interval_seconds: int):
        """Update task interval."""
        if name in self.tasks:
            task = self.tasks[name]
            task.interval_seconds = interval_seconds
            # Update next run time
            if task.last_run:
                task.next_run = task.last_run + timedelta(seconds=interval_seconds)
            else:
                task.next_run = datetime.now() + timedelta(seconds=interval_seconds)
            self.logger.info(f"Updated task '{name}' interval to {interval_seconds}s")
    
    def get_task_status(self, name: str) -> Optional[Dict]:
        """Get status of a specific task."""
        if name not in self.tasks:
            return None
        
        task = self.tasks[name]
        return {
            "name": task.name,
            "enabled": task.enabled,
            "interval_seconds": task.interval_seconds,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "seconds_until_next": (task.next_run - datetime.now()).total_seconds() if task.next_run else None
        }
    
    def get_all_tasks_status(self) -> Dict[str, Dict]:
        """Get status of all tasks."""
        return {name: self.get_task_status(name) for name in self.tasks}
    
    async def run_task(self, task: ScheduledTask):
        """Execute a single task."""
        try:
            self.logger.info(f"Running task '{task.name}'")
            start_time = datetime.now()
            
            # Execute the task (handle both sync and async functions)
            if asyncio.iscoroutinefunction(task.func):
                await task.func()
            else:
                task.func()
            
            # Update task timing
            task.last_run = start_time
            task.next_run = start_time + timedelta(seconds=task.interval_seconds)
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Task '{task.name}' completed in {duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error running task '{task.name}': {e}")
            # Still update next run time even if task failed
            task.last_run = datetime.now()
            task.next_run = task.last_run + timedelta(seconds=task.interval_seconds)
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.running = True
        self.logger.info("Starting scheduler")
        
        try:
            while self.running:
                current_time = datetime.now()
                
                # Check which tasks need to run
                tasks_to_run = []
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    if task.next_run and current_time >= task.next_run:
                        tasks_to_run.append(task)
                
                # Run tasks concurrently
                if tasks_to_run:
                    await asyncio.gather(*[self.run_task(task) for task in tasks_to_run])
                
                # Sleep for a short interval before checking again
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=1.0)
                    break  # Stop event was set
                except asyncio.TimeoutError:
                    pass  # Continue the loop
                
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
        finally:
            self.running = False
            self.logger.info("Scheduler stopped")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.logger.info("Stopping scheduler")
        self._stop_event.set()
        self.running = False
    
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.running

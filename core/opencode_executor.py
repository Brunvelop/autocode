"""
OpenCode execution module for autocode.
"""

import json
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from ..prompts import load_prompt, list_available_prompts, get_prompt_info


class OpenCodeExecutor:
    """Executor for running OpenCode in headless mode."""
    
    def __init__(self, project_root: Path, config_file: Optional[Path] = None):
        """Initialize OpenCode executor.
        
        Args:
            project_root: Root directory of the project
            config_file: Path to configuration file (autocode_config.yml)
        """
        self.project_root = project_root
        self.config_file = config_file or project_root / "autocode_config.yml"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('opencode', self._get_default_config())
        except Exception as e:
            print(f"⚠️  Warning: Could not load config from {self.config_file}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default OpenCode configuration."""
        return {
            'enabled': True,
            'model': 'claude-4-sonnet',
            'max_tokens': 64000,
            'debug': False,
            'config_path': '.opencode.json',
            'quiet_mode': True,
            'json_output': False,
            'timeout': 300,
            'retry_attempts': 3
        }
    
    def is_opencode_available(self) -> bool:
        """Check if OpenCode is available in the system."""
        try:
            result = subprocess.run(
                ['opencode', '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def list_prompts(self) -> List[str]:
        """List all available prompt files."""
        return list_available_prompts()
    
    def get_prompts_info(self) -> Dict[str, str]:
        """Get information about available prompts."""
        return get_prompt_info()
    
    def execute_opencode(
        self,
        prompt: str,
        *,
        debug: Optional[bool] = None,
        json_output: Optional[bool] = None,
        quiet: Optional[bool] = None,
        cwd: Optional[Path] = None
    ) -> Tuple[int, str, str]:
        """Execute OpenCode with the given prompt.
        
        Args:
            prompt: The prompt to send to OpenCode
            debug: Enable debug mode (overrides config)
            json_output: Enable JSON output (overrides config)
            quiet: Enable quiet mode (overrides config)
            cwd: Working directory for OpenCode execution
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        if not self.config.get('enabled', True):
            return 1, "", "OpenCode is disabled in configuration"
        
        if not self.is_opencode_available():
            return 1, "", "OpenCode is not available. Please install it first."
        
        # Build command
        cmd = ['opencode']
        
        # Add prompt
        cmd.extend(['-p', prompt])
        
        # Add configuration options
        if quiet if quiet is not None else self.config.get('quiet_mode', True):
            cmd.append('-q')
        
        if json_output if json_output is not None else self.config.get('json_output', False):
            cmd.extend(['-f', 'json'])
        
        if debug if debug is not None else self.config.get('debug', False):
            cmd.append('-d')
        
        # Set working directory
        execution_cwd = cwd or self.project_root
        if execution_cwd != Path.cwd():
            cmd.extend(['-c', str(execution_cwd)])
        
        try:
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.get('timeout', 300),
                cwd=str(execution_cwd)
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return 1, "", f"OpenCode execution timed out after {self.config.get('timeout', 300)} seconds"
        except Exception as e:
            return 1, "", f"Error executing OpenCode: {str(e)}"
    
    def execute_with_prompt_file(
        self,
        prompt_name: str,
        **kwargs
    ) -> Tuple[int, str, str]:
        """Execute OpenCode with a prompt loaded from file.
        
        Args:
            prompt_name: Name of the prompt file (without .md extension)
            **kwargs: Additional arguments for execute_opencode
            
        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        prompt_content = load_prompt(prompt_name)
        if prompt_content is None:
            available_prompts = self.list_prompts()
            error_msg = f"Prompt '{prompt_name}' not found. Available prompts: {', '.join(available_prompts)}"
            return 1, "", error_msg
        
        return self.execute_opencode(prompt_content, **kwargs)
    
    def format_output(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        json_output: bool = False,
        verbose: bool = False
    ) -> str:
        """Format the output for display.
        
        Args:
            exit_code: Exit code from OpenCode
            stdout: Standard output from OpenCode
            stderr: Standard error from OpenCode
            json_output: Whether to format as JSON
            verbose: Whether to show verbose information
            
        Returns:
            Formatted output string
        """
        if json_output:
            return self._format_json_output(exit_code, stdout, stderr)
        else:
            return self._format_text_output(exit_code, stdout, stderr, verbose)
    
    def _format_json_output(self, exit_code: int, stdout: str, stderr: str) -> str:
        """Format output as JSON."""
        output_data = {
            'exit_code': exit_code,
            'success': exit_code == 0,
            'stdout': stdout,
            'stderr': stderr,
            'timestamp': self._get_timestamp()
        }
        
        # Try to parse stdout as JSON if it looks like JSON
        if stdout.strip().startswith('{') and stdout.strip().endswith('}'):
            try:
                parsed_stdout = json.loads(stdout)
                output_data['parsed_response'] = parsed_stdout
            except json.JSONDecodeError:
                pass
        
        return json.dumps(output_data, indent=2)
    
    def _format_text_output(self, exit_code: int, stdout: str, stderr: str, verbose: bool) -> str:
        """Format output as human-readable text."""
        output_lines = []
        
        if exit_code == 0:
            output_lines.append("🤖 OpenCode Analysis Complete")
            output_lines.append("=" * 50)
            
            if stdout.strip():
                output_lines.append(stdout.strip())
            
            if verbose and stderr.strip():
                output_lines.append("\n📋 Debug Information:")
                output_lines.append("-" * 30)
                output_lines.append(stderr.strip())
                
        else:
            output_lines.append("❌ OpenCode Analysis Failed")
            output_lines.append("=" * 50)
            
            if stderr.strip():
                output_lines.append(f"Error: {stderr.strip()}")
            
            if stdout.strip():
                output_lines.append(f"Output: {stdout.strip()}")
        
        return "\n".join(output_lines)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def validate_opencode_setup(project_root: Path) -> Tuple[bool, str]:
    """Validate that OpenCode is properly set up.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    executor = OpenCodeExecutor(project_root)
    
    # Check if OpenCode is available
    if not executor.is_opencode_available():
        return False, "OpenCode is not installed or not available in PATH"
    
    # Check if configuration is valid
    if not executor.config.get('enabled', True):
        return False, "OpenCode is disabled in configuration"
    
    # Check if .opencode.json exists
    opencode_config = project_root / executor.config.get('config_path', '.opencode.json')
    if not opencode_config.exists():
        return False, f"OpenCode configuration file not found: {opencode_config}"
    
    return True, "OpenCode setup is valid"

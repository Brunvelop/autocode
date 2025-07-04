"""
CLI interface for autocode tools.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .doc_checker import DocChecker
from .git_analyzer import GitAnalyzer


def check_docs_command(args) -> int:
    """Handle check-docs command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Initialize checker
    checker = DocChecker(project_root)
    
    # Check for outdated documentation
    outdated_results = checker.get_outdated_docs()
    
    # Format and display results
    output = checker.format_results(outdated_results)
    print(output)
    
    # Return appropriate exit code
    return 1 if outdated_results else 0


def git_changes_command(args) -> int:
    """Handle git-changes command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Initialize git analyzer  
    analyzer = GitAnalyzer(project_root)
    
    try:
        # Determine output file
        if args.output:
            output_file = Path(args.output)
        else:
            output_file = project_root / "git_changes.json"
        
        # Analyze changes and save to file
        changes_data = analyzer.save_changes_to_file(output_file)
        
        # Display summary to user
        status = changes_data["repository_status"]
        modified_files = changes_data["modified_files"]
        
        print(f"📊 Repository Status:")
        print(f"   Total files changed: {status['total_files']}")
        print(f"   Modified: {status['modified']}")
        print(f"   Added: {status['added']}")
        print(f"   Deleted: {status['deleted']}")
        print(f"   Untracked: {status['untracked']}")
        if status['renamed'] > 0:
            print(f"   Renamed: {status['renamed']}")
        
        print(f"\n📄 Modified Files:")
        for file_path in modified_files:
            print(f"   - {file_path}")
        
        print(f"\n💾 Detailed changes saved to: {output_file}")
        
        # Show verbose output if requested
        if args.verbose:
            print(f"\n📋 Detailed Changes:")
            for change in changes_data["changes"]:
                status_indicator = "🟢" if change["staged"] else "🔴"
                print(f"   {status_indicator} {change['file']} ({change['status']})")
                print(f"      +{change['additions']} -{change['deletions']}")
                if change["diff"] and len(change["diff"]) < 500:
                    print(f"      {change['diff'][:200]}...")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error analyzing git changes: {e}")
        return 1


def daemon_command(args) -> int:
    """Handle daemon command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        import uvicorn
        from .api import app
        
        print("🚀 Starting Autocode Monitoring Daemon")
        print(f"   📡 API Server: http://{args.host}:{args.port}")
        print(f"   🌐 Web Interface: http://{args.host}:{args.port}")
        print("   📊 Dashboard will auto-refresh every 5 seconds")
        print("   🔄 Checks run automatically per configuration")
        print("\n   Press Ctrl+C to stop the daemon")
        print("-" * 50)
        
        # Run the FastAPI application with uvicorn
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info" if args.verbose else "warning",
            access_log=args.verbose
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Daemon stopped by user")
        return 0
    except ImportError as e:
        print(f"❌ Error: Missing dependency for daemon mode: {e}")
        print("   Please ensure FastAPI and uvicorn are installed")
        return 1
    except Exception as e:
        print(f"❌ Error starting daemon: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="autocode",
        description="Automated code quality and development tools"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    
    # check-docs subcommand
    check_docs_parser = subparsers.add_parser(
        "check-docs",
        help="Check if documentation is up to date"
    )
    
    # git-changes subcommand
    git_changes_parser = subparsers.add_parser(
        "git-changes", 
        help="Analyze git changes for commit message generation"
    )
    git_changes_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path (default: git_changes.json)"
    )
    git_changes_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed diff information"
    )
    
    # daemon subcommand
    daemon_parser = subparsers.add_parser(
        "daemon",
        help="Start the autocode monitoring daemon with web interface"
    )
    daemon_parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    daemon_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to (default: 8080)"
    )
    daemon_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command specified, default to check-docs for backwards compatibility
    if not args.command:
        args.command = "check-docs"
    
    # Route to appropriate command handler
    if args.command == "check-docs":
        exit_code = check_docs_command(args)
    elif args.command == "git-changes":
        exit_code = git_changes_command(args)
    elif args.command == "daemon":
        exit_code = daemon_command(args)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

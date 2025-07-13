"""
CLI interface for autocode tools.
"""

import argparse
import json
import sys
import yaml
import warnings
from pathlib import Path
from typing import Optional

from .core.docs import DocChecker, DocIndexer
from .core.test import TestChecker
from .core.git import GitAnalyzer
from .core.ai import OpenCodeExecutor, validate_opencode_setup
from .core.design import CodeToDesign
from .api.models import AutocodeConfig


def find_config_file(start_path: Path) -> Optional[Path]:
    """Find autocode_config.yml by searching up the directory tree.
    
    Args:
        start_path: Starting directory to search from
        
    Returns:
        Path to autocode_config.yml if found, None otherwise
    """
    current = start_path.resolve()
    while current != current.parent:  # Until we reach filesystem root
        config_file = current / "autocode_config.yml"
        if config_file.exists():
            return config_file
        current = current.parent
    return None


def load_config(working_dir: Path = None) -> AutocodeConfig:
    """Load configuration from autocode_config.yml.
    
    Searches up the directory tree starting from working_dir (or cwd) 
    until it finds autocode_config.yml.
    
    Args:
        working_dir: Directory to start search from (defaults to cwd)
        
    Returns:
        Loaded configuration with defaults
    """
    if working_dir is None:
        working_dir = Path.cwd()
    
    config_file = find_config_file(working_dir)
    
    if config_file is None:
        # Return default configuration if file doesn't exist
        return AutocodeConfig()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not config_data:
            return AutocodeConfig()
        
        # Check for deprecated 'language' field (Mejora 5)
        if config_data and 'code_to_design' in config_data and 'language' in config_data['code_to_design']:
            warnings.warn("⚠️  Campo 'language' está deprecado en code_to_design. Usa 'languages' como lista en su lugar.", 
                         DeprecationWarning, stacklevel=2)
        
        # Parse configuration with Pydantic
        return AutocodeConfig(**config_data)
        
    except Exception as e:
        print(f"⚠️  Warning: Error loading config from {config_file}: {e}")
        print("   Using default configuration")
        return AutocodeConfig()


def check_docs_command(args) -> int:
    """Handle check-docs command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Load configuration (searches up directory tree)
    config = load_config()
    
    # Initialize checker with configuration
    checker = DocChecker(project_root, config.docs)
    
    # Check for outdated documentation
    outdated_results = checker.get_outdated_docs()
    
    # Format and display results
    output = checker.format_results(outdated_results)
    print(output)
    
    # Generate documentation index if docs are up to date and config allows it
    if not outdated_results and config.doc_index.enabled and config.doc_index.auto_generate:
        try:
            # Initialize doc indexer with CLI override if provided
            indexer = DocIndexer(project_root, config.doc_index, args.doc_index_output)
            
            # Generate the index
            index_path = indexer.generate_index()
            
            # Show success message
            relative_path = index_path.relative_to(project_root)
            print(f"📋 Documentation index generated: {relative_path}")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate documentation index: {e}")
            # Don't fail the command for index generation issues
    
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
        from .api.server import app
        
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


def opencode_command(args) -> int:
    """Handle opencode command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    try:
        # Initialize OpenCode executor
        executor = OpenCodeExecutor(project_root)
        
        # Validate OpenCode setup if requested
        if args.validate:
            is_valid, message = validate_opencode_setup(project_root)
            if is_valid:
                print(f"✅ {message}")
                return 0
            else:
                print(f"❌ {message}")
                return 1
        
        # List available prompts if requested
        if args.list_prompts:
            prompts_info = executor.get_prompts_info()
            if prompts_info:
                print("📋 Available Prompts:")
                for prompt_name, description in prompts_info.items():
                    print(f"   • {prompt_name}: {description}")
            else:
                print("❌ No prompts found")
            return 0
        
        # Execute OpenCode
        if args.prompt_file:
            # Load prompt from file
            exit_code, stdout, stderr = executor.execute_with_prompt_file(
                args.prompt_file,
                debug=args.debug,
                json_output=args.json,
                quiet=args.quiet,
                cwd=Path(args.cwd) if args.cwd else None
            )
        elif args.prompt:
            # Use direct prompt
            exit_code, stdout, stderr = executor.execute_opencode(
                args.prompt,
                debug=args.debug,
                json_output=args.json,
                quiet=args.quiet,
                cwd=Path(args.cwd) if args.cwd else None
            )
        else:
            print("❌ Error: Either --prompt or --prompt-file must be specified")
            return 1
        
        # Format and display output
        formatted_output = executor.format_output(
            exit_code, stdout, stderr, 
            json_output=args.json, 
            verbose=args.verbose
        )
        print(formatted_output)
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Error executing OpenCode: {e}")
        return 1


def check_tests_command(args) -> int:
    """Handle check-tests command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for issues found)
    """
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Load configuration (searches up directory tree)
    config = load_config()
    
    # Initialize test checker with configuration
    checker = TestChecker(project_root, config.tests)
    
    # Check for missing/failing tests
    test_issues = checker.get_missing_and_failing_tests()
    
    # Format and display results
    output = checker.format_results(test_issues)
    print(output)
    
    # Return appropriate exit code
    return 1 if test_issues else 0


def code_to_design_command(args) -> int:
    """Handle code-to-design command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        project_root = Path.cwd()
        config = load_config()  # Use existing load_config
        
        # Convert CodeToDesignConfig to dict for CodeToDesign
        if hasattr(config, 'code_to_design'):
            config_dict = {
                "output_dir": config.code_to_design.output_dir,
                # Handle both old 'language' and new 'languages' format
                "languages": getattr(config.code_to_design, 'languages', [getattr(config.code_to_design, 'language', 'python')]),
                "diagrams": config.code_to_design.diagrams
            }
        else:
            config_dict = {
                "output_dir": "design",
                "languages": ["python"],
                "diagrams": ["classes"]
            }
        
        # Mejora 1: CLI Overrides - Apply CLI arguments
        if args.languages:
            config_dict["languages"] = args.languages
        if args.diagrams:
            config_dict["diagrams"] = args.diagrams
        if args.output_dir:
            config_dict["output_dir"] = args.output_dir
        
        # Mejora 2: Validación Temprana
        try:
            from .core.design.analyzers.analyzer_factory import AnalyzerFactory
            from .core.design.generators.generator_factory import GeneratorFactory
            
            temp_analyzer_factory = AnalyzerFactory(project_root)
            temp_generator_factory = GeneratorFactory({})
            
            available_languages = temp_analyzer_factory.get_available_analyzers()
            available_diagrams = temp_generator_factory.get_available_generators()
            
            # Validate languages
            for lang in config_dict.get("languages", []):
                if lang not in available_languages:
                    warnings.warn(f"⚠️  Lenguaje '{lang}' no soportado. Disponibles: {available_languages}. Ignorando.")
                    config_dict["languages"] = [l for l in config_dict["languages"] if l in available_languages]
            
            # Validate diagrams  
            for diag in config_dict.get("diagrams", []):
                if diag not in available_diagrams:
                    warnings.warn(f"⚠️  Diagrama '{diag}' no soportado. Disponibles: {available_diagrams}. Ignorando.")
                    config_dict["diagrams"] = [d for d in config_dict["diagrams"] if d in available_diagrams]
            
            # Ensure we have at least some valid options
            if not config_dict["languages"]:
                config_dict["languages"] = ["python"]  # Fallback
            if not config_dict["diagrams"]:
                config_dict["diagrams"] = ["classes"]  # Fallback
                
        except ImportError as e:
            warnings.warn(f"⚠️  No se pudo validar configuración: {e}")
        
        # Mejora 4: Soporte Multi-Directorio - Determine directories to process  
        if args.directories:
            directories = args.directories
        elif args.directory:
            directories = [args.directory]
        elif hasattr(config, 'code_to_design') and config.code_to_design.directories:
            directories = config.code_to_design.directories
        else:
            directories = ["autocode/"]  # Default fallback
        
        # Mejora 3: Show Config - Display configuration if requested
        if args.show_config:
            print("📋 Configuración Cargada/Normalizada:")
            config_display = {
                "directories": directories,
                "languages": config_dict["languages"],
                "diagrams": config_dict["diagrams"],
                "output_dir": config_dict["output_dir"],
                "pattern": args.pattern if hasattr(args, 'pattern') else "*.py"
            }
            print(yaml.dump(config_display, default_flow_style=False, allow_unicode=True))
            print("-" * 50)
        
        # Initialize CodeToDesign
        transformer = CodeToDesign(
            project_root=project_root,
            config=config_dict
        )
        
        # Process each directory
        all_results = []
        for directory in directories:
            print(f"🔍 Analyzing directory: {directory}")
            
            # Generate design for this directory
            patterns = [args.pattern] if args.pattern else None
            result = transformer.generate_design(
                directory=directory,
                patterns=patterns
            )
            
            all_results.append(result)
            
            if result['status'] == 'success':
                print(f"✅ Design generation successful for {directory}")
                if 'metrics' in result and 'total_items' in result['metrics']:
                    print(f"   Items found: {result['metrics']['total_items']}")
                if result.get('message'):
                    print(f"   {result['message']}")
                print("   Generated files:")
                for file_path in result['generated_files']:
                    print(f"     - {file_path}")
            elif result['status'] == 'warning':
                print(f"⚠️  Design generation completed with warnings for {directory}")
                if result.get('message'):
                    print(f"   {result['message']}")
                print("   Generated files:")
                for file_path in result['generated_files']:
                    print(f"     - {file_path}")
            else:
                print(f"❌ Design generation failed for {directory}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
        
        # Check overall success
        successful_results = [r for r in all_results if r['status'] in ['success', 'warning']]
        if successful_results:
            total_files = sum(len(r['generated_files']) for r in successful_results)
            print(f"\n🎉 Overall: {len(successful_results)}/{len(all_results)} directories processed successfully")
            print(f"   Total files generated: {total_files}")
            return 0
        else:
            print(f"\n❌ Overall: All directories failed")
            return 1
            
    except Exception as e:
        print(f"❌ Error generating design: {e}")
        return 1


def count_tokens_command(args) -> int:
    """Handle count-tokens command.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for errors)
    """
    try:
        from .core.ai import TokenCounter, count_tokens_in_multiple_files
        
        project_root = Path.cwd()
        
        # Initialize token counter with specified model
        token_counter = TokenCounter(args.model)
        
        if args.file:
            # Count tokens in a single file
            file_path = project_root / args.file
            if not file_path.exists():
                print(f"❌ File not found: {args.file}")
                return 1
            
            stats = token_counter.get_token_statistics(file_path)
            
            print(f"📊 Token Analysis for {args.file}:")
            print(f"   Tokens: {stats['token_count']:,}")
            print(f"   Model: {stats['model']}")
            print(f"   File size: {stats['file_size_mb']:.2f} MB")
            print(f"   Tokens per KB: {stats['tokens_per_kb']:.1f}")
            
            # Check threshold if provided
            if args.threshold:
                threshold_check = token_counter.check_threshold(stats['token_count'], args.threshold)
                if threshold_check['exceeds_threshold']:
                    print(f"⚠️  WARNING: Exceeds threshold of {args.threshold:,} tokens")
                    print(f"   Over by: {threshold_check['tokens_over']:,} tokens")
                else:
                    print(f"✅ Within threshold of {args.threshold:,} tokens")
                    print(f"   Remaining: {threshold_check['tokens_remaining']:,} tokens")
            
        elif args.directory:
            # Count tokens in multiple files
            directory_path = project_root / args.directory
            if not directory_path.exists():
                print(f"❌ Directory not found: {args.directory}")
                return 1
            
            # Find files matching pattern
            pattern = args.pattern or "*"
            file_paths = list(directory_path.rglob(pattern))
            
            if not file_paths:
                print(f"❌ No files found matching pattern '{pattern}' in {args.directory}")
                return 1
            
            # Count tokens in all files
            results = count_tokens_in_multiple_files(file_paths, args.model)
            
            print(f"📊 Token Analysis for {args.directory} (pattern: {pattern}):")
            print(f"   Total files: {results['file_count']}")
            print(f"   Total tokens: {results['total_tokens']:,}")
            print(f"   Average per file: {results['average_tokens_per_file']:.0f}")
            print(f"   Model: {results['model']}")
            
            # Show individual files if verbose
            if args.verbose:
                print(f"\n📋 Individual Files:")
                for file_stat in results['file_statistics']:
                    if file_stat['token_count'] > 0:
                        rel_path = Path(file_stat['file_path']).relative_to(project_root)
                        print(f"   {rel_path}: {file_stat['token_count']:,} tokens")
            
            # Check threshold if provided
            if args.threshold:
                threshold_check = token_counter.check_threshold(results['total_tokens'], args.threshold)
                if threshold_check['exceeds_threshold']:
                    print(f"⚠️  WARNING: Total exceeds threshold of {args.threshold:,} tokens")
                    print(f"   Over by: {threshold_check['tokens_over']:,} tokens")
                else:
                    print(f"✅ Total within threshold of {args.threshold:,} tokens")
                    print(f"   Remaining: {threshold_check['tokens_remaining']:,} tokens")
        
        else:
            print("❌ Error: Either --file or --directory must be specified")
            return 1
        
        return 0
        
    except ImportError:
        print("❌ Error: tiktoken not installed. Run 'uv add tiktoken' to install.")
        return 1
    except Exception as e:
        print(f"❌ Error counting tokens: {e}")
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
    check_docs_parser.add_argument(
        "--doc-index-output",
        type=str,
        help="Override output path for documentation index"
    )
    
    # check-tests subcommand
    check_tests_parser = subparsers.add_parser(
        "check-tests",
        help="Check if tests exist and are passing"
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
    
    # opencode subcommand
    opencode_parser = subparsers.add_parser(
        "opencode",
        help="Execute OpenCode AI analysis with prompts"
    )
    
    # Main options - either prompt or prompt-file is required
    prompt_group = opencode_parser.add_mutually_exclusive_group()
    prompt_group.add_argument(
        "--prompt", "-p",
        type=str,
        help="Direct prompt to send to OpenCode"
    )
    prompt_group.add_argument(
        "--prompt-file", "-f",
        type=str,
        help="Load prompt from internal file (e.g., 'code-review')"
    )
    
    # Utility options
    opencode_parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="List all available internal prompts"
    )
    opencode_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate OpenCode setup and configuration"
    )
    
    # Execution options
    opencode_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (overrides config)"
    )
    opencode_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    opencode_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Enable quiet mode (overrides config)"
    )
    opencode_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including debug info"
    )
    opencode_parser.add_argument(
        "--cwd",
        type=str,
        help="Working directory for OpenCode execution (default: current directory)"
    )
    
    # code-to-design subcommand
    code_to_design_parser = subparsers.add_parser(
        "code-to-design",
        help="Generate design diagrams from code"
    )
    code_to_design_parser.add_argument(
        "--directory", "-d",
        type=str,
        help="Directory to analyze (defaults to directories in config)"
    )
    code_to_design_parser.add_argument(
        "--pattern", "-p",
        type=str,
        default="*.py",
        help="File pattern to match (default: *.py)"
    )
    code_to_design_parser.add_argument(
        "--output-dir", "-o",
        type=str,
        help="Output directory for generated designs (default: design/)"
    )
    # Mejora 1: Más Overrides CLI
    code_to_design_parser.add_argument(
        "--languages", "-l",
        type=str,
        nargs="+",
        help="Lenguajes a analizar (e.g., python js). Sobrescribe config."
    )
    code_to_design_parser.add_argument(
        "--diagrams", "-g",
        type=str,
        nargs="+",
        help="Tipos de diagramas (e.g., classes components). Sobrescribe config."
    )
    # Mejora 3: Modo Verbose/Info
    code_to_design_parser.add_argument(
        "--show-config",
        action="store_true",
        help="Mostrar configuración cargada/normalizada antes de ejecutar."
    )
    # Mejora 4: Soporte Multi-Directorio
    code_to_design_parser.add_argument(
        "--directories",
        type=str,
        nargs="+",
        help="Directorios a analizar (e.g., autocode/ src/). Sobrescribe config."
    )

    # count-tokens subcommand
    count_tokens_parser = subparsers.add_parser(
        "count-tokens",
        help="Count tokens in files for LLM analysis"
    )
    
    # File or directory options (mutually exclusive)
    file_group = count_tokens_parser.add_mutually_exclusive_group(required=True)
    file_group.add_argument(
        "--file", "-f",
        type=str,
        help="Count tokens in a specific file"
    )
    file_group.add_argument(
        "--directory", "-d",
        type=str,
        help="Count tokens in all files in a directory"
    )
    
    # Additional options
    count_tokens_parser.add_argument(
        "--pattern", "-p",
        type=str,
        default="*",
        help="File pattern to match when using --directory (default: *)"
    )
    count_tokens_parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4",
        help="LLM model for token encoding (default: gpt-4)"
    )
    count_tokens_parser.add_argument(
        "--threshold", "-t",
        type=int,
        help="Token threshold for warnings"
    )
    count_tokens_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed per-file information"
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
    elif args.command == "check-tests":
        exit_code = check_tests_command(args)
    elif args.command == "git-changes":
        exit_code = git_changes_command(args)
    elif args.command == "daemon":
        exit_code = daemon_command(args)
    elif args.command == "opencode":
        exit_code = opencode_command(args)
    elif args.command == "code-to-design":
        exit_code = code_to_design_command(args)
    elif args.command == "count-tokens":
        exit_code = count_tokens_command(args)
    else:
        parser.print_help()
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

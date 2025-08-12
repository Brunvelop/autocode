"""
CLI interface for autocode tools.
"""

import json
import sys
import yaml
import warnings
import typer
from pathlib import Path
from typing import Optional, List

from .core.docs import DocIndexer, check_documentation, format_cli_output, has_documentation_issues
from .core.test import TestChecker
from .core.git import GitAnalyzer
from .core.ai import OpenCodeExecutor, validate_opencode_setup
from .core.design import CodeToDesign
from .core.config import load_config, AutocodeConfig

# Create Typer app
app = typer.Typer(help="Automated code quality and development tools")


@app.command("check-docs")
def check_docs(
    doc_index_output: Optional[str] = typer.Option(None, "--doc-index-output", help="Override output path for documentation index")
) -> int:
    """Check if documentation is up to date"""
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Load configuration using the unified config system
    config = load_config()
    
    # Check documentation using new functional API
    result = check_documentation(project_root, config.docs)
    
    # Format and display results using new formatter
    output = format_cli_output(result)
    print(output)
    
    # Check if there are documentation issues
    has_issues = has_documentation_issues(result)
    
    # Generate documentation index if docs are up to date and config allows it
    if not has_issues and config.doc_index.enabled and config.doc_index.auto_generate:
        try:
            # Initialize doc indexer with CLI override if provided
            indexer = DocIndexer(project_root, config.doc_index, doc_index_output)
            
            # Generate the index
            index_path = indexer.generate_index()
            
            # Show success message
            relative_path = index_path.relative_to(project_root)
            print(f"📋 Documentation index generated: {relative_path}")
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate documentation index: {e}")
            # Don't fail the command for index generation issues
    
    # Return appropriate exit code
    return 1 if has_issues else 0


@app.command("check-tests")
def check_tests() -> int:
    """Check if tests exist and are passing"""
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


@app.command("git-changes")
def git_changes(
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output JSON file path (default: git_changes.json)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed diff information")
) -> int:
    """Analyze git changes for commit message generation"""
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    # Initialize git analyzer  
    analyzer = GitAnalyzer(project_root)
    
    try:
        # Determine output file
        if output:
            output_file = Path(output)
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
        if verbose:
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


@app.command("daemon")
def daemon(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to (default: 127.0.0.1)"),
    port: int = typer.Option(8080, "--port", help="Port to bind to (default: 8080)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging")
) -> int:
    """Start the autocode monitoring daemon with web interface"""
    try:
        import uvicorn
        from .api.server import app
        
        print("🚀 Starting Autocode Monitoring Daemon")
        print(f"   📡 API Server: http://{host}:{port}")
        print(f"   🌐 Web Interface: http://{host}:{port}")
        print("   📊 Dashboard will auto-refresh every 5 seconds")
        print("   🔄 Checks run automatically per configuration")
        print("\n   Press Ctrl+C to stop the daemon")
        print("-" * 50)
        
        # Run the FastAPI application with uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if verbose else "warning",
            access_log=verbose
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


@app.command("opencode")
def opencode(
    prompt: Optional[str] = typer.Option(None, "-p", "--prompt", help="Direct prompt to send to OpenCode"),
    prompt_file: Optional[str] = typer.Option(None, "-f", "--prompt-file", help="Load prompt from internal file (e.g., 'code-review')"),
    list_prompts: bool = typer.Option(False, "--list-prompts", help="List all available internal prompts"),
    validate: bool = typer.Option(False, "--validate", help="Validate OpenCode setup and configuration"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode (overrides config)"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    quiet: bool = typer.Option(False, "--quiet", help="Enable quiet mode (overrides config)"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed output including debug info"),
    cwd: Optional[str] = typer.Option(None, "--cwd", help="Working directory for OpenCode execution (default: current directory)")
) -> int:
    """Execute OpenCode AI analysis with prompts"""
    # Validate mutually exclusive arguments
    if prompt and prompt_file:
        typer.echo("Error: --prompt and --prompt-file are mutually exclusive", err=True)
        raise typer.Exit(1)
    
    # Get project root (current working directory)
    project_root = Path.cwd()
    
    try:
        # Initialize OpenCode executor
        executor = OpenCodeExecutor(project_root)
        
        # Validate OpenCode setup if requested
        if validate:
            is_valid, message = validate_opencode_setup(project_root)
            if is_valid:
                print(f"✅ {message}")
                return 0
            else:
                print(f"❌ {message}")
                return 1
        
        # List available prompts if requested
        if list_prompts:
            prompts_info = executor.get_prompts_info()
            if prompts_info:
                print("📋 Available Prompts:")
                for prompt_name, description in prompts_info.items():
                    print(f"   • {prompt_name}: {description}")
            else:
                print("❌ No prompts found")
            return 0
        
        # Execute OpenCode
        if prompt_file:
            # Load prompt from file
            exit_code, stdout, stderr = executor.execute_with_prompt_file(
                prompt_file,
                debug=debug,
                json_output=json_output,
                quiet=quiet,
                cwd=Path(cwd) if cwd else None
            )
        elif prompt:
            # Use direct prompt
            exit_code, stdout, stderr = executor.execute_opencode(
                prompt,
                debug=debug,
                json_output=json_output,
                quiet=quiet,
                cwd=Path(cwd) if cwd else None
            )
        else:
            print("❌ Error: Either --prompt or --prompt-file must be specified")
            return 1
        
        # Format and display output
        formatted_output = executor.format_output(
            exit_code, stdout, stderr, 
            json_output=json_output, 
            verbose=verbose
        )
        print(formatted_output)
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Error executing OpenCode: {e}")
        return 1


@app.command("code-to-design")
def code_to_design(
    directory: Optional[str] = typer.Option(None, "-d", "--directory", help="Directory to analyze (defaults to directories in config)"),
    pattern: str = typer.Option("*.py", "-p", "--pattern", help="File pattern to match (default: *.py)"),
    output_dir: Optional[str] = typer.Option(None, "-o", "--output-dir", help="Output directory for generated designs (default: design/)"),
    languages: Optional[List[str]] = typer.Option(None, "-l", "--languages", help="Languages to analyze (e.g., python js). Overrides config."),
    diagrams: Optional[List[str]] = typer.Option(None, "-g", "--diagrams", help="Diagram types (e.g., classes components). Overrides config."),
    show_config: bool = typer.Option(False, "--show-config", help="Show loaded/normalized configuration before executing."),
    directories: Optional[List[str]] = typer.Option(None, "--directories", help="Directories to analyze (e.g., autocode/ src/). Overrides config.")
) -> int:
    """Generate design diagrams from code"""
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
        if languages:
            config_dict["languages"] = languages
        if diagrams:
            config_dict["diagrams"] = diagrams
        if output_dir:
            config_dict["output_dir"] = output_dir
        
        # Mejora 2: Validación Temprana
        try:
            from .core.design.analyzers.analyzer_factory import AnalyzerFactory
            from .core.design.diagrams.generator_factory import GeneratorFactory
            
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
        if directories:
            dirs_to_process = directories
        elif directory:
            dirs_to_process = [directory]
        elif hasattr(config, 'code_to_design') and config.code_to_design.directories:
            dirs_to_process = config.code_to_design.directories
        else:
            dirs_to_process = ["autocode/"]  # Default fallback
        
        # Mejora 3: Show Config - Display configuration if requested
        if show_config:
            print("📋 Configuración Cargada/Normalizada:")
            config_display = {
                "directories": dirs_to_process,
                "languages": config_dict["languages"],
                "diagrams": config_dict["diagrams"],
                "output_dir": config_dict["output_dir"],
                "pattern": pattern
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
        for dir_path in dirs_to_process:
            print(f"🔍 Analyzing directory: {dir_path}")
            
            # Generate design for this directory
            patterns = [pattern] if pattern else None
            result = transformer.generate_design(
                directory=dir_path,
                patterns=patterns
            )
            
            all_results.append(result)
            
            if result['status'] == 'success':
                print(f"✅ Design generation successful for {dir_path}")
                if 'metrics' in result and 'total_items' in result['metrics']:
                    print(f"   Items found: {result['metrics']['total_items']}")
                if result.get('message'):
                    print(f"   {result['message']}")
                print("   Generated files:")
                for file_path in result['generated_files']:
                    print(f"     - {file_path}")
            elif result['status'] == 'warning':
                print(f"⚠️  Design generation completed with warnings for {dir_path}")
                if result.get('message'):
                    print(f"   {result['message']}")
                print("   Generated files:")
                for file_path in result['generated_files']:
                    print(f"     - {file_path}")
            else:
                print(f"❌ Design generation failed for {dir_path}")
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


@app.command("count-tokens")
def count_tokens(
    file: Optional[str] = typer.Option(None, "-f", "--file", help="Count tokens in a specific file"),
    directory: Optional[str] = typer.Option(None, "-d", "--directory", help="Count tokens in all files in a directory"),
    pattern: str = typer.Option("*", "-p", "--pattern", help="File pattern to match when using --directory (default: *)"),
    model: str = typer.Option("gpt-4", "-m", "--model", help="LLM model for token encoding (default: gpt-4)"),
    threshold: Optional[int] = typer.Option(None, "-t", "--threshold", help="Token threshold for warnings"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed per-file information")
) -> int:
    """Count tokens in files for LLM analysis"""
    # Validate mutually exclusive arguments
    if not file and not directory:
        typer.echo("Error: Either --file or --directory must be specified", err=True)
        raise typer.Exit(1)
    
    if file and directory:
        typer.echo("Error: --file and --directory are mutually exclusive", err=True)
        raise typer.Exit(1)
    
    try:
        from .core.ai import TokenCounter, count_tokens_in_multiple_files
        
        project_root = Path.cwd()
        
        # Initialize token counter with specified model
        token_counter = TokenCounter(model)
        
        if file:
            # Count tokens in a single file
            file_path = project_root / file
            if not file_path.exists():
                print(f"❌ File not found: {file}")
                return 1
            
            stats = token_counter.get_token_statistics(file_path)
            
            print(f"📊 Token Analysis for {file}:")
            print(f"   Tokens: {stats['token_count']:,}")
            print(f"   Model: {stats['model']}")
            print(f"   File size: {stats['file_size_mb']:.2f} MB")
            print(f"   Tokens per KB: {stats['tokens_per_kb']:.1f}")
            
            # Check threshold if provided
            if threshold:
                threshold_check = token_counter.check_threshold(stats['token_count'], threshold)
                if threshold_check['exceeds_threshold']:
                    print(f"⚠️  WARNING: Exceeds threshold of {threshold:,} tokens")
                    print(f"   Over by: {threshold_check['tokens_over']:,} tokens")
                else:
                    print(f"✅ Within threshold of {threshold:,} tokens")
                    print(f"   Remaining: {threshold_check['tokens_remaining']:,} tokens")
            
        elif directory:
            # Count tokens in multiple files
            directory_path = project_root / directory
            if not directory_path.exists():
                print(f"❌ Directory not found: {directory}")
                return 1
            
            # Find files matching pattern
            file_paths = list(directory_path.rglob(pattern))
            
            if not file_paths:
                print(f"❌ No files found matching pattern '{pattern}' in {directory}")
                return 1
            
            # Count tokens in all files
            results = count_tokens_in_multiple_files(file_paths, model)
            
            print(f"📊 Token Analysis for {directory} (pattern: {pattern}):")
            print(f"   Total files: {results['file_count']}")
            print(f"   Total tokens: {results['total_tokens']:,}")
            print(f"   Average per file: {results['average_tokens_per_file']:.0f}")
            print(f"   Model: {results['model']}")
            
            # Show individual files if verbose
            if verbose:
                print(f"\n📋 Individual Files:")
                for file_stat in results['file_statistics']:
                    if file_stat['token_count'] > 0:
                        rel_path = Path(file_stat['file_path']).relative_to(project_root)
                        print(f"   {rel_path}: {file_stat['token_count']:,} tokens")
            
            # Check threshold if provided
            if threshold:
                threshold_check = token_counter.check_threshold(results['total_tokens'], threshold)
                if threshold_check['exceeds_threshold']:
                    print(f"⚠️  WARNING: Total exceeds threshold of {threshold:,} tokens")
                    print(f"   Over by: {threshold_check['tokens_over']:,} tokens")
                else:
                    print(f"✅ Total within threshold of {threshold:,} tokens")
                    print(f"   Remaining: {threshold_check['tokens_remaining']:,} tokens")
        
        return 0
        
    except ImportError:
        print("❌ Error: tiktoken not installed. Run 'uv add tiktoken' to install.")
        return 1
    except Exception as e:
        print(f"❌ Error counting tokens: {e}")
        return 1


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()

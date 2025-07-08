#!/usr/bin/env python3
"""
Basic usage example for autocode.

This example shows how to use autocode programmatically.
"""

from pathlib import Path
from autocode.core.doc_checker import DocChecker
from autocode.core.git_analyzer import GitAnalyzer


def main():
    """Demonstrate basic autocode functionality."""
    print("🚀 Autocode Basic Usage Example")
    print("=" * 40)
    
    # Get current project root
    project_root = Path.cwd()
    print(f"📁 Project root: {project_root}")
    
    # Example 1: Check documentation
    print("\n📋 1. Checking documentation...")
    try:
        doc_checker = DocChecker(project_root)
        outdated_docs = doc_checker.get_outdated_docs()
        
        if outdated_docs:
            print(f"⚠️  Found {len(outdated_docs)} outdated documentation files:")
            for doc_path, code_path, doc_time, code_time in outdated_docs:
                print(f"   - {doc_path} (outdated)")
        else:
            print("✅ All documentation is up to date!")
            
    except Exception as e:
        print(f"❌ Error checking documentation: {e}")
    
    # Example 2: Analyze git changes
    print("\n🔍 2. Analyzing git changes...")
    try:
        git_analyzer = GitAnalyzer(project_root)
        
        # Get status summary
        status = git_analyzer.get_repository_status()
        print(f"📊 Repository status:")
        print(f"   Total files changed: {status['total_files']}")
        print(f"   Modified: {status['modified']}")
        print(f"   Added: {status['added']}")
        print(f"   Deleted: {status['deleted']}")
        
        if status['total_files'] > 0:
            # Get modified files
            modified_files = git_analyzer.get_modified_files()
            print(f"\n📄 Modified files:")
            for file_path in modified_files[:5]:  # Show first 5
                print(f"   - {file_path}")
            if len(modified_files) > 5:
                print(f"   ... and {len(modified_files) - 5} more")
        
    except Exception as e:
        print(f"❌ Error analyzing git changes: {e}")
    
    print("\n✨ Example completed!")
    print("\n💡 To run more examples:")
    print("   autocode check-docs")
    print("   autocode git-changes --verbose")
    print("   autocode daemon")


if __name__ == "__main__":
    main()

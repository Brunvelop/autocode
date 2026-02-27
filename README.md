# Autocode - Automated Development Tools

Automated code quality and development tools with AI integration, featuring continuous monitoring and web interface.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Quality](https://img.shields.io/badge/code%20quality-autocode-brightgreen.svg)](https://github.com/brunvelop/autocode)

## 🚀 Features

### CLI Tools
- **📋 Documentation Check**: Verify documentation is up-to-date with code changes
- **🔍 Git Analysis**: Analyze git changes for commit message generation  
- **🧪 Test Checker**: Validate test coverage and identify missing tests
- **🤖 OpenCode Integration**: AI-powered code analysis and generation
- **📊 Token Counter**: Count LLM tokens for cost estimation

### Continuous Monitoring
- **⚡ Real-time Dashboard**: Clean web interface to view check results
- **🔄 Automatic Checks**: Periodic execution of quality checks
- **📈 Live Updates**: Dashboard auto-refreshes every 5 seconds
- **🎛️ Manual Controls**: Run checks on-demand via web interface
- **⚙️ Configurable**: Adjust intervals and enable/disable checks

## 📦 Installation

### Prerequisites
Autocode uses [uv](https://github.com/astral-sh/uv) for dependency management. Install it first:

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Install via pip
pip install uv
```

### 🔧 Development Installation
For development and contribution:

```bash
# 1. Clone the repository
git clone https://github.com/brunvelop/autocode.git
cd autocode

# 2. Install dependencies and setup environment
uv sync

# 3. Verify installation
uv run autocode --help

# 4. Run tests (optional)
uv run pytest tests/

# 5. Start development server
uv run autocode daemon
```

### 🚀 Production Installation
For using Autocode in your projects:

```bash
# Clone and install
git clone https://github.com/brunvelop/autocode.git
cd autocode
uv sync

# Or with pip (alternative)
pip install -e .
```

### 📋 Installation Verification
After installation, verify everything works:

```bash
# Check CLI access
uv run autocode --help

# Test basic functionality
uv run autocode check-docs
uv run autocode git-changes

# Start web dashboard
uv run autocode daemon
# Then open: http://127.0.0.1:8080
```

### 🔮 Future PyPI Installation
Once published, it will be available as:
```bash
uv add autocode
# or: pip install autocode
```

## 🏃 Quick Start

### CLI Usage
```bash
# Check documentation status
uv run autocode check-docs

# Analyze git changes
uv run autocode git-changes --verbose

# Check test coverage
uv run autocode check-tests

# Count tokens in files
uv run autocode count-tokens --directory src --model gpt-4

# AI-powered code analysis with OpenCode
uv run autocode opencode --prompt "Analyze code quality and suggest improvements"
```

### Web Dashboard
```bash
# Start monitoring daemon
uv run autocode daemon

# Open browser to http://127.0.0.1:8080
# View real-time status and run checks manually
```

## 🛠️ Configuration

Create `autocode_config.yml` in your project root:

```yaml
# Daemon configuration
daemon:
  doc_check:
    enabled: true
    interval_minutes: 1
  git_check:
    enabled: true
    interval_minutes: 1
  test_check:
    enabled: true
    interval_minutes: 5
  auto_update:
    enabled: false
    trigger_on_docs: true
    trigger_on_git: true
    interval_minutes: 15

# API server settings
api:
  port: 8080
  host: "127.0.0.1"

# Documentation settings
docs:
  enabled: true
  directories:
    - "autocode/"
    - "examples/"
    - "docs/"
  file_extensions:
    - ".py"
    - ".js"
    - ".html"
    - ".css"
    - ".md"
  exclude:
    - "__pycache__/"
    - "*.pyc"
    - "__init__.py"

# Test settings  
tests:
  enabled: true
  directories:
    - "tests/"
  exclude:
    - "__pycache__/"
    - "*.pyc"
    - "__init__.py"
  test_frameworks:
    - "pytest"
  auto_execute: true
  
# Doc index generation
doc_index:
  enabled: true
  auto_generate: true
  output_path: ".clinerules/docs_index.json"
  update_on_docs_change: true

# OpenCode integration
opencode:
  enabled: true
  model: "claude-4-sonnet"
  max_tokens: 64000
  config_path: ".opencode.json"
  timeout: 300
  quiet_mode: true
  json_output: true
```

## 📚 Documentation

- **[CLI Interface](docs/autocode/cli.md)**: Interfaz unificada de comandos
- **[Módulo Core](docs/autocode/core/_module.md)**: Herramientas fundamentales de análisis
- **[Módulo API](docs/autocode/api/_module.md)**: Interfaz web y REST API  
- **[Módulo Orchestration](docs/autocode/orchestration/_module.md)**: Automatización y programación
- **[Módulo Web](docs/autocode/web/_module.md)**: Dashboard web interactivo
- **[Examples](examples/)**: Ejemplos de uso y plantillas

## 🔧 Architecture

```
autocode/
├── cli.py              # CLI interface
├── core/               # Core functionality
│   ├── doc_checker.py     # Documentation verification
│   ├── test_checker.py    # Test validation
│   ├── git_analyzer.py    # Git change analysis
│   ├── opencode_executor.py # OpenCode integration
│   └── token_counter.py   # Token counting
├── api/                # Web API
│   ├── server.py          # FastAPI application
│   └── models.py          # Pydantic models
├── orchestration/      # Automation
│   ├── daemon.py          # Monitoring daemon
│   └── scheduler.py       # Task scheduler
└── web/               # Web interface
    ├── templates/         # HTML templates
    └── static/           # CSS/JS assets
```

## 🌐 Web Interface

The web dashboard provides:

- **📊 System Status**: Daemon uptime, total checks, last check time
- **✅ Active Checks**: Real-time status of all enabled checks
- **⚙️ Configuration**: Live adjustment of check intervals
- **🎮 Manual Controls**: Run any check immediately
- **📈 Results**: Detailed output from each check

### Keyboard Shortcuts
- **Space**: Manual refresh
- **R**: Toggle auto-refresh on/off

## 🤖 AI Integration

### OpenCode Support
Autocode integrates with [OpenCode](https://github.com/opencode-ai/opencode) for AI-powered analysis:

```bash
# Setup OpenCode configuration
uv run autocode opencode --validate

# List available prompts
uv run autocode opencode --list-prompts

# Run AI analysis
uv run autocode opencode --prompt "Review code for security vulnerabilities"

# Use predefined prompts
uv run autocode opencode --prompt-file code-review
```

## 🧪 Development

### Running Tests
```bash
uv run pytest tests/
```

### Starting Development Server
```bash
uv run autocode daemon --verbose
```

### Adding New Checks
1. Create checker in `autocode/core/`
2. Add to daemon's task setup
3. Update web interface
4. Add tests

## 📊 API Reference

- `GET /` - Web dashboard
- `GET /api/status` - System status
- `GET /api/checks` - All check results
- `POST /api/checks/{check_name}/run` - Run specific check
- `GET /api/config` - Current configuration
- `PUT /api/config` - Update configuration
- `GET /health` - Health check

## 🔧 Troubleshooting

### Common Issues

#### `ModuleNotFoundError: No module named 'autocode'`
**Solution**: Ensure you're in the correct directory and the package is installed:
```bash
# Make sure you're in the autocode directory
cd autocode

# Reinstall the package
uv sync
# or
pip install -e .

# Verify installation
uv run autocode --help
```

#### `Port 8080 already in use`
**Solution**: Change the port in `autocode_config.yml`:
```yaml
api:
  port: 8081  # or any other available port
  host: "127.0.0.1"
```

#### `uv` command not found
**Solution**: Install uv first:
```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative
pip install uv
```

#### Permission denied errors
**Solution**: On Windows, run PowerShell as administrator. On Linux/macOS:
```bash
chmod +x ~/.local/bin/uv
```

#### Dashboard not loading
**Solution**: 
1. Ensure daemon is running: `uv run autocode daemon`
2. Check if port is accessible: `http://127.0.0.1:8080`
3. Check firewall settings
4. Try different browser or incognito mode

#### Token count warnings
**Solution**: This is normal for large projects. Adjust token threshold in config:
```yaml
opencode:
  max_tokens: 100000  # increase limit
```

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Run daemon with `--verbose` flag
2. **Search issues**: Check [GitHub Issues](https://github.com/brunvelop/autocode/issues)
3. **Create an issue**: Include error logs and system information

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for the web interface
- Integrates with [OpenCode](https://github.com/opencode-ai/opencode) for AI analysis
- Uses [tiktoken](https://github.com/openai/tiktoken) for token counting

---

**Made with ❤️ for developers who value code quality**

```bash
uv lock --upgrade-package autocode && uv sync
```

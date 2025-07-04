# Autocode - Automated Development Tools

Updated autocode system with continuous monitoring and web interface.

## Features

### CLI Tools (Original)
- **Documentation Check**: Verify documentation is up-to-date with code changes
- **Git Analysis**: Analyze git changes for commit message generation

### New: Monitoring Daemon
- **Continuous Monitoring**: Automatic periodic execution of checks
- **Web Dashboard**: Simple, clean interface to view check results
- **Real-time Updates**: Dashboard auto-refreshes every 5 seconds
- **Manual Triggers**: Run checks on-demand via web interface
- **Configuration**: Adjust check intervals and enable/disable checks

## Usage

### CLI Commands

```bash
# Traditional CLI usage (unchanged)
uv run -m autocode.cli check-docs
uv run -m autocode.cli git-changes
uv run -m autocode.cli git-changes --verbose

# New: Start monitoring daemon
uv run -m autocode.cli daemon
uv run -m autocode.cli daemon --port 8080 --verbose
```

### Web Interface

1. Start the daemon:
   ```bash
   uv run -m autocode.cli daemon
   ```

2. Open your browser to: `http://127.0.0.1:8080`

3. The dashboard shows:
   - **System Status**: Daemon uptime, total checks run, last check time
   - **Active Checks**: Current status of doc_check and git_check
   - **Configuration**: Enable/disable checks and adjust intervals
   - **Manual Controls**: Run checks immediately

### Configuration

Default configuration:
- **Documentation Check**: Every 10 minutes
- **Git Analysis**: Every 5 minutes
- **Web Interface**: Port 8080, localhost only

Adjust intervals in the web interface or modify the default values in `models.py`.

## Architecture

The updated system follows a clean, simple design:

```
autocode/
├── cli.py              # CLI interface (enhanced)
├── doc_checker.py      # Documentation checker (unchanged)
├── git_analyzer.py     # Git analyzer (unchanged)
├── daemon.py           # Monitoring daemon
├── scheduler.py        # Task scheduler
├── api.py              # FastAPI application
├── models.py           # Pydantic models
└── web/                # Web interface
    ├── templates/
    │   └── index.html  # Dashboard
    └── static/
        ├── style.css   # Styles
        └── app.js      # Frontend logic
```

### Key Design Principles

1. **No Code Duplication**: Daemon uses existing DocChecker and GitAnalyzer directly
2. **Backwards Compatibility**: Original CLI commands work unchanged
3. **Stateless**: No persistence, current state only
4. **Simple UI**: Minimal, functional web interface
5. **FastAPI**: Modern, fast API framework

## API Endpoints

- `GET /` - Web dashboard
- `GET /api/status` - Complete system status
- `GET /api/checks` - All check results
- `GET /api/checks/{check_name}` - Specific check result
- `POST /api/checks/{check_name}/run` - Run check manually
- `GET /api/config` - Current configuration
- `PUT /api/config` - Update configuration
- `GET /health` - Health check

## Development

### Adding New Checks

1. Create the check logic (following existing patterns)
2. Add it to the daemon's `_setup_tasks()` method
3. Update the web interface to display the new check
4. Add API endpoints as needed

### Frontend Development

The web interface uses vanilla JavaScript with:
- Automatic refresh every 5 seconds
- Manual refresh with spacebar
- Configuration updates in real-time
- Responsive design

### Testing

```bash
# Test CLI functionality
uv run -m autocode.cli check-docs
uv run -m autocode.cli git-changes

# Test daemon (Ctrl+C to stop)
uv run -m autocode.cli daemon --verbose
```

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Jinja2**: Template engine
- **Pydantic**: Data validation
- Existing dependencies (unchanged)

## Keyboard Shortcuts

When viewing the web dashboard:
- **Space**: Manual refresh
- **R**: Toggle auto-refresh on/off

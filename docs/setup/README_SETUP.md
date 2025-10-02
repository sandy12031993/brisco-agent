# Setup Guide - PHP-to-Laravel Migration Analysis System

Quick setup guide for running this system on any PC.

## Prerequisites

- **Python 3.8+** (tested with Python 3.12)
- **Git** (for cloning)
- **Windows PowerShell** (for Windows users)

## Quick Start (Windows)

### 1. Clone Repository

```powershell
cd C:\your\project\path
git clone <repository-url> .agent
cd .agent
```

### 2. Run Setup

```powershell
.\setup.ps1
```

This will:
- Create Python virtual environment (`venv/`)
- Install all required packages
- Initialize knowledge database
- Verify installation

### 3. Verify Setup

```powershell
.\TEST_SETUP.ps1
```

All tests should pass (5/5).

### 4. Configure Project

Edit `config/config.yaml`:

```yaml
project:
  name: "Your Project Name"
  root_path: "C:/path/to/your/project"
  core_path: "C:/path/to/your/project/core"      # Legacy PHP
  laravel_path: "C:/path/to/your/project/laravel" # New Laravel
```

### 5. Run Commands

```powershell
# Show system status
.\run.ps1 status

# Analyze a PHP file
.\run.ps1 analyze ../core/index.php --smart --output analysis.md

# Learn from feedback
.\run.ps1 learn-from-feedback analysis.md examples/sample_feedback.md

# Show learned insights
.\run.ps1 show-insights

# See all commands
.\run.ps1 --help
```

## Setup (Linux/Mac)

### 1. Clone Repository

```bash
cd /your/project/path
git clone <repository-url> .agent
cd .agent
```

### 2. Run Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure & Run

```bash
# Edit config
nano config/config.yaml

# Run commands
python main.py status
python main.py analyze ../core/index.php --smart
python main.py show-insights
```

## Project Structure

```
.agent/
├── agents/              # Multi-agent system (Coordinator, PHP, Laravel, Database)
├── analyzers/           # Code parsers (PHP, SQL, Vue, Routes, Relationships)
├── utils/               # Utilities (AI, Pattern Learner, Flow Diagrams, Token Tracking)
├── config/              # Configuration files
├── examples/            # Example feedback files
├── knowledge/           # Auto-generated (gitignored)
│   ├── patterns.json    # Learned patterns
│   └── insights.db      # Insights database
├── main.py              # Main CLI interface
├── setup.ps1            # Windows setup script
├── run.ps1              # Windows run wrapper
├── requirements.txt     # Python dependencies
└── README.md            # Main documentation
```

## What Gets Excluded from Git

The `.gitignore` excludes:
- `venv/` - Virtual environment
- `knowledge/` - Auto-generated patterns and database
- `outputs/` - Analysis output files
- `test_*.md` - Test files
- `*.log` - Log files
- `*.db` - SQLite databases
- `__pycache__/` - Python cache

## Available Commands

| Command | Description |
|---------|-------------|
| `status` | Show system configuration and AI provider status |
| `analyze` | Smart analysis with relationship mapping |
| `learn-from-feedback` | Extract patterns from analysis feedback |
| `show-insights` | Display learned patterns and insights |
| `compare` | Compare legacy vs Laravel implementation |
| `feature` | Plan new feature migration |
| `graph` | Generate dependency graphs |
| `progress` | Track feature migration progress |
| `analyze-file` | Analyze specific file |
| `analyze-module` | Analyze entire module/directory |
| `generate-report` | Generate comprehensive migration report |
| `prepare-for-claude` | Prepare context for Claude Code |
| `token-stats` | Show token usage statistics |

## AI Provider Configuration (Optional)

The system works in **Manual Mode** (Claude Code) by default, but you can configure AI providers:

```yaml
# In config/config.yaml
ai_providers:
  anthropic:
    api_key: "your-key-here"  # Optional
    model: "claude-3-5-sonnet-20241022"

  openai:
    api_key: "your-key-here"  # Optional
    model: "gpt-4"
```

Or use environment variables:
```powershell
$env:ANTHROPIC_API_KEY = "your-key"
$env:OPENAI_API_KEY = "your-key"
```

## Troubleshooting

### PowerShell Execution Policy

If you get "execution policy" error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

Make sure Python 3.8+ is installed and in PATH:
```powershell
python --version  # Should show Python 3.8+
```

### Unicode Errors (Windows)

The system automatically handles UTF-8 encoding for Windows. If you still see errors, set:
```powershell
$env:PYTHONIOENCODING = "utf-8"
chcp 65001
```

### Module Import Errors

If you see import errors, ensure virtual environment is activated:
```powershell
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac
```

## First-Time Usage Example

```powershell
# 1. Setup
.\setup.ps1

# 2. Test
.\TEST_SETUP.ps1

# 3. Analyze a file
.\run.ps1 analyze ../core/index.php --smart --output my_analysis.md

# 4. Review generated analysis.md, add your feedback to examples/my_feedback.md

# 5. Learn from your feedback
.\run.ps1 learn-from-feedback my_analysis.md examples/my_feedback.md

# 6. See what was learned
.\run.ps1 show-insights
```

## Support

For issues, see:
- Main documentation: `README.md`
- Example files: `examples/`
- Configuration guide: `config/config.yaml`

## License

[Your License Here]

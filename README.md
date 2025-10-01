# PHP-to-Laravel Migration Analysis System

A sophisticated multi-agent system for analyzing and managing PHP to Laravel migration projects. This system uses specialized AI agents to analyze legacy PHP code, modern Laravel applications, and database schemas to provide comprehensive migration insights and recommendations.

## Features

### 🤖 Multi-Agent Architecture
- **PHP Legacy Agent**: Analyzes PHP 5.6 codebase, identifies patterns, security issues, and migration requirements
- **Laravel Agent**: Analyzes Laravel/Vue applications, tracks migration progress, and identifies gaps
- **Database Agent**: Analyzes database schemas, migrations, and data integrity
- **Coordinator Agent**: Orchestrates multiple agents and provides unified analysis

### 🔍 Advanced Analysis Capabilities
- **Code Parsing**: AST-based parsing for accurate code structure analysis
- **Pattern Recognition**: Identifies anti-patterns, security vulnerabilities, and architectural issues
- **Dependency Mapping**: Builds comprehensive dependency graphs across the codebase
- **Migration Tracking**: Tracks what's been migrated vs. what's pending
- **Cross-Reference Analysis**: Finds relationships between core PHP and Laravel implementations

### 🧠 AI-Powered Insights
- **Multi-Provider Support**: Supports Anthropic Claude, OpenAI GPT, and Cursor API
- **Flexible AI Integration**: Works with API keys or manual Claude Code workflow
- **Token Budget Management**: Intelligent usage tracking and cost optimization
- **Learning System**: Continuously learns from analysis patterns and improves recommendations
- **Persistent Knowledge**: Stores insights and patterns in SQLite database for future reference

### 📊 Comprehensive Reporting
- **Executive Summaries**: High-level migration status and health reports
- **Detailed Analysis**: File-by-file and module-by-module analysis results
- **Migration Recommendations**: Prioritized action plans with effort estimates
- **Security Assessments**: Critical security issue identification and remediation plans

## Installation

### Prerequisites
- Python 3.8 or higher
- Access to your PHP and Laravel codebases
- (Optional) AI provider API keys for enhanced insights:
  - Anthropic API key for Claude
  - OpenAI API key for GPT models
  - Cursor API key (when available)

### Setup

#### Windows Users (Recommended)

**One-time setup:**
```cmd
cd C:\MAMP\htdocs\br\.agent
setup.bat
```

This will:
- Create a virtual environment (like `node_modules` for npm)
- Install all dependencies in isolation
- Avoid conflicts with other Python projects

**Running commands:**
```cmd
# Check system status
run.bat status

# Analyze a file
run.bat analyze core/cyclecount.php --smart

# Get help
run.bat --help
```

**What's happening:**
- `setup.bat` - Creates `venv\` folder with isolated Python packages
- `run.bat` - Activates venv and runs commands
- Works like: `npm install` + `npm run` for Node.js

**To manually activate venv:**
```cmd
venv\Scripts\activate.bat
python main.py status
```

---

#### Linux/Mac Users

1. **Create Virtual Environment**
   ```bash
   cd /path/to/.agent
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Commands**
   ```bash
   python main.py status
   ```

---

#### Without Virtual Environment (Not Recommended)

If you prefer global installation:

```bash
cd C:/MAMP/htdocs/br/.agent
pip install -r requirements.txt
python main.py status
```

**Note:** This may cause conflicts with other Python projects.

---

### Configure AI Providers (Optional)

**Interactive Setup:**
```cmd
run.bat   # or: python setup_wizard.py
```

**Manual Configuration:**
```cmd
# Option 1: Anthropic Claude
set ANTHROPIC_API_KEY=your_anthropic_key_here
pip install anthropic>=0.18.0

# Option 2: OpenAI GPT
set OPENAI_API_KEY=your_openai_key_here
pip install openai>=1.0.0

# Option 3: Use without API keys (Manual Claude Code workflow)
# No additional setup required - works in manual mode
```

### Verify Installation

```cmd
# Windows with venv
run.bat status

# Or without venv
python main.py status
```

You should see:
```
╔════════════════════════════════════════════╗
║  Agent System Status                       ║
╚════════════════════════════════════════════╝

AI Provider: Manual Mode (Claude Code)
Agents: ✓ All Ready
```

## Usage

> **Windows Users:** Replace `python main.py` with `run.bat` in all commands below.
>
> Example: `run.bat analyze-file core/file.php` instead of `python main.py analyze-file core/file.php`

### Basic File Analysis

Analyze a specific PHP file:
```bash
# Windows
run.bat analyze-file C:/MAMP/htdocs/br/core/controllers/UserController.php

# Linux/Mac
python main.py analyze-file C:/MAMP/htdocs/br/core/controllers/UserController.php
```

Analyze with specific agent:
```bash
python main.py analyze-file core/auth/login.php --agent php
```

Save analysis results with different formats:
```bash
# Standard JSON output
python main.py analyze-file core/models/User.php --output user_analysis.json

# Claude Code optimized format (3K tokens)
python main.py analyze-file core/models/User.php --format claude-summary --output user_claude.md

# Brief summary (1K tokens)
python main.py analyze-file core/models/User.php --format brief --output user_brief.md

# Detailed analysis (8K tokens)
python main.py analyze-file core/models/User.php --format detailed --output user_detailed.md

# Custom token limit
python main.py analyze-file core/models/User.php --format claude-summary --max-tokens 2000
```

### Module Analysis

Analyze entire modules:
```bash
# Analyze core PHP module
python main.py analyze-module C:/MAMP/htdocs/br/core

# Analyze Laravel module with Claude format
python main.py analyze-module C:/MAMP/htdocs/br/laravel/app --format claude-summary

# Brief module overview
python main.py analyze-module core/auth --format brief --summary
```

### Comprehensive Reports

Generate full migration report:
```bash
# Standard JSON report
python main.py generate-report --scope all --output migration_report.json

# Executive summary format for stakeholders
python main.py generate-report --scope all --format markdown --output executive_summary.md

# Claude Code optimized report
python main.py generate-report --scope all --format claude-summary --output claude_analysis.md
```

Scope-specific reports:
```bash
# Core PHP analysis only
python main.py generate-report --scope core --format detailed

# Laravel analysis brief
python main.py generate-report --scope laravel --format brief
```

### Entity Search

Find entities across the codebase:
```bash
# Find all references to a class
python main.py find-entity UserController --type class

# Find database tables
python main.py find-entity users --type table

# Find Vue components
python main.py find-entity LoginForm --type component
```

### Knowledge Base

View learned insights:
```bash
# Show recent insights
python main.py show-insights

# Filter by type
python main.py show-insights --type security_issues --limit 20
```

### Claude Code Integration

Prepare context specifically optimized for Claude Code analysis:

```bash
# Analyze single file for Claude Code
python main.py prepare-for-claude --file core/auth/login.php --focus security

# Analyze module with migration focus
python main.py prepare-for-claude --module core/controllers --focus migration

# Custom token limit and output
python main.py prepare-for-claude --file core/models/User.php --max-tokens 2500 --output my_analysis.md

# Focus areas available:
# --focus migration (default)
# --focus security
# --focus dependencies
# --focus api-integrations
# --focus database
# --focus all
```

### Token Usage Management

Monitor and optimize token usage:

```bash
# Check today's usage statistics
python main.py token-stats

# Check current session usage
python main.py token-stats --period session

# Weekly usage overview
python main.py token-stats --period week

# All-time statistics
python main.py token-stats --period all
```

## Configuration

The system configuration is stored in `config/config.yaml`. Key settings include:

### Project Paths
```yaml
project:
  root_path: "C:/MAMP/htdocs/br"
  core_path: "C:/MAMP/htdocs/br/core"
  laravel_path: "C:/MAMP/htdocs/br/laravel"
```

### Analysis Files
```yaml
analysis_files:
  core_analysis: "C:/MAMP/htdocs/br/core_project_analysis.json"
  laravel_analysis: "C:/MAMP/htdocs/br/laravel_project_analysis.json"
  database_analysis: "C:/MAMP/htdocs/br/database_schema_analysis.json"
```

### AI Provider Configuration
```yaml
ai_provider:
  mode: 'none'  # Options: 'none', 'anthropic', 'openai', 'cursor'

  # API keys (can be environment variables or direct values)
  anthropic_api_key: null
  openai_api_key: null
  cursor_api_key: null

  # Token budget management
  token_budget:
    max_tokens_per_analysis: 3000
    max_tokens_per_session: 30000
    warn_at_percentage: 80

  # Manual mode settings
  manual_export_path: 'claude_context'
  fallback_to_manual: true
```

### Output Formats

The system supports 5 output formats optimized for different use cases:

#### JSON Format (`--format json`)
- **Use case**: Data processing, automation, detailed analysis
- **Token limit**: None (complete data)
- **Content**: Full analysis results with all metadata
```bash
python main.py analyze-file core/auth.php --format json --output analysis.json
```

#### Claude Summary Format (`--format claude-summary`)
- **Use case**: Claude Code analysis, strategic review
- **Token limit**: 3,000 tokens (default)
- **Content**: Scannable overview, critical issues, migration checklist, suggested prompts
```bash
python main.py analyze-file core/auth.php --format claude-summary --output claude_context.md
```

#### Brief Format (`--format brief`)
- **Use case**: Quick scans, overview dashboards
- **Token limit**: 1,000 tokens
- **Content**: Ultra-condensed summary with key metrics and top issues
```bash
python main.py analyze-module core/controllers --format brief
```

#### Detailed Format (`--format detailed`)
- **Use case**: Comprehensive analysis, technical deep-dives
- **Token limit**: 8,000 tokens
- **Content**: Complete analysis with all classes, methods, security issues
```bash
python main.py generate-report --scope all --format detailed --output comprehensive.md
```

#### Markdown Format (`--format markdown`)
- **Use case**: Documentation, stakeholder reports
- **Token limit**: 5,000 tokens
- **Content**: Human-readable with executive summary and recommendations
```bash
python main.py generate-report --scope core --format markdown --output executive_report.md
```

### Token Optimization Guide

**For Quick Analysis:**
```bash
# Use brief format for fast overviews (1K tokens)
python main.py analyze-module core/auth --format brief

# Focus on specific areas
python main.py prepare-for-claude --file auth.php --focus security --max-tokens 2000
```

**For Claude Code Review:**
```bash
# Perfect for pasting into Claude Code (3K tokens)
python main.py prepare-for-claude --module core/controllers --focus migration

# Custom token limits based on context window
python main.py analyze-file complex.php --format claude-summary --max-tokens 2500
```

**For Comprehensive Analysis:**
```bash
# When you need everything (8K tokens)
python main.py generate-report --scope all --format detailed

# Or break into smaller chunks
python main.py analyze-module core/auth --format claude-summary
python main.py analyze-module core/controllers --format claude-summary
```

**Monitor Usage:**
```bash
# Check if you're within budget
python main.py token-stats

# Optimize based on recommendations
# System will suggest format changes based on usage patterns
```

### Agent Configuration
```yaml
agents:
  php_legacy:
    extensions: [".php", ".inc", ".class.php"]
    ignore_patterns: ["vendor/", "cache/", "tmp/"]

  laravel:
    extensions: [".php", ".vue", ".js", ".blade.php"]
    paths: ["app/", "resources/", "routes/"]
```

## Architecture

### Directory Structure
```
.agent/
├── agents/                     # Specialized analysis agents
│   ├── base_agent.py          # Base agent class with common functionality
│   ├── php_legacy_agent.py    # PHP 5.6 codebase analysis
│   ├── laravel_agent.py       # Laravel/Vue analysis
│   ├── database_agent.py      # Database schema analysis
│   └── coordinator_agent.py   # Multi-agent orchestration
├── analyzers/                  # Code parsing and analysis
│   ├── php_parser.py          # PHP code structure parsing
│   ├── vue_parser.py          # Vue/Laravel code parsing
│   └── sql_parser.py          # SQL schema parsing
├── utils/                      # Utility modules
│   ├── __init__.py            # Utils package initialization
│   ├── ai_helper.py           # Multi-provider AI integration
│   └── provider_checker.py    # AI provider detection and validation
├── knowledge/                  # Persistent knowledge storage
│   ├── patterns.json          # Migration patterns and best practices
│   ├── migrations_map.json    # Migration tracking and mappings
│   └── learned_insights.db    # SQLite database for insights
├── config/                     # Configuration files
│   └── config.yaml           # Main configuration
├── claude_context/             # Manual Claude Code workflow exports
├── main.py                    # CLI interface
├── setup_wizard.py            # Interactive AI provider setup
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

### Agent Specializations

#### PHP Legacy Agent
- Parses PHP 5.6 syntax and patterns
- Identifies security vulnerabilities (SQL injection, XSS, etc.)
- Detects deprecated features and anti-patterns
- Maps to Laravel equivalents
- Estimates migration complexity

#### Laravel Agent
- Analyzes Laravel controllers, models, and views
- Parses Vue.js components and JavaScript
- Checks Laravel best practices compliance
- Identifies migration gaps and incomplete features
- Validates API integration patterns

#### Database Agent
- Parses SQL schema definitions
- Analyzes Laravel migration files
- Checks referential integrity and constraints
- Identifies performance optimization opportunities
- Validates Laravel compatibility

#### Coordinator Agent
- Orchestrates multi-agent analysis
- Synthesizes insights across agents
- Generates comprehensive reports
- Manages parallel processing
- Integrates with multiple AI providers for enhanced reasoning
- Handles token budget management and usage optimization
- Exports analysis context for manual Claude Code review when needed

## AI Provider Workflows

### API-Based Analysis (Anthropic/OpenAI)
When configured with API keys, the system provides real-time AI analysis:

```bash
# Check current provider status
python main.py status

# Generate analysis with AI insights
python main.py generate-report --scope all --output ai_enhanced_report.json
```

**Features:**
- Real-time strategic analysis and recommendations
- Pattern recognition and security assessment
- Migration complexity estimation
- Token usage tracking and budget management

### Manual Claude Code Workflow
When no API keys are configured, the system exports analysis context for manual review:

```bash
# Analysis exports to claude_context/ directory
python main.py analyze-module core/auth

# Files exported:
# claude_context/security_analysis_20240101_123456_abc123.md
# claude_context/migration_analysis_20240101_123457_def456.md
```

**Workflow:**
1. System performs technical analysis (parsing, metrics, patterns)
2. Analysis context exported to markdown files in `claude_context/`
3. Open files in Claude Code or Cursor for AI-powered strategic insights
4. Use insights to inform migration decisions and planning

### Hybrid Approach
Combine automated analysis with manual review for optimal results:

```bash
# Run automated analysis
python main.py analyze-module core/ --output core_analysis.json

# Export specific components for manual review
python main.py find-entity AuthController --type class
```

## Example Workflows

### 1. Initial Project Assessment
```bash
# Check system status and AI provider configuration
python main.py status

# Set up AI providers if needed
python setup_wizard.py

# Generate comprehensive baseline report
python main.py generate-report --scope all --output baseline_report.json

# Analyze critical security components first
python main.py analyze-module core/auth --verbose
```

### 2. Feature Migration Planning
```bash
# Analyze specific feature module
python main.py analyze-module core/modules/user_management

# Find related Laravel implementations
python main.py find-entity UserController

# Check migration status
python main.py show-insights --type migration_status
```

### 3. Security Audit
```bash
# Find security issues across the project
python main.py show-insights --type security_issues

# Analyze high-risk files
python main.py analyze-file core/auth/login.php --verbose

# Generate security-focused report
python main.py generate-report --scope core --output security_audit.json
```

### 4. Migration Validation
```bash
# Compare core vs Laravel implementations
python main.py analyze-module laravel/app/Http/Controllers

# Check database migration completeness
python main.py analyze-module laravel/database/migrations

# Generate final migration report
python main.py generate-report --scope all --output final_report.json
```

## Analysis Output Examples

### File Analysis Output
```json
{
  "file_path": "core/controllers/UserController.php",
  "parsed": true,
  "classes": [
    {
      "name": "UserController",
      "methods": ["index", "create", "update", "delete"],
      "extends": "BaseController"
    }
  ],
  "migration_recommendations": {
    "priority": "high",
    "complexity": "medium",
    "required_changes": [
      "Convert MySQL direct functions to Eloquent ORM",
      "Add proper input validation",
      "Implement CSRF protection"
    ]
  },
  "patterns": {
    "security_issues": [
      {
        "type": "sql_concatenation",
        "severity": "high",
        "description": "Potential SQL injection through string concatenation"
      }
    ]
  }
}
```

### Module Analysis Output
```json
{
  "module_path": "core/auth",
  "summary": {
    "total_files": 15,
    "migration_priorities": {"high": 8, "medium": 5, "low": 2},
    "security_issues": 12,
    "api_integrations": ["oauth", "ldap"]
  },
  "cross_agent_insights": {
    "migration_completeness": {"overall_score": 65},
    "security_assessment": {"overall_risk_level": "high"}
  }
}
```

## Integration with Existing Analysis Files

The system automatically loads and enhances your existing analysis files:

- **core_project_analysis.json**: 17,536 PHP files analysis
- **laravel_project_analysis.json**: Laravel models and controllers
- **database_schema_analysis.json**: Complete database schema mapping

These files provide the foundation for cross-reference analysis and migration tracking.

## Extending the System

### Adding Custom Patterns
Add patterns to `knowledge/patterns.json`:
```json
{
  "custom_patterns": {
    "your_pattern": {
      "detection": "regex_pattern",
      "severity": "medium",
      "solution": "Laravel equivalent"
    }
  }
}
```

### Custom Analysis Rules
Extend agent classes to add custom analysis logic:
```python
class CustomPHPAgent(PHPLegacyAgent):
    def analyze_custom_pattern(self, content):
        # Your custom analysis logic
        pass
```

### Integration with CI/CD
Use the CLI in automated workflows:
```bash
#!/bin/bash
# Migration quality gate
python main.py generate-report --scope all --output ci_report.json
python check_migration_quality.py ci_report.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration Issues**: Verify paths in `config/config.yaml`
   ```bash
   python main.py status
   ```

3. **Analysis File Missing**: Check if the required JSON files exist
   ```bash
   ls -la *.json
   ```

4. **Permission Errors**: Ensure read access to source directories

5. **AI Provider Issues**: Check provider configuration and API keys
   ```bash
   python main.py status  # Check provider status
   python setup_wizard.py  # Reconfigure providers
   ```

### AI Provider Troubleshooting

**No API Key Issues:**
```bash
# Check environment variables
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Use manual mode if API keys not available
# Analysis will export to claude_context/ directory
```

**Invalid API Key:**
```bash
# Run setup wizard to validate and fix keys
python setup_wizard.py

# Or manually test with specific provider
python -c "from utils.provider_checker import validate_api_key; print(validate_api_key('anthropic', 'your_key'))"
```

**Token Budget Exceeded:**
```bash
# Check current usage
python main.py status

# Adjust budget limits in config/config.yaml
# Or wait for session reset
```

### Debug Mode
Run with verbose output:
```bash
python main.py analyze-file path/to/file.php --verbose
```

## Contributing

This system is designed to be extensible and can be customized for your specific migration needs. Key extension points include:

- Custom parsers for specific frameworks
- Additional analysis patterns
- Integration with other tools and APIs
- Custom reporting formats

## License

This migration analysis system is part of your PHP-to-Laravel migration project. Modify and extend as needed for your specific requirements.

## Support

For issues or questions about the migration analysis system:

1. Check the troubleshooting section above
2. Review the configuration in `config/config.yaml`
3. Use `python main.py status` to verify system health
4. Enable verbose output for detailed debugging information
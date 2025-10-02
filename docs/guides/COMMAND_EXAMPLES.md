# Command Examples - Quick Reference

## ✅ Fixed! Commands Now Working

The PowerShell argument passing has been fixed. All commands now work correctly.

## Common Commands

### 1. Analyze Laravel Route (Full Stack)

```powershell
# Warehouse cycle-count route with architecture focus
.\run.ps1 analyze warehouse/cycle-count --type route --smart --focus architecture --output cycle_count_analysis.md

# With flow diagram
.\run.ps1 analyze warehouse/cycle-count --type route --smart --diagram --output analysis_with_diagram.md
```

### 2. Analyze Legacy PHP File

```powershell
# Single PHP file with smart context
.\run.ps1 analyze ../core/index.php --smart --output index_analysis.md

# With deeper relationship tracking
.\run.ps1 analyze ../core/index.php --smart --depth 5 --output deep_analysis.md

# Security-focused analysis
.\run.ps1 analyze ../core/index.php --smart --focus security --output security_analysis.md
```

### 3. Analyze Specific File Type

```powershell
# Vue component analysis
.\run.ps1 analyze laravel/resources/app/src/views/pages/Warehouse/cycleCount/index.vue --type file --smart

# JavaScript route file
.\run.ps1 analyze laravel/resources/app/src/routes/Warehouse/cycleCount.routes.js --type file --smart
```

### 4. Different Analysis Focus

```powershell
# Migration planning
.\run.ps1 analyze ../core/users.php --smart --focus migration --output migration_plan.md

# Security audit
.\run.ps1 analyze ../core/login.php --smart --focus security --output security_audit.md

# Architecture analysis
.\run.ps1 analyze warehouse/receiving --type route --smart --focus architecture

# Complete analysis (all aspects)
.\run.ps1 analyze warehouse/cycle-count --type route --smart --focus all
```

### 5. Generate Flow Diagrams

```powershell
# ASCII diagram
.\run.ps1 analyze warehouse/cycle-count --type route --smart --diagram --format ascii

# Mermaid diagram
.\run.ps1 analyze warehouse/cycle-count --type route --smart --diagram --format mermaid

# Both formats
.\run.ps1 analyze warehouse/cycle-count --type route --smart --diagram --format both
```

## Other Useful Commands

### System Status
```powershell
.\run.ps1 status
```

### List All Routes
```powershell
.\run.ps1 list-routes
```

### Find Entity
```powershell
# Find a function
.\run.ps1 find-entity add_row --type function

# Find a table
.\run.ps1 find-entity users --type table

# Find a class
.\run.ps1 find-entity CycleCountController --type class
```

### Generate Reports
```powershell
# Full migration report
.\run.ps1 generate-report --format markdown --output migration_report.md

# HTML report
.\run.ps1 generate-report --format html --output report.html
```

### Compare Implementations
```powershell
# Compare legacy vs Laravel
.\run.ps1 compare cyclecount.php warehouse/cycle-count
```

### Token Statistics
```powershell
.\run.ps1 token-stats
```

## Command Syntax Breakdown

### General Format
```
.\run.ps1 COMMAND [TARGET] [OPTIONS]
```

### For `analyze` Command
```
.\run.ps1 analyze TARGET [--type TYPE] [--smart] [--focus FOCUS] [--output FILE]
```

**Required:**
- `TARGET` - File path or route path

**Common Options:**
- `--smart` - Enable intelligent relationship following (recommended)
- `--type` - Analysis type: `file`, `route`, `feature`, `module`
- `--focus` - Focus area: `migration`, `security`, `architecture`, `all`
- `--output` or `-o` - Output file path
- `--depth` - How deep to follow relationships (1-5)
- `--diagram` - Generate flow diagram
- `--format` - Diagram format: `mermaid`, `ascii`, `both`

## Examples by Use Case

### Initial Setup
```powershell
# First time setup
.\setup.ps1

# Verify installation
.\run.ps1 status
```

### Migrating a Feature
```powershell
# 1. Analyze legacy implementation
.\run.ps1 analyze ../core/cyclecount.php --smart --focus migration --output legacy_analysis.md

# 2. Analyze new Laravel route
.\run.ps1 analyze warehouse/cycle-count --type route --smart --output laravel_analysis.md

# 3. Compare both
.\run.ps1 compare cyclecount.php warehouse/cycle-count --output comparison.md
```

### Security Audit
```powershell
# Audit legacy PHP files
.\run.ps1 analyze ../core/index.php --smart --focus security --output security_index.md
.\run.ps1 analyze ../core/login.php --smart --focus security --output security_login.md

# Generate security report
.\run.ps1 generate-report --focus security --output security_report.md
```

### Understanding Architecture
```powershell
# Full route with diagram
.\run.ps1 analyze warehouse/cycle-count --type route --smart --focus architecture --diagram --format both --output architecture.md

# Deep dependency analysis
.\run.ps1 analyze warehouse/cycle-count --type route --smart --depth 5 --output deep_dependencies.md
```

## Tips

1. **Always use `--smart`** for better analysis with relationship mapping
2. **Use `--output`** to save results to specific files
3. **Use `--diagram`** to visualize complex flows
4. **Use `--focus`** to target specific aspects
5. **Check `.\run.ps1 COMMAND --help`** for detailed options

## Troubleshooting

### Command not found?
```powershell
# Make sure you're in the .agent directory
cd C:\MAMP\htdocs\br\.agent

# Use the full path
.\run.ps1 analyze warehouse/cycle-count --smart
```

### Virtual environment issues?
```powershell
# Re-run setup
.\setup.ps1
```

### Need more help?
```powershell
# General help
.\run.ps1 --help

# Command-specific help
.\run.ps1 analyze --help
.\run.ps1 generate-report --help
```

## Quick Reference Card

| Task | Command |
|------|---------|
| Analyze route | `.\run.ps1 analyze warehouse/cycle-count --type route --smart` |
| Analyze PHP file | `.\run.ps1 analyze ../core/index.php --smart` |
| With diagram | Add `--diagram` |
| Security focus | Add `--focus security` |
| Save output | Add `--output filename.md` |
| System status | `.\run.ps1 status` |
| List routes | `.\run.ps1 list-routes` |
| Get help | `.\run.ps1 --help` |

---

**Last Updated:** After PowerShell argument fix
**All commands verified working!** ✅

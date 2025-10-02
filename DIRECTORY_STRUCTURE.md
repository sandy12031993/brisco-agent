# .agent Directory Structure

This document describes the organized structure of the Migration Analysis System.

## Directory Tree

```
.agent/
├── README.md                    # Main project readme
├── main.py                      # Entry point for the analysis system
├── requirements.txt             # Python dependencies
├── setup.py                     # Python package setup
├── .gitignore                   # Git ignore rules
│
├── run.ps1                      # Convenience wrapper → scripts/run.ps1
├── run.bat                      # Convenience wrapper → scripts/run.bat
├── setup.ps1                    # Convenience wrapper → scripts/setup.ps1
├── setup.bat                    # Convenience wrapper → scripts/setup.bat
│
├── agents/                      # AI Agent modules
│   ├── __init__.py
│   ├── base_agent.py
│   ├── coordinator_agent.py
│   ├── database_agent.py
│   ├── laravel_agent.py
│   └── php_legacy_agent.py
│
├── analyzers/                   # Code analysis modules
│   ├── __init__.py
│   ├── js_route_parser.py       # JavaScript route parser
│   ├── php_parser.py            # PHP code parser
│   ├── relationship_mapper.py   # File relationship analyzer
│   ├── route_parser.py          # Laravel route parser
│   ├── sql_parser.py            # SQL query parser
│   └── vue_parser.py            # Vue.js component parser
│
├── config/                      # Configuration files
│   └── ...
│
├── docs/                        # 📚 All documentation
│   ├── README.md                # Documentation index
│   ├── IMPLEMENTATION_SUMMARY.md
│   │
│   ├── setup/                   # Setup & installation docs
│   │   ├── WINDOWS_SETUP.md
│   │   ├── SETUP_SUMMARY.md
│   │   └── README_SETUP.md
│   │
│   ├── guides/                  # User guides & tutorials
│   │   ├── QUICK_START.md
│   │   ├── NEW_COMMANDS.md
│   │   ├── TASKS_3_4_GUIDE.md
│   │   └── examples.md
│   │
│   └── fixes/                   # Bug fix documentation
│       ├── API_EXTRACTION_FIX_SUMMARY.md
│       └── PHP_TABLE_EXTRACTION_FIX_SUMMARY.md
│
├── examples/                    # Example files & templates
│   └── sample_feedback.md
│
├── knowledge/                   # Knowledge base (if present)
│   └── ...
│
├── scripts/                     # 🔧 All executable scripts
│   ├── README.md                # Scripts documentation
│   ├── run.ps1                  # PowerShell run script
│   ├── run.bat                  # Batch run script
│   ├── setup.ps1                # PowerShell setup script
│   ├── setup.bat                # Batch setup script
│   ├── setup_wizard.py          # Interactive setup wizard
│   │
│   └── tests/                   # Test scripts
│       ├── TEST_SETUP.ps1
│       └── TEST_SETUP.bat
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── ai_helper.py
│   ├── flow_diagram.py
│   ├── output_formatter.py
│   ├── pattern_learner.py
│   ├── provider_checker.py
│   ├── token_counter.py
│   └── token_tracker.py
│
└── venv/                        # Python virtual environment (gitignored)
    └── ...
```

## Key Changes from Original Structure

### ✅ Organized
- **All documentation** now in `docs/` with logical subfolders
- **All scripts** now in `scripts/` with test scripts separated
- **Convenience wrappers** in root for easy access

### ✅ Cleaned
- Deleted temporary test files (`test_analysis.md`, `WINDOWS_SETUP_COMPLETE.txt`)
- Removed duplicate/old analysis outputs

### ✅ Structured
- **docs/setup/** - All setup-related documentation
- **docs/guides/** - User guides and tutorials
- **docs/fixes/** - Bug fix summaries
- **scripts/tests/** - Test scripts separated from main scripts

## Usage

### Quick Start (from .agent root)

```powershell
# Initial setup (uses wrapper → scripts/setup.ps1)
.\setup.ps1

# Run analysis (uses wrapper → scripts/run.ps1)
.\run.ps1 analyze warehouse/cycle-count --type route --smart
```

### Direct Script Access

```powershell
# Using scripts directly
.\scripts\setup.ps1
.\scripts\run.ps1 analyze ../core/index.php --smart --output analysis.md

# Running tests
.\scripts\tests\TEST_SETUP.ps1
```

## File Organization Rules

### Documentation (docs/)
- **Setup docs** → `docs/setup/`
- **User guides** → `docs/guides/`
- **Bug fixes** → `docs/fixes/`
- **Major architectural docs** → `docs/` root

### Scripts (scripts/)
- **Main scripts** → `scripts/` root
- **Test scripts** → `scripts/tests/`
- **Utility scripts** → `scripts/` root

### Root Directory
- Keep minimal: README, main.py, requirements.txt, setup.py
- Convenience wrappers for common scripts (run.ps1, setup.ps1)
- Configuration files (.gitignore)

## Benefits

1. **Clarity** - Easy to find documentation and scripts
2. **Maintainability** - Logical organization for future additions
3. **Professionalism** - Clean, organized structure
4. **Convenience** - Wrapper scripts for easy access from root
5. **Scalability** - Clear pattern for adding new docs/scripts

## Navigation Tips

- **Need setup help?** → `docs/setup/`
- **Learning the system?** → `docs/guides/QUICK_START.md`
- **Running scripts?** → Use wrappers in root or `scripts/`
- **Understanding fixes?** → `docs/fixes/`
- **Adding documentation?** → Follow the structure in `docs/README.md`

## Maintenance

When adding new files:
- ❌ Don't add .md files to root (except main README)
- ✅ Add documentation to appropriate `docs/` subfolder
- ✅ Add scripts to `scripts/` (or `scripts/tests/` for tests)
- ✅ Update relevant README files to reference new content

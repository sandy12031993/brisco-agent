# Windows Setup Guide

Complete guide for setting up the Migration Analysis System on Windows.

---

## Quick Start (TL;DR)

```cmd
cd C:\MAMP\htdocs\br\.agent
setup.bat
run.bat status
```

Done! 🎉

---

## Understanding Python Virtual Environments

### What's a Virtual Environment?

Think of it like `node_modules` for npm:

| Node.js | Python |
|---------|--------|
| `npm install` | `setup.bat` |
| `node_modules/` | `venv/` |
| `npm run dev` | `run.bat command` |
| `package.json` | `requirements.txt` |

**Why use it?**
- Isolates project dependencies
- Avoids conflicts between projects
- Easy to delete and recreate
- Keeps your global Python clean

---

## Step-by-Step Setup

### 1. Check Python Installation

```cmd
python --version
```

**Expected output:**
```
Python 3.8.0 (or higher)
```

**If not installed:**
1. Download Python from https://www.python.org/
2. ✅ Check "Add Python to PATH" during installation
3. Restart your terminal
4. Verify: `python --version`

---

### 2. Navigate to Project

```cmd
cd C:\MAMP\htdocs\br\.agent
```

**Verify you're in the right place:**
```cmd
dir
```

You should see:
- `main.py`
- `setup.bat`
- `run.bat`
- `requirements.txt`

---

### 3. Run Setup

```cmd
setup.bat
```

**What happens:**
1. Creates `venv\` folder (virtual environment)
2. Installs Python packages inside `venv\`
3. Shows progress and success messages

**Expected output:**
```
========================================
 Migration Analysis System - Setup
========================================

[1/4] Checking Python version...
Python 3.12.0

[2/4] Creating virtual environment...
[SUCCESS] Virtual environment created at: venv\

[3/4] Activating virtual environment...
[SUCCESS] Virtual environment activated

[4/4] Installing dependencies...
This may take a few minutes...

[... package installation messages ...]

========================================
 Setup Complete!
========================================

Virtual environment created at: venv\

Next steps:
  1. Run: run.bat status
  2. Try: run.bat analyze --help
```

**If you see errors:**
- See [Troubleshooting](#troubleshooting) section below

---

### 4. Test the System

```cmd
run.bat status
```

**Expected output:**
```
╔════════════════════════════════════════════╗
║  Agent System Status                       ║
╚════════════════════════════════════════════╝

AI Provider: Manual Mode (Claude Code)
Agents: ✓ All Ready

[... more status info ...]
```

---

## Using the System

### Basic Commands

All commands use `run.bat` instead of `python main.py`:

```cmd
# Check status
run.bat status

# Get help
run.bat --help

# Analyze a file
run.bat analyze core/cyclecount.php --smart

# Learn from feedback
run.bat learn-from-feedback analysis.md feedback.md

# Show insights
run.bat show-insights

# Compare features
run.bat compare cyclecount --smart
```

### What's `run.bat` doing?

```batch
run.bat status
  ↓
Activates venv
  ↓
Runs: python main.py status
  ↓
Uses packages from venv\ (not global Python)
```

---

## File Structure After Setup

```
.agent\
├── venv\                    ← Virtual environment (created by setup.bat)
│   ├── Scripts\
│   │   ├── activate.bat     ← Activation script
│   │   └── python.exe       ← Python executable for this project
│   └── Lib\
│       └── site-packages\   ← Installed packages (rich, click, etc.)
├── setup.bat                ← Run this once to create venv
├── run.bat                  ← Use this to run commands
├── main.py                  ← Main program
├── requirements.txt         ← List of dependencies
└── ...
```

**Important:**
- `venv\` is in `.gitignore` (not tracked by git)
- Safe to delete and recreate anytime
- Size: ~100-200 MB

---

## Advanced Usage

### Manual Activation

If you want to run multiple commands without typing `run.bat` each time:

```cmd
# Activate venv manually
venv\Scripts\activate.bat

# Now you're "inside" the venv
# Your prompt will show: (venv) C:\...

# Run commands directly
python main.py status
python main.py analyze file.php --smart
python main.py show-insights

# Deactivate when done
deactivate
```

### Updating Dependencies

If `requirements.txt` changes:

```cmd
# Activate venv
venv\Scripts\activate.bat

# Update packages
pip install -r requirements.txt --upgrade

# Or just run setup.bat again (it will ask to recreate)
setup.bat
```

### Recreating Virtual Environment

If something breaks:

```cmd
# Delete venv folder
rmdir /s /q venv

# Run setup again
setup.bat
```

---

## Troubleshooting

### Error: "Python is not recognized"

**Problem:** Python not in PATH

**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   - Search Windows for "Environment Variables"
   - Add Python installation directory to PATH
   - Restart terminal

**Verify:**
```cmd
python --version
```

---

### Error: "No module named 'rich'"

**Problem:** Running `python main.py` instead of `run.bat`

**Solution:**
Use `run.bat` instead:
```cmd
run.bat status
```

**Why:**
- `python main.py` uses global Python (packages not installed)
- `run.bat` uses venv Python (packages installed)

---

### Error: "Virtual environment not found"

**Problem:** `venv\` folder doesn't exist

**Solution:**
Run setup first:
```cmd
setup.bat
```

---

### Error: "Failed to create virtual environment"

**Possible causes:**

1. **Permissions issue:**
   ```cmd
   # Run as Administrator
   Right-click CMD → Run as administrator
   setup.bat
   ```

2. **Python venv module missing:**
   ```cmd
   python -m pip install --upgrade pip
   python -m ensurepip
   ```

3. **Antivirus blocking:**
   - Temporarily disable antivirus
   - Run setup.bat
   - Re-enable antivirus

---

### Error: "Failed to install some dependencies"

**Problem:** Network or package issues

**Solution:**

1. **Check internet connection**

2. **Try installing individually:**
   ```cmd
   venv\Scripts\activate.bat
   pip install pyyaml
   pip install click
   pip install rich
   # ... etc
   ```

3. **Use different package index:**
   ```cmd
   pip install -r requirements.txt --index-url https://pypi.org/simple
   ```

4. **Clear pip cache:**
   ```cmd
   pip cache purge
   pip install -r requirements.txt
   ```

---

### System Still Says "Manual Mode" After Setup

**This is normal!**

The system works in "Manual Mode" by default (doesn't require AI API keys).

To use AI providers:
1. Get an API key (Anthropic or OpenAI)
2. Set environment variable:
   ```cmd
   set ANTHROPIC_API_KEY=your_key_here
   ```
3. Or run setup wizard:
   ```cmd
   run.bat   # runs setup_wizard.py
   ```

---

### Deleting Virtual Environment

**To start fresh:**

```cmd
# Method 1: Let setup.bat handle it
setup.bat
# It will ask if you want to recreate

# Method 2: Manual deletion
rmdir /s /q venv
setup.bat
```

**When to recreate:**
- After major dependency updates
- If packages are corrupted
- To free up disk space
- When switching Python versions

---

## Comparison with npm

For Node.js developers, here's how it maps:

| Task | Node.js | Python |
|------|---------|--------|
| Setup | `npm install` | `setup.bat` |
| Run command | `npm run dev` | `run.bat command` |
| Dependencies | `node_modules/` | `venv/` |
| Package list | `package.json` | `requirements.txt` |
| Update deps | `npm update` | `pip install -r requirements.txt --upgrade` |
| Clean install | `rm -rf node_modules && npm install` | `rmdir /s /q venv && setup.bat` |
| Add package | `npm install package` | `pip install package` |
| Global install | `npm install -g` | `pip install` (outside venv) |
| Dev dependencies | `devDependencies` | N/A (all in requirements.txt) |

---

## Best Practices

### ✅ DO:
- Use `run.bat` for all commands
- Keep `venv\` in `.gitignore`
- Recreate venv if problems occur
- Update dependencies regularly

### ❌ DON'T:
- Commit `venv\` to git (it's huge!)
- Mix venv and global Python
- Install packages globally for this project
- Run `python main.py` directly (use `run.bat`)

---

## FAQ

### Q: Where are the packages installed?

**A:** In `.agent\venv\Lib\site-packages\`

Not in your global Python installation.

---

### Q: Can I use `pip` commands?

**A:** Yes, but activate venv first:

```cmd
venv\Scripts\activate.bat
pip list                    # Show installed packages
pip show rich               # Info about a package
pip install some-package    # Install new package
deactivate                  # Exit venv
```

---

### Q: How much disk space does venv use?

**A:** ~100-200 MB

To check:
```cmd
dir venv /s
```

---

### Q: Can I have multiple venvs?

**A:** Yes, but not recommended for this project.

Each project should have one venv.

---

### Q: What if I accidentally delete `venv\`?

**A:** No problem! Just run:

```cmd
setup.bat
```

It will recreate everything.

---

### Q: Do I need to activate venv every time?

**A:** No, `run.bat` does it automatically.

Only activate manually if running multiple commands.

---

### Q: Can I copy venv to another computer?

**A:** No, venv is machine-specific.

On the new computer:
```cmd
setup.bat
```

---

### Q: How do I update Python version?

**A:**

1. Install new Python version
2. Delete old venv:
   ```cmd
   rmdir /s /q venv
   ```
3. Run setup with new Python:
   ```cmd
   setup.bat
   ```

---

## Getting Help

1. **Check this guide first** - Most issues covered above

2. **View command help:**
   ```cmd
   run.bat --help
   run.bat <command> --help
   ```

3. **Check main documentation:**
   - `README.md` - General usage
   - `QUICK_START.md` - Quick start guide
   - `TASKS_3_4_GUIDE.md` - Advanced features

4. **Check Python/pip:**
   ```cmd
   python --version
   pip --version
   venv\Scripts\activate.bat
   pip list
   ```

---

## Success Checklist

After setup, verify:

- [ ] `python --version` shows 3.8+
- [ ] `setup.bat` completed without errors
- [ ] `venv\` folder exists (~100-200 MB)
- [ ] `run.bat status` shows "Agents: ✓ All Ready"
- [ ] `run.bat --help` shows available commands
- [ ] `run.bat show-insights` runs (even if empty)

If all checked, you're ready to go! 🚀

---

## Quick Reference Card

```cmd
# Setup (one time)
setup.bat

# Common commands
run.bat status                       # Check system
run.bat analyze file.php --smart     # Smart analysis
run.bat compare feature --smart      # Compare implementations
run.bat show-insights                # View learned patterns
run.bat --help                       # Get help

# Manual venv activation (optional)
venv\Scripts\activate.bat            # Activate
python main.py status                # Run commands
deactivate                           # Exit venv

# Troubleshooting
rmdir /s /q venv                     # Delete venv
setup.bat                            # Recreate
```

---

**You're all set!** Start with `run.bat status` and explore the system. 🎉

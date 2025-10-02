# New Commands: Tasks 3 & 4

## Quick Reference

### Learning Commands

```bash
# Learn from feedback
python main.py learn-from-feedback <analysis.md> <feedback.md>

# Show learned insights
python main.py show-insights [--type <type>] [--search <term>]
```

### Smart Analysis Commands

```bash
# Smart analysis with relationship mapping
python main.py analyze <target> --smart [--diagram]

# Compare legacy vs Laravel
python main.py compare <feature> --smart

# Plan new feature or enhancement
python main.py feature "<description>" --type <new|enhance>

# Generate dependency graph
python main.py graph <target> --format <mermaid|ascii|json>

# Track feature progress
python main.py progress <feature>
```

---

## Command Details

### `learn-from-feedback`

**Syntax:**
```bash
python main.py learn-from-feedback <analysis_file> <feedback_file>
```

**Example:**
```bash
python main.py learn-from-feedback claude_context.md feedback.md
```

**What it does:**
- Extracts migration patterns (legacy → modern)
- Stores code transformations
- Learns security improvements
- Identifies architecture patterns
- Builds searchable knowledge base

**Output:**
```
Patterns learned: 5
Insights gained: 12
Transformations found: 3
Strategies identified: 1
```

---

### `show-insights`

**Syntax:**
```bash
python main.py show-insights [options]
```

**Options:**
- `--type <type>` - Filter by type (migration_patterns, security, etc.)
- `--search <term>` - Search for specific term
- `--limit <n>` - Number of results (default: 10)

**Examples:**
```bash
# Show all insights
python main.py show-insights

# Filter by type
python main.py show-insights --type migration_patterns

# Search for term
python main.py show-insights --search "ajax"

# Show more results
python main.py show-insights --limit 20
```

**Output:**
- Table of insights with confidence scores
- Migration patterns with before/after examples
- Success counts and categories

---

### `analyze` (Enhanced)

**Syntax:**
```bash
python main.py analyze <target> [options]
```

**New Options:**
- `--smart` - Enable intelligent relationship following
- `--type <type>` - file, route, feature, module
- `--depth <n>` - How deep to follow relationships (1-5)
- `--focus <area>` - migration, security, architecture, all
- `--diagram` - Generate flow diagrams
- `--format <fmt>` - mermaid, ascii, both (for diagrams)

**Examples:**
```bash
# Smart analysis of PHP file
python main.py analyze core/cyclecount.php --smart

# Laravel route analysis
python main.py analyze warehouse/cycle-count --type route --smart

# With flow diagrams
python main.py analyze cyclecount.php --smart --diagram

# Deep analysis with security focus
python main.py analyze file.php --smart --depth 5 --focus security
```

**Output:**
- `claude_context.md` with complete feature analysis
- File relationship map
- Database tables used
- Flow diagrams (if --diagram)
- Smart suggestions based on patterns

**What it analyzes for PHP:**
- Main file
- All included files (require/include)
- AJAX endpoints and their PHP files
- JavaScript files used
- Form submission targets
- Database queries and tables

**What it analyzes for Laravel:**
- Route definition
- Controller and method
- Models used (Eloquent)
- Services/repositories
- Vue components rendered
- All API calls from Vue
- Middleware and policies

---

### `compare`

**Syntax:**
```bash
python main.py compare <feature_name> [options]
```

**Options:**
- `--smart` - Include full context analysis
- `--output <file>` - Output file (default: comparison_<feature>.md)

**Example:**
```bash
python main.py compare cyclecount --smart
```

**Output:**
- `comparison_cyclecount.md` with:
  - Legacy implementation details
  - Laravel implementation details
  - Side-by-side comparison
  - Migration status checklist

---

### `feature`

**Syntax:**
```bash
python main.py feature "<description>" [options]
```

**Options:**
- `--type <type>` - new or enhance (default: new)
- `--suggestion <text>` - Enhancement suggestion (for type=enhance)
- `--output <file>` - Output file

**Examples:**
```bash
# Plan new feature
python main.py feature "barcode scanning integration" --type new

# Plan enhancement
python main.py feature "orders" --type enhance --suggestion "add bulk delete"
```

**Output:**
- Feature plan markdown file with:
  - Implementation checklist
  - Recommended patterns from knowledge base
  - Estimated complexity
  - Similar existing features
  - Required changes

---

### `graph`

**Syntax:**
```bash
python main.py graph <target> [options]
```

**Options:**
- `--format <fmt>` - mermaid, ascii, json (default: ascii)
- `--output <file>` - Output file

**Examples:**
```bash
# ASCII tree (default)
python main.py graph cyclecount.php

# Mermaid diagram
python main.py graph cyclecount.php --format mermaid

# JSON export
python main.py graph cyclecount.php --format json --output graph.json
```

**Output:**
- Dependency graph visualization
- File relationships
- Database table usage

---

### `progress`

**Syntax:**
```bash
python main.py progress <feature_name>
```

**Example:**
```bash
python main.py progress cyclecount
```

**Output:**
```
╔════════════════════════════════════════════╗
║  Feature Progress: cyclecount              ║
╚════════════════════════════════════════════╝

Analysis: ✅ Complete
Migration Status: 🟡 In Progress

Components:
  ✅ Database schema migrated
  ✅ Backend API created
  🟡 Frontend partially migrated (60%)
  ❌ Excel export not implemented
```

---

## Complete Workflow Example

### Analyze → Learn → Apply Pattern

```bash
# Step 1: Analyze feature with smart context
python main.py analyze core/cyclecount.php --smart --diagram

# Step 2: Review analysis
# Open claude_context.md

# Step 3: Provide feedback
# Create feedback.md with your insights

# Step 4: Learn from feedback
python main.py learn-from-feedback claude_context.md feedback.md

# Step 5: View learned patterns
python main.py show-insights

# Step 6: Compare with Laravel (if exists)
python main.py compare cyclecount --smart

# Step 7: Use patterns for next feature
python main.py analyze core/nextfeature.php --smart
# Now gets smart suggestions based on learned patterns!
```

---

## Key Features

### 🧠 Smart Analysis
- Follows file relationships automatically
- Discovers complete feature stacks
- Identifies all dependencies
- Tracks database usage

### 📚 Pattern Learning
- Learns from your feedback
- Builds confidence scores
- Suggests relevant patterns
- Improves over time

### 📊 Flow Visualization
- Mermaid diagrams for docs
- ASCII diagrams for terminal
- Feature flow layers
- Dependency trees

### 🎯 Intelligent Suggestions
- Based on code similarity
- Confidence scoring
- Success rate tracking
- Context-aware recommendations

---

## Files Generated

| Command | Default Output | Content |
|---------|---------------|---------|
| `analyze --smart` | `claude_context.md` | Complete analysis with relationships |
| `compare` | `comparison_<feature>.md` | Before/after comparison |
| `feature` | `feature_plan_<name>.md` | Implementation plan |
| `graph` | Terminal output | Dependency visualization |
| `learn-from-feedback` | N/A (updates DB) | Stores in knowledge/ directory |

---

## Knowledge Storage

### `knowledge/patterns.json`
- Migration patterns with confidence scores
- Success/failure counts
- Related files
- Categories

### `knowledge/learned_insights.db` (SQLite)
- Insights table
- Code transformations
- Migration strategies
- Feedback sessions

---

## Getting Started

1. **Run first analysis:**
   ```bash
   python main.py analyze core/yourfile.php --smart --diagram
   ```

2. **Create feedback:**
   - Copy `examples/sample_feedback.md`
   - Customize with your insights

3. **Learn from feedback:**
   ```bash
   python main.py learn-from-feedback analysis.md feedback.md
   ```

4. **Use insights:**
   ```bash
   python main.py show-insights
   ```

5. **Get smart suggestions:**
   - Next analysis will include pattern-based suggestions!

---

## Documentation

- **QUICK_START.md** - Get started in 5 minutes
- **TASKS_3_4_GUIDE.md** - Complete documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical details
- **examples/sample_feedback.md** - Feedback template

---

## Support

```bash
# Command help
python main.py <command> --help

# Example
python main.py analyze --help
```

**Happy analyzing! 🚀**

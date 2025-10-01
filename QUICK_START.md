# Quick Start: Tasks 3 & 4

Get started with the feedback learning system and smart contextual analysis in 5 minutes.

## Prerequisites

```bash
cd .agent
pip install -r requirements.txt
```

## Step 1: Test the System (30 seconds)

```bash
# Check system status
python main.py status

# View available commands
python main.py --help
```

## Step 2: Run Your First Smart Analysis (2 minutes)

```bash
# Analyze a legacy PHP file with smart context
python main.py analyze core/cyclecount.php --smart --diagram

# This creates: claude_context.md
```

**What you get:**
- Complete file relationship map
- All included files analyzed
- AJAX endpoints discovered
- Database tables identified
- Flow diagrams (Mermaid + ASCII)
- Smart suggestions based on learned patterns

## Step 3: Learn from Feedback (1 minute)

```bash
# Use sample feedback to build initial knowledge base
python main.py learn-from-feedback \
    claude_context.md \
    examples/sample_feedback.md

# View what was learned
python main.py show-insights
```

**What happens:**
- Extracts migration patterns
- Stores code transformations
- Builds confidence scores
- Creates searchable knowledge base

## Step 4: Compare Implementations (1 minute)

```bash
# Compare legacy vs Laravel
python main.py compare cyclecount --smart

# This creates: comparison_cyclecount.md
```

**What you get:**
- Side-by-side architecture comparison
- Files involved in each implementation
- Database table usage
- API/AJAX endpoint counts
- Migration status checklist

## Step 5: Plan a New Feature (30 seconds)

```bash
# Plan a new feature
python main.py feature "mobile barcode scanning" --type new

# This creates: feature_plan_mobile_barcode_scanning.md
```

**What you get:**
- Recommended patterns from knowledge base
- Implementation checklist
- Estimated complexity
- Similar existing features to learn from

---

## Real-World Workflow

### Scenario: Migrate "Orders" Feature

```bash
# 1. Analyze legacy implementation
python main.py analyze core/orders.php --smart --diagram \
    -o analysis_orders.md

# 2. Compare with Laravel (if partially done)
python main.py compare orders --smart \
    -o comparison_orders.md

# 3. Review analysis files
# Open analysis_orders.md in Claude Code
# Review comparison_orders.md

# 4. Create feedback based on findings
# Copy examples/sample_feedback.md
# Customize for orders feature

# 5. Learn from your feedback
python main.py learn-from-feedback \
    analysis_orders.md \
    feedback_orders.md

# 6. View updated insights
python main.py show-insights --search "orders"

# 7. Generate dependency graph
python main.py graph orders.php --format mermaid \
    -o orders_dependencies.md

# 8. Track progress
python main.py progress orders
```

---

## Command Cheat Sheet

### Analysis Commands

```bash
# Smart analysis
python main.py analyze <file> --smart

# With diagrams
python main.py analyze <file> --smart --diagram

# Laravel route analysis
python main.py analyze <route> --type route --smart

# Deep analysis (depth 5)
python main.py analyze <file> --smart --depth 5

# Security-focused
python main.py analyze <file> --smart --focus security
```

### Learning Commands

```bash
# Learn from feedback
python main.py learn-from-feedback <analysis> <feedback>

# Show all insights
python main.py show-insights

# Filter by type
python main.py show-insights --type migration_patterns

# Search insights
python main.py show-insights --search "ajax"

# Show more results
python main.py show-insights --limit 20
```

### Planning Commands

```bash
# Compare features
python main.py compare <feature> --smart

# Plan new feature
python main.py feature "<description>" --type new

# Plan enhancement
python main.py feature "<feature>" --type enhance \
    --suggestion "<improvement>"

# Generate graph
python main.py graph <file> --format mermaid

# Track progress
python main.py progress <feature>
```

---

## Output Files Reference

| Command | Default Output | Purpose |
|---------|---------------|---------|
| `analyze --smart` | `claude_context.md` | Complete feature analysis |
| `compare` | `comparison_<feature>.md` | Before/after comparison |
| `feature` | `feature_plan_<name>.md` | Implementation plan |
| `graph` | Terminal output | Dependency visualization |

---

## Tips for Success

### 1. Start with Sample Feedback

Use `examples/sample_feedback.md` as a template for your own feedback:

```bash
# Copy and customize
cp examples/sample_feedback.md feedback_myfeature.md
# Edit feedback_myfeature.md with your insights

# Learn from it
python main.py learn-from-feedback analysis.md feedback_myfeature.md
```

### 2. Build Knowledge Incrementally

```bash
# Analyze multiple features
for feature in cyclecount inventory orders; do
    python main.py analyze core/${feature}.php --smart \
        -o analysis_${feature}.md
done

# Provide feedback for each
# Then learn from all of them
for feature in cyclecount inventory orders; do
    python main.py learn-from-feedback \
        analysis_${feature}.md \
        feedback_${feature}.md
done

# Now you have a rich knowledge base!
python main.py show-insights
```

### 3. Use Smart Suggestions

After building knowledge base, the system provides smart suggestions:

```bash
# Analyze new file
python main.py analyze core/newfeature.php --smart

# Check claude_context.md for "Smart Suggestions" section
# It will show relevant patterns based on similar code
```

### 4. Leverage Flow Diagrams

Flow diagrams help understand complex features:

```bash
# Generate Mermaid for GitHub/docs
python main.py analyze <file> --smart --diagram --format mermaid

# Generate ASCII for terminal/quick view
python main.py graph <file> --format ascii

# Both formats
python main.py analyze <file> --smart --diagram --format both
```

### 5. Track Migration Progress

```bash
# Before migration
python main.py progress myfeature
# Shows: ❌ All components pending

# During migration
python main.py progress myfeature
# Shows: 🟡 Some components complete

# After migration
python main.py progress myfeature
# Shows: ✅ All components migrated
```

---

## Common Questions

### Q: What if I don't have feedback yet?

**A:** Start with the sample feedback to build initial knowledge:

```bash
python main.py learn-from-feedback \
    analysis.md \
    examples/sample_feedback.md
```

Then create your own feedback as you work.

### Q: How does smart analysis differ from regular analysis?

**A:** Smart analysis:
- Follows file relationships (includes, AJAX, routes)
- Analyzes complete feature stacks
- Provides pattern-based suggestions
- Generates flow diagrams
- Tracks database usage across files

Regular analysis only examines a single file.

### Q: Can I analyze Laravel routes?

**A:** Yes! Use `--type route`:

```bash
python main.py analyze warehouse/cycle-count --type route --smart
```

This analyzes:
- Route definition
- Controller and method
- Models used
- Vue components
- All API calls
- Complete stack

### Q: How do insights improve over time?

**A:** As you provide feedback:
1. Patterns gain confidence scores
2. Success counts increase for working patterns
3. Transformations are stored with success rates
4. Similar code triggers relevant suggestions

The more feedback, the better the recommendations!

### Q: Can I export graphs for documentation?

**A:** Yes:

```bash
# Mermaid (for GitHub, GitLab, Notion)
python main.py graph file.php --format mermaid -o diagram.md

# JSON (for programmatic use)
python main.py graph file.php --format json -o graph.json

# ASCII (for terminal/plain text)
python main.py graph file.php --format ascii -o tree.txt
```

---

## Next Steps

1. **Run the examples above** to get familiar with commands

2. **Analyze your first feature:**
   ```bash
   python main.py analyze core/<yourfile>.php --smart --diagram
   ```

3. **Create feedback** based on sample format

4. **Learn from feedback:**
   ```bash
   python main.py learn-from-feedback analysis.md feedback.md
   ```

5. **Use insights** for future migrations:
   ```bash
   python main.py show-insights
   ```

6. **Read full guide:**
   - `TASKS_3_4_GUIDE.md` - Complete documentation
   - `examples/sample_feedback.md` - Feedback template

---

## Troubleshooting

### Command not found

Make sure you're in the `.agent` directory:
```bash
cd .agent
python main.py --help
```

### No insights shown

Build knowledge base first:
```bash
python main.py learn-from-feedback \
    examples/sample_analysis.md \
    examples/sample_feedback.md
```

### Permission errors

Check file permissions:
```bash
chmod +x main.py
```

---

## Support

- **Full Guide:** `TASKS_3_4_GUIDE.md`
- **Examples:** `examples/` directory
- **Command Help:** `python main.py <command> --help`

**Have fun analyzing and migrating! 🚀**

# Database Analysis Guide

## Overview

The Migration Analysis System includes a dedicated **Database Agent** that can analyze:
- Laravel migration files
- SQL schema files
- Database table relationships
- Migration safety and rollback operations
- Data loss risks

## ✅ Working Commands

### 1. Analyze Laravel Migration Files

**Basic migration analysis:**
```powershell
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database
```

**Save to file with JSON format:**
```powershell
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --format json --output users_migration_analysis.json
```

**Detailed markdown format:**
```powershell
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --format markdown --output users_migration.md
```

**Brief summary:**
```powershell
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --format brief
```

### 2. Analyze SQL Schema Files

**If you have a SQL dump file:**
```powershell
.\run.ps1 analyze-file path/to/schema.sql --agent database --format markdown --output schema_analysis.md
```

**Example with database dump:**
```powershell
.\run.ps1 analyze-file ../database/dump.sql --agent database --output db_structure.md
```

### 3. Analyze Multiple Migrations

**Analyze all user-related migrations:**
```powershell
# First migration
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --output migration_1.md

# Second migration
.\run.ps1 analyze-file ../laravel/database/migrations/2022_03_05_041643_create_ebay_api_logs_table.php --agent database --output migration_2.md
```

## What Database Analysis Provides

### ✅ Migration Analysis

When analyzing Laravel migration files, you get:

1. **Migration Type**
   - `create_table` - Creates a new table
   - `alter_table` - Modifies existing table
   - `drop_table` - Removes a table
   - `add_column` - Adds new column(s)
   - `modify_column` - Changes column definition

2. **Operations Detected**
   ```json
   {
     "operations": [
       {
         "operation": "create_table",
         "table": "users"
       }
     ]
   }
   ```

3. **Safety Analysis**
   - Risk level: `low`, `medium`, `high`, `critical`
   - Potential issues
   - Safety recommendations
   - Rollback requirements

4. **Data Loss Check**
   - Has data loss risk: `true/false`
   - Risky operations list
   - Prevention strategies

5. **Rollback Analysis**
   - Has rollback: `true/false`
   - Rollback safety
   - Rollback issues
   - Rollback recommendations

6. **Dependency Analysis**
   - Table dependencies
   - Execution order
   - Dependency conflicts
   - Prerequisites

### ✅ SQL Schema Analysis

When analyzing SQL files, you get:

1. **Table Structure**
   - All tables defined
   - Columns and data types
   - Primary keys
   - Foreign keys

2. **Relationships**
   - Table dependencies
   - Foreign key relationships
   - Index definitions

3. **Schema Integrity**
   - Missing indexes
   - Orphaned foreign keys
   - Data type inconsistencies

## Example: Analyzing Users Table Migration

### Command:
```powershell
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --format json --output users_analysis.json
```

### Output (JSON format):
```json
{
  "file_path": "../laravel/database/migrations/2014_10_12_000000_create_users_table.php",
  "parsed": true,
  "type": "laravel_migration",
  "operations": [
    {
      "operation": "create_table",
      "table": "users"
    }
  ],
  "migration_type": "create_table",
  "class_name": "CreateUsersTable",
  "safety_analysis": {
    "risk_level": "low",
    "potential_issues": [],
    "safety_recommendations": []
  },
  "data_loss_check": {
    "has_data_loss_risk": false,
    "risky_operations": []
  },
  "rollback_analysis": {
    "has_rollback": true,
    "rollback_safety": "unknown"
  },
  "dependency_analysis": {
    "table_dependencies": [],
    "execution_order": []
  }
}
```

## Available Output Formats

### 1. JSON (Default)
Best for programmatic processing and detailed analysis.
```powershell
--format json
```

### 2. Markdown
Human-readable report format.
```powershell
--format markdown
```

### 3. Brief
Quick summary of key findings.
```powershell
--format brief
```

### 4. Detailed
Comprehensive analysis with all details.
```powershell
--format detailed
```

### 5. Claude Summary
Optimized for AI analysis and review.
```powershell
--format claude-summary
```

## Common Use Cases

### Use Case 1: Audit All Migrations

**Check safety of all migrations before deployment:**
```powershell
# Create a script to analyze all migrations
$migrations = Get-ChildItem ../laravel/database/migrations/*.php

foreach ($migration in $migrations) {
    $output = "migration_analysis_$($migration.BaseName).json"
    .\run.ps1 analyze-file $migration.FullName --agent database --format json --output $output
    Write-Host "Analyzed: $($migration.Name)"
}
```

### Use Case 2: Find Risky Migrations

**Identify migrations with data loss risks:**
```powershell
# Analyze and check for risks
.\run.ps1 analyze-file ../laravel/database/migrations/some_migration.php --agent database --format json | ConvertFrom-Json | Select-Object -ExpandProperty data_loss_check
```

### Use Case 3: Compare Schema Changes

**Compare old vs new schema:**
```powershell
# Analyze old schema
.\run.ps1 analyze-file old_schema.sql --agent database --output old_schema_analysis.md

# Analyze new migration
.\run.ps1 analyze-file new_migration.php --agent database --output new_migration_analysis.md

# Manually compare the outputs
```

### Use Case 4: Validate Rollback Safety

**Ensure migrations can be safely rolled back:**
```powershell
# Check rollback for a migration
.\run.ps1 analyze-file ../laravel/database/migrations/critical_migration.php --agent database --format json --output rollback_check.json

# Look for rollback_analysis section
```

## Database Tables in Route Analysis

When you analyze routes, the system automatically extracts database tables used:

```powershell
.\run.ps1 analyze warehouse/cycle-count --type route --smart --output cycle_count.md
```

**Output includes:**
```markdown
## Database Tables

- users
- IP_address
- User_IP_Tracking
- users_deparments
```

This shows which tables are accessed by the route!

## Tips and Best Practices

### 1. **Always Check Safety First**
Before running migrations in production:
```powershell
.\run.ps1 analyze-file path/to/migration.php --agent database --format json
# Review safety_analysis and data_loss_check
```

### 2. **Use JSON for Automation**
For scripts and CI/CD pipelines:
```powershell
--format json --output analysis.json
```

### 3. **Use Markdown for Documentation**
For team reviews and documentation:
```powershell
--format markdown --output migration_review.md
```

### 4. **Analyze Before Deployment**
Create a pre-deployment checklist:
```powershell
# 1. Analyze migration
.\run.ps1 analyze-file new_migration.php --agent database --output pre_deploy.md

# 2. Review safety analysis
# 3. Test rollback
# 4. Deploy to staging
# 5. Validate
```

### 5. **Track Table Dependencies**
Understand execution order:
```powershell
# Check dependency_analysis section in output
# Ensures migrations run in correct order
```

## Troubleshooting

### Issue: "No such column: agent_name"
This is a known issue with the find-entity command for tables. Use direct migration analysis instead:
```powershell
# Instead of: find-entity users --type table
# Use: analyze-file on the migration file directly
.\run.ps1 analyze-file ../laravel/database/migrations/*_create_users_table.php --agent database
```

### Issue: Empty Analysis Output
Ensure you're using the correct agent:
```powershell
# Always specify --agent database for database files
.\run.ps1 analyze-file migration.php --agent database
```

### Issue: JSON Format Not Readable
Use markdown format for human reading:
```powershell
--format markdown --output readable_output.md
```

## Migration File Locations

**Laravel migrations:**
```
../laravel/database/migrations/
├── 2014_10_12_000000_create_users_table.php
├── 2014_10_12_100000_create_password_resets_table.php
├── 2019_08_19_000000_create_failed_jobs_table.php
└── ... (other migrations)
```

**To list all migrations:**
```powershell
ls ../laravel/database/migrations/*.php
```

## Direct Database Analysis (NEW!)

### ✅ Analyze Live MySQL Database

**For projects with many tables without migrations** (e.g., 250+ tables with only 5 migrations):

**IMPORTANT:** Since MySQL runs in Docker and is only accessible from within the Docker network, you must run these commands from inside the `brisco-agent` container.

### 1. Basic Database Analysis

**Analyze entire database** (all tables with schemas):
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco
```

**Analyze specific table**:
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --table product
```

**Search for tables by pattern**:
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --search "user"
```

### 2. Connection Details

**Connection settings for Docker MySQL:**
- **Host:** `mysql` (Docker service name, not `localhost`)
- **Port:** `3306` (default)
- **Database:** `brisco`
- **User:** `brisco`
- **Password:** `brisco`

**Why Docker commands?**
The MySQL server runs inside Docker on the `internal` network without exposed ports. Only containers on the same network (like `brisco-agent`) can access it directly.

### 3. Output Formats

**Summary format** (default - human-readable):
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco
```

**JSON format** (for programmatic processing):
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --format json --output /workspace/schema.json
```

**Markdown format** (for documentation):
```powershell
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --format markdown --output /workspace/schema.md
```

**Note:** Output files are saved inside the container at `/workspace/` which maps to your project root `C:\MAMP\htdocs\br\`

### 4. What You Get

**Database Summary**:
- Total tables count
- Total columns across all tables
- Total indexes
- Total foreign keys
- Tables with/without primary keys
- Complete table list

**For Each Table**:
- All columns with types, nullable, defaults
- Primary key information
- All indexes (with unique constraint status)
- All foreign key relationships
- Table comments (if any)

**Relationship Analysis**:
- Complete foreign key relationship map
- From/to table connections
- ON DELETE and ON UPDATE actions

### Example Output

```
DATABASE: brisco
Total Tables: 250+
Total Columns: 2,500+
Total Indexes: 400+
Total Foreign Keys: 50+

TABLE: product (Example)
Columns: 336
Indexes: 31
Foreign Keys: 0

Sample Columns:
├─ id (INTEGER) - Primary Key
├─ ProductID (VARCHAR(100)) - Nullable
├─ QTY (INTEGER) - Not Null, Default '0'
├─ Garment_Style (VARCHAR(100)) - Nullable
├─ Garment_Color (VARCHAR(100)) - Nullable
├─ Garment_Size (VARCHAR(50)) - Nullable
├─ Cust_Price (FLOAT) - Nullable
├─ Sale_Price (FLOAT) - Nullable
├─ Brand (ENUM) - Nullable
├─ Product_Name (VARCHAR(80)) - Nullable
└─ ... (326 more columns)

Indexes: 31 total
Foreign Keys: None
```

## Summary

### ✅ Working Features:
- ✅ Laravel migration analysis
- ✅ SQL schema file analysis
- ✅ **Direct MySQL database connection and analysis (NEW!)**
- ✅ **Live schema extraction for 250+ tables (NEW!)**
- ✅ Safety and risk assessment
- ✅ Rollback analysis
- ✅ Dependency detection
- ✅ Multiple output formats
- ✅ Database tables in route analysis

### ⚠️ Known Limitations:
- `find-entity --type table` has database errors (use direct file analysis instead)
- Markdown output may show escaped newlines (use JSON or brief instead)

### 🎯 Quick Test Commands:

```powershell
# Test 1: Analyze users migration
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database

# Test 2: Get JSON output
.\run.ps1 analyze-file ../laravel/database/migrations/2014_10_12_000000_create_users_table.php --agent database --format json --output test.json

# Test 3: Analyze route and see database tables
.\run.ps1 analyze warehouse/cycle-count --type route --smart --output route_db.md
# Check "Database Tables" section in output

# Test 4: Direct database analysis (NEW!)
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco

# Test 5: Analyze specific table (NEW!)
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --table product --format json

# Test 6: Search tables by pattern (NEW!)
docker exec brisco-agent python /workspace/.agent/main.py analyze-database --host mysql --database brisco --user brisco --password brisco --search "order" --output /workspace/order_tables.md
```

---

**Database analysis is fully functional!** ✅

Use it to:
- Analyze Laravel migration files for safety and rollback analysis
- **Connect directly to MySQL and analyze 250+ tables without migrations (via Docker)**
- Understand complete database schema structure
- Extract foreign key relationships
- Generate database documentation

**Docker Setup:**
The `brisco-agent` container has all dependencies installed and can access the MySQL database on the internal Docker network. All database analysis commands must be run through this container using `docker exec`.

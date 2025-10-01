# Usage Examples for PHP-to-Laravel Migration Analysis System

This document provides comprehensive examples of how to use the migration analysis system for various scenarios in your PHP-to-Laravel migration project.

## Quick Start Examples

### 1. System Health Check
```bash
# Check if everything is configured correctly
python main.py status

# Expected output:
# System Status
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃                                Configuration                                 ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
# ┃ Setting      ┃ Value                              ┃
# ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ Project Name │ PHP-to-Laravel Migration          │
# │ Root Path    │ C:/MAMP/htdocs/br                  │
# │ Core Path    │ C:/MAMP/htdocs/br/core             │
# │ Laravel Path │ C:/MAMP/htdocs/br/laravel          │
# └──────────────┴────────────────────────────────────┘
```

### 2. Quick File Analysis
```bash
# Analyze a specific core PHP file
python main.py analyze-file C:/MAMP/htdocs/br/core/controllers/UserController.php

# Analyze with verbose output for more details
python main.py analyze-file core/auth/LoginController.php --verbose

# Use a specific agent instead of auto-detection
python main.py analyze-file core/models/User.php --agent php
```

### 3. Save Analysis Results
```bash
# Save analysis to JSON file for later review
python main.py analyze-file core/api/orders.php --output analysis_orders.json

# Analyze and save Laravel file
python main.py analyze-file laravel/app/Http/Controllers/OrderController.php --output laravel_orders.json
```

## Comprehensive Analysis Examples

### 4. Module-Level Analysis
```bash
# Analyze entire core authentication module
python main.py analyze-module C:/MAMP/htdocs/br/core/auth

# Analyze Laravel models directory
python main.py analyze-module C:/MAMP/htdocs/br/laravel/app/Models

# Get summary-only view for large modules
python main.py analyze-module core/ --summary

# Save comprehensive module analysis
python main.py analyze-module laravel/app --output laravel_app_analysis.json
```

### 5. Cross-System Analysis
```bash
# Generate comprehensive migration report
python main.py generate-report --scope all --output complete_migration_report.json

# Core-only analysis
python main.py generate-report --scope core --output core_analysis.json

# Laravel-only analysis
python main.py generate-report --scope laravel --output laravel_analysis.json
```

## Specific Use Cases

### 6. Security Audit Workflow
```bash
# Step 1: Check overall security status
python main.py generate-report --scope all | grep -i security

# Step 2: Analyze high-risk authentication files
python main.py analyze-file core/auth/login.php --verbose
python main.py analyze-file core/auth/session.php --verbose

# Step 3: Check Laravel security implementation
python main.py analyze-file laravel/app/Http/Controllers/Auth/LoginController.php --verbose

# Step 4: Review security insights from knowledge base
python main.py show-insights --type security_issues --limit 20

# Step 5: Generate security-focused report
python main.py generate-report --scope all --output security_audit_report.json
```

### 7. Database Migration Analysis
```bash
# Analyze database schema files
python main.py analyze-file database/schema.sql --agent database

# Check Laravel migration files
python main.py analyze-module laravel/database/migrations

# Analyze specific migration
python main.py analyze-file laravel/database/migrations/2024_01_01_000000_create_users_table.php
```

### 8. API Migration Tracking
```bash
# Find all API-related files in core
python main.py find-entity api --type function

# Analyze core API implementation
python main.py analyze-module core/api

# Check Laravel API controllers
python main.py analyze-module laravel/app/Http/Controllers/Api

# Generate API-focused migration report
python main.py generate-report --scope all --output api_migration_report.json
```

### 9. Frontend Migration Analysis
```bash
# Analyze Vue components
python main.py analyze-file laravel/resources/js/components/UserProfile.vue

# Analyze entire frontend directory
python main.py analyze-module laravel/resources/js

# Check Blade templates
python main.py analyze-module laravel/resources/views
```

## Advanced Examples

### 10. Pattern-Based Analysis
```bash
# Find all instances of specific patterns
python main.py find-entity UserController --type class

# Search for database tables
python main.py find-entity users --type table

# Find Vue components
python main.py find-entity LoginForm --type component

# Search for specific functions across codebase
python main.py find-entity authenticate --type function
```

### 11. Knowledge Base Exploration
```bash
# View all learned insights
python main.py show-insights

# Filter by specific types
python main.py show-insights --type migration_status --limit 10
python main.py show-insights --type security_critical --limit 15
python main.py show-insights --type cross_references --limit 25

# View recent insights only
python main.py show-insights --limit 50
```

### 12. Batch Analysis Workflow
```bash
#!/bin/bash
# analyze_project.sh - Comprehensive project analysis script

echo "Starting comprehensive migration analysis..."

# 1. System check
echo "=== System Status ==="
python main.py status

# 2. Analyze critical core modules
echo "=== Core Authentication Analysis ==="
python main.py analyze-module core/auth --output core_auth_analysis.json

echo "=== Core API Analysis ==="
python main.py analyze-module core/api --output core_api_analysis.json

echo "=== Core Models Analysis ==="
python main.py analyze-module core/models --output core_models_analysis.json

# 3. Analyze Laravel implementation
echo "=== Laravel Controllers Analysis ==="
python main.py analyze-module laravel/app/Http/Controllers --output laravel_controllers_analysis.json

echo "=== Laravel Models Analysis ==="
python main.py analyze-module laravel/app/Models --output laravel_models_analysis.json

echo "=== Vue Components Analysis ==="
python main.py analyze-module laravel/resources/js --output vue_components_analysis.json

# 4. Database analysis
echo "=== Database Migration Analysis ==="
python main.py analyze-module laravel/database/migrations --output database_migrations_analysis.json

# 5. Generate comprehensive report
echo "=== Generating Final Report ==="
python main.py generate-report --scope all --output final_migration_report.json

echo "Analysis complete! Check the generated JSON files for detailed results."
```

### 13. CI/CD Integration Example
```bash
#!/bin/bash
# migration_quality_gate.sh - Quality gate for CI/CD pipeline

# Set exit codes
SUCCESS=0
WARNING=1
FAILURE=2

# Generate report
python main.py generate-report --scope all --output ci_report.json

# Check if report was generated successfully
if [ ! -f "ci_report.json" ]; then
    echo "ERROR: Failed to generate analysis report"
    exit $FAILURE
fi

# Extract key metrics (you'd implement proper JSON parsing)
CRITICAL_ISSUES=$(grep -o '"critical_issues":[0-9]*' ci_report.json | cut -d':' -f2)
MIGRATION_SCORE=$(grep -o '"completion_percentage":[0-9.]*' ci_report.json | cut -d':' -f2)

echo "Migration completion: ${MIGRATION_SCORE}%"
echo "Critical issues: ${CRITICAL_ISSUES}"

# Quality gates
if [ "$CRITICAL_ISSUES" -gt "0" ]; then
    echo "FAIL: Critical security issues found"
    exit $FAILURE
fi

if [ "${MIGRATION_SCORE%.*}" -lt "80" ]; then
    echo "WARNING: Migration completion below 80%"
    exit $WARNING
fi

echo "PASS: Migration quality gate passed"
exit $SUCCESS
```

## Troubleshooting Examples

### 14. Debug Analysis Issues
```bash
# Enable verbose output for debugging
python main.py analyze-file problematic_file.php --verbose

# Check specific agent behavior
python main.py analyze-file core/test.php --agent php --verbose
python main.py analyze-file laravel/app/Test.php --agent laravel --verbose

# Verify file paths and permissions
python main.py status
ls -la C:/MAMP/htdocs/br/core/
```

### 15. Performance Analysis
```bash
# Analyze large modules with timing
time python main.py analyze-module core/

# Use summary mode for quick overviews
python main.py analyze-module large_directory/ --summary

# Save intermediate results
python main.py analyze-module core/controllers --output controllers.json
python main.py analyze-module core/models --output models.json
```

## Integration Examples

### 16. Docker Integration
```dockerfile
# Dockerfile for containerized analysis
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set up analysis environment
ENV PYTHONPATH=/app
ENV MIGRATION_CONFIG=/app/config/config.yaml

# Run analysis
CMD ["python", "main.py", "generate-report", "--scope", "all", "--output", "/output/report.json"]
```

```bash
# Build and run analysis container
docker build -t migration-analyzer .
docker run -v /path/to/your/code:/data -v /path/to/output:/output migration-analyzer
```

### 17. Custom Analysis Script
```python
#!/usr/bin/env python3
"""
Custom analysis script for specific migration patterns
"""

import sys
import json
from pathlib import Path

# Add agent path
sys.path.insert(0, str(Path(__file__).parent))

from agents.coordinator_agent import CoordinatorAgent

def analyze_custom_patterns():
    """Run custom analysis patterns."""
    coordinator = CoordinatorAgent("config/config.yaml")

    # Define files to analyze
    critical_files = [
        "core/auth/login.php",
        "core/models/User.php",
        "core/api/auth.php"
    ]

    results = {}

    for file_path in critical_files:
        print(f"Analyzing {file_path}...")
        analysis = coordinator.analyze_file(file_path)

        # Extract security issues
        if analysis.get('patterns', {}).get('security_issues'):
            results[file_path] = {
                'security_issues': analysis['patterns']['security_issues'],
                'migration_priority': analysis.get('migration_recommendations', {}).get('priority')
            }

    # Save custom results
    with open('custom_security_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("Custom analysis complete!")

if __name__ == "__main__":
    analyze_custom_patterns()
```

## Real-World Scenarios

### 18. E-commerce Migration Analysis
```bash
# Analyze core e-commerce modules
python main.py analyze-module core/shopping --output core_shopping.json
python main.py analyze-module core/payments --output core_payments.json
python main.py analyze-module core/orders --output core_orders.json

# Check Laravel equivalents
python main.py analyze-module laravel/app/Http/Controllers/Shop --output laravel_shop.json
python main.py find-entity OrderController

# Database schema analysis
python main.py analyze-file database/ecommerce_schema.sql --agent database

# Generate e-commerce focused report
python main.py generate-report --scope all --output ecommerce_migration_report.json
```

### 19. User Management System Migration
```bash
# Core user system analysis
python main.py analyze-module core/users --verbose
python main.py analyze-file core/auth/permissions.php --verbose

# Laravel authentication analysis
python main.py analyze-module laravel/app/Http/Controllers/Auth
python main.py analyze-file laravel/app/Models/User.php --verbose

# Vue.js frontend analysis
python main.py analyze-file laravel/resources/js/components/UserDashboard.vue
python main.py analyze-module laravel/resources/js/pages/auth

# Cross-system analysis
python main.py find-entity User --type class
python main.py generate-report --scope all --output user_system_report.json
```

### 20. API Migration Validation
```bash
# Analyze core API endpoints
python main.py analyze-module core/api --verbose --output core_api.json

# Check Laravel API implementation
python main.py analyze-module laravel/app/Http/Controllers/Api --output laravel_api.json

# Database API schema
python main.py analyze-module laravel/database/migrations --summary

# Generate API migration report
python main.py generate-report --scope all --output api_migration_validation.json

# Review API-specific insights
python main.py show-insights --type api_integration --limit 30
```

These examples demonstrate the flexibility and power of the migration analysis system. Adapt them to your specific migration needs and project structure.
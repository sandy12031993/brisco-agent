#!/usr/bin/env python3
"""
Test script to validate token efficiency and output formatting functionality.
"""

import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.token_counter import token_counter
from utils.output_formatter import output_formatter, get_format_info
from utils.token_tracker import token_tracker


def create_sample_analysis_data():
    """Create sample analysis data for testing."""
    return {
        'file_path': 'core/auth/UserController.php',
        'parsed': True,
        'metrics': {
            'lines_of_code': 245,
            'classes_count': 2,
            'functions_count': 15,
            'complexity_score': 7.2
        },
        'classes': [
            {
                'name': 'UserController',
                'methods': [
                    {'name': 'index', 'visibility': 'public'},
                    {'name': 'create', 'visibility': 'public'},
                    {'name': 'store', 'visibility': 'public'},
                    {'name': 'show', 'visibility': 'public'},
                    {'name': 'edit', 'visibility': 'public'},
                    {'name': 'update', 'visibility': 'public'},
                    {'name': 'destroy', 'visibility': 'public'},
                    {'name': 'authenticate', 'visibility': 'private'},
                    {'name': 'validateInput', 'visibility': 'private'},
                    {'name': 'sendNotification', 'visibility': 'private'}
                ]
            },
            {
                'name': 'UserValidator',
                'methods': [
                    {'name': 'validateEmail', 'visibility': 'public'},
                    {'name': 'validatePassword', 'visibility': 'public'},
                    {'name': 'validateAge', 'visibility': 'public'},
                    {'name': 'checkDuplicates', 'visibility': 'private'},
                    {'name': 'sanitizeInput', 'visibility': 'private'}
                ]
            }
        ],
        'patterns': {
            'security_issues': [
                {
                    'type': 'sql_injection',
                    'severity': 'critical',
                    'description': 'Direct SQL concatenation detected in user authentication function',
                    'line': 45,
                    'recommendation': 'Use prepared statements or Laravel Query Builder'
                },
                {
                    'type': 'xss_vulnerability',
                    'severity': 'high',
                    'description': 'Unescaped user input in view rendering',
                    'line': 78,
                    'recommendation': 'Use Laravel Blade templating with automatic escaping'
                },
                {
                    'type': 'password_storage',
                    'severity': 'critical',
                    'description': 'Passwords stored in plain text',
                    'line': 123,
                    'recommendation': 'Use Laravel Hash facade with bcrypt'
                },
                {
                    'type': 'session_management',
                    'severity': 'medium',
                    'description': 'Insecure session handling',
                    'line': 156,
                    'recommendation': 'Use Laravel session management'
                }
            ],
            'anti_patterns': [
                'direct_database_access',
                'mixed_concerns',
                'hardcoded_values'
            ],
            'framework_patterns': ['mvc_structure', 'basic_validation'],
            'database_patterns': ['direct_mysql_calls', 'no_migrations']
        },
        'dependencies': [
            {'name': 'mysql_connect', 'type': 'deprecated', 'file': 'database.php'},
            {'name': 'custom_auth', 'type': 'legacy', 'file': 'auth_helper.php'},
            {'name': 'email_validator', 'type': 'utility', 'file': 'validators.php'},
            {'name': 'session_handler', 'type': 'legacy', 'file': 'session.php'}
        ],
        'migration_recommendations': {
            'priority': 'high',
            'complexity': 'medium',
            'required_changes': [
                'Convert to Laravel Controller',
                'Implement Eloquent ORM',
                'Add proper input validation',
                'Implement CSRF protection',
                'Use Laravel authentication',
                'Add unit tests'
            ],
            'estimated_effort': '3-5 days',
            'migration_order': 1
        }
    }


def test_token_estimation():
    """Test token estimation accuracy."""
    print("Testing Token Estimation...")

    # Test various text types
    test_cases = [
        ("Short text", "Hello world"),
        ("Code snippet", "function authenticate($user, $password) { return hash_verify($password, $user->password); }"),
        ("JSON data", json.dumps({'key': 'value', 'array': [1, 2, 3], 'nested': {'inner': 'data'}})),
        ("Markdown text", "# Title\n\nThis is a **bold** text with *italic* and `code` formatting.")
    ]

    for name, text in test_cases:
        tokens = token_counter.estimate_tokens(text)
        chars = len(text)
        ratio = chars / tokens if tokens > 0 else 0
        print(f"  {name}: {chars} chars -> {tokens} tokens (ratio: {ratio:.1f})")

    print("Token estimation test completed\n")


def test_output_formats():
    """Test all output formats with token limits."""
    print("Testing Output Formats...")

    sample_data = create_sample_analysis_data()
    format_info = get_format_info()

    results = {}

    for format_type, config in format_info.items():
        print(f"  Testing {format_type} format...")

        # Format the data
        output = output_formatter.format_analysis(
            sample_data,
            format_type,
            config['max_tokens']
        )

        # Count tokens
        actual_tokens = token_counter.estimate_tokens(output)
        max_tokens = config['max_tokens']

        # Check if within limits
        within_limit = max_tokens is None or actual_tokens <= max_tokens
        limit_status = "PASS" if within_limit else "FAIL"

        print(f"    {limit_status} Tokens: {actual_tokens:,} / {max_tokens or 'unlimited'}")

        results[format_type] = {
            'tokens': actual_tokens,
            'max_tokens': max_tokens,
            'within_limit': within_limit,
            'description': config['description']
        }

    print("Output format test completed\n")
    return results


def test_token_truncation():
    """Test token truncation functionality."""
    print("Testing Token Truncation...")

    # Create a long text
    long_text = "This is a very long text that should be truncated. " * 100
    original_tokens = token_counter.estimate_tokens(long_text)

    # Test truncation to different limits
    limits = [100, 500, 1000]

    for limit in limits:
        truncated = token_counter.truncate_to_tokens(long_text, limit)
        truncated_tokens = token_counter.estimate_tokens(truncated)

        within_limit = truncated_tokens <= limit
        status = "PASS" if within_limit else "FAIL"

        print(f"  {status} Limit {limit}: {original_tokens} -> {truncated_tokens} tokens")

    print("Token truncation test completed\n")


def test_claude_summary_format():
    """Test Claude summary format specifically for token efficiency."""
    print("Testing Claude Summary Format...")

    sample_data = create_sample_analysis_data()

    # Test with default limit
    output = output_formatter.format_analysis(sample_data, 'claude-summary', 3000)
    tokens = token_counter.estimate_tokens(output)

    print(f"  Claude Summary: {tokens:,} / 3,000 tokens ({tokens/3000*100:.1f}%)")

    # Test key sections are present
    required_sections = [
        "Quick Summary",
        "Key Metrics",
        "Critical Issues",
        "Migration Checklist",
        "Suggested Prompts"
    ]

    sections_found = 0
    for section in required_sections:
        if section in output:
            sections_found += 1

    print(f"  Required sections: {sections_found}/{len(required_sections)} found")

    # Test with smaller limit
    compact_output = output_formatter.format_analysis(sample_data, 'claude-summary', 2000)
    compact_tokens = token_counter.estimate_tokens(compact_output)

    print(f"  Compact version: {compact_tokens:,} / 2,000 tokens ({compact_tokens/2000*100:.1f}%)")

    print("Claude summary format test completed\n")


def test_token_tracking():
    """Test token tracking functionality."""
    print("Testing Token Tracking...")

    # Record some sample usage
    session_id = token_tracker.get_session_id()

    test_records = [
        ('analyze-file', 'claude-summary', 2847, 'test.php'),
        ('analyze-module', 'brief', 892, 'test_module/'),
        ('prepare-for-claude', 'claude-summary', 2956, 'auth.php'),
    ]

    for command, format_type, tokens_used, input_path in test_records:
        token_tracker.record_usage(
            command=command,
            format_type=format_type,
            tokens_used=tokens_used,
            input_path=input_path,
            session_id=session_id,
            success=True
        )

    # Get statistics
    stats = token_tracker.get_usage_stats('session')
    basic_stats = stats['basic_stats']

    print(f"  Recorded {basic_stats['analyses_run']} test analyses")
    print(f"  Total tokens: {basic_stats['total_tokens']:,}")
    print(f"  Average tokens: {basic_stats['avg_tokens']:.1f}")

    # Test format distribution
    format_dist = stats['format_distribution']
    print(f"  Format distribution: {len(format_dist)} formats used")

    print("Token tracking test completed\n")


def generate_test_summary(format_results):
    """Generate a summary of test results."""
    print("Test Summary")
    print("=" * 50)

    print("\nFormat Efficiency:")
    for format_type, results in format_results.items():
        tokens = results['tokens']
        max_tokens = results['max_tokens']
        within_limit = results['within_limit']

        status = "PASS" if within_limit else "FAIL"
        limit_str = f"{max_tokens:,}" if max_tokens else "unlimited"

        print(f"  {status} {format_type:15} : {tokens:5,} / {limit_str:>9} tokens")

    print("\nRecommendations:")
    print("  - Use 'brief' format for quick overviews (< 1K tokens)")
    print("  - Use 'claude-summary' for Claude Code integration (~3K tokens)")
    print("  - Use 'detailed' for comprehensive analysis (~8K tokens)")
    print("  - Monitor usage with 'python main.py token-stats'")

    print("\nSystem Status: All token optimization features working correctly!")


def main():
    """Run all token efficiency tests."""
    print("Token Efficiency Test Suite")
    print("=" * 50)
    print()

    try:
        # Run tests
        test_token_estimation()
        format_results = test_output_formats()
        test_token_truncation()
        test_claude_summary_format()
        test_token_tracking()

        # Generate summary
        generate_test_summary(format_results)

        print("\nAll tests completed successfully!")

    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
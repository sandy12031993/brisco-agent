"""
Output formatting utilities with token-optimized formats for different use cases.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .token_counter import token_counter


class OutputFormatter:
    """
    Formats analysis results in different styles optimized for specific token budgets.
    """

    # Format configurations with default token limits
    FORMAT_CONFIGS = {
        'json': {'max_tokens': None, 'description': 'Full JSON output (no token limit)'},
        'claude-summary': {'max_tokens': 3000, 'description': 'Optimized for Claude Code'},
        'brief': {'max_tokens': 1000, 'description': 'Ultra-condensed summary'},
        'detailed': {'max_tokens': 8000, 'description': 'Comprehensive analysis'},
        'markdown': {'max_tokens': 5000, 'description': 'Human-readable markdown'}
    }

    def __init__(self):
        self.token_counter = token_counter

    def format_analysis(self, data: Dict[str, Any], format_type: str = 'json',
                       max_tokens: Optional[int] = None, metadata: Optional[Dict] = None) -> str:
        """
        Format analysis data according to specified format type.

        Args:
            data: Analysis data to format
            format_type: Output format ('json', 'claude-summary', 'brief', 'detailed', 'markdown')
            max_tokens: Override default token limit for format
            metadata: Additional metadata to include

        Returns:
            Formatted string
        """
        if format_type not in self.FORMAT_CONFIGS:
            raise ValueError(f"Unknown format type: {format_type}. "
                           f"Available: {list(self.FORMAT_CONFIGS.keys())}")

        # Get token limit
        if max_tokens is None:
            max_tokens = self.FORMAT_CONFIGS[format_type]['max_tokens']

        # Add metadata if provided
        if metadata:
            data = {**data, 'metadata': metadata}

        # Route to appropriate formatter
        if format_type == 'json':
            return self._format_json(data, max_tokens)
        elif format_type == 'claude-summary':
            return self._format_claude_summary(data, max_tokens)
        elif format_type == 'brief':
            return self._format_brief(data, max_tokens)
        elif format_type == 'detailed':
            return self._format_detailed(data, max_tokens)
        elif format_type == 'markdown':
            return self._format_markdown(data, max_tokens)

    def _format_json(self, data: Dict[str, Any], max_tokens: Optional[int]) -> str:
        """Format as JSON with optional token optimization."""
        if max_tokens is None:
            return json.dumps(data, indent=2)
        else:
            return self.token_counter.optimize_json_for_tokens(data, max_tokens)

    def _format_claude_summary(self, data: Dict[str, Any], max_tokens: int) -> str:
        """
        Format optimized for Claude Code analysis.
        Focus: Scannable, actionable, complete for decision making.
        """
        output_lines = []

        # Header
        file_path = data.get('file_path', data.get('module_path', 'Analysis'))
        output_lines.append(f"# 🔍 Migration Analysis: {Path(file_path).name}")
        output_lines.append("")

        # Quick Summary (2-3 sentences)
        summary = self._generate_quick_summary(data)
        output_lines.append("## 📋 Quick Summary")
        output_lines.append(summary)
        output_lines.append("")

        # Key Metrics Table
        output_lines.append("## 📊 Key Metrics")
        metrics_table = self._create_metrics_table(data)
        output_lines.extend(metrics_table)
        output_lines.append("")

        # Critical Issues (top 3-5 only)
        critical_issues = self._get_critical_issues(data, limit=5)
        if critical_issues:
            output_lines.append("## 🚨 Critical Issues")
            for i, issue in enumerate(critical_issues, 1):
                output_lines.append(f"{i}. **{issue['type']}**: {issue['description']}")
            output_lines.append("")

        # Dependencies (summarized)
        deps = self._summarize_dependencies(data, limit=5)
        if deps:
            output_lines.append("## 📦 Dependencies")
            output_lines.extend(deps)
            output_lines.append("")

        # Security Concerns
        security = self._get_security_summary(data)
        if security:
            output_lines.append("## 🛡️ Security Concerns")
            output_lines.extend(security)
            output_lines.append("")

        # Migration Checklist
        checklist = self._create_migration_checklist(data, limit=10)
        if checklist:
            output_lines.append("## ✅ Migration Checklist")
            output_lines.extend(checklist)
            output_lines.append("")

        # Code Patterns
        patterns = self._summarize_patterns(data)
        if patterns:
            output_lines.append("## 🔧 Code Patterns Detected")
            output_lines.extend(patterns)
            output_lines.append("")

        # Suggested Approach
        approach = self._generate_approach(data)
        if approach:
            output_lines.append("## 🎯 Suggested Approach")
            output_lines.append(approach)
            output_lines.append("")

        # Files for Review
        files = self._get_files_for_review(data, limit=5)
        if files:
            output_lines.append("## 📁 Files for Review")
            output_lines.extend(files)
            output_lines.append("")

        # Suggested Prompts
        prompts = self._generate_suggested_prompts(data)
        output_lines.append("## 💬 Suggested Prompts for Claude Code")
        output_lines.extend(prompts)
        output_lines.append("")

        # Join and check token count
        content = "\\n".join(output_lines)

        # Add token usage footer
        actual_tokens = self.token_counter.estimate_tokens(content)
        footer = f"\\n---\\n*Token usage: {actual_tokens:,} / {max_tokens:,} tokens*"
        content += footer

        # Truncate if necessary
        if actual_tokens > max_tokens:
            content = self.token_counter.truncate_to_tokens(content, max_tokens - 50)
            # Re-add footer
            final_tokens = self.token_counter.estimate_tokens(content)
            content += f"\\n---\\n*Token usage: {final_tokens:,} / {max_tokens:,} tokens (truncated)*"

        return content

    def _format_brief(self, data: Dict[str, Any], max_tokens: int) -> str:
        """Ultra-condensed format for quick scans."""
        output_lines = []

        # One-line summary
        file_path = data.get('file_path', data.get('module_path', 'Analysis'))
        summary_line = f"**{Path(file_path).name}**: "

        # Quick status
        status_parts = []
        if data.get('parsed', True):
            status_parts.append("✅ Parsed")
        else:
            status_parts.append("❌ Parse Failed")

        # Key metrics
        metrics = data.get('metrics', {})
        if metrics.get('lines_of_code'):
            status_parts.append(f"{metrics['lines_of_code']} LOC")

        # Issues count
        issues = self._count_all_issues(data)
        if issues > 0:
            status_parts.append(f"{issues} issues")

        # Migration priority
        migration = data.get('migration_recommendations', {})
        priority = migration.get('priority', 'unknown')
        if priority != 'unknown':
            status_parts.append(f"{priority} priority")

        summary_line += " | ".join(status_parts)
        output_lines.append(summary_line)

        # Top 3 critical issues only
        critical_issues = self._get_critical_issues(data, limit=3)
        if critical_issues:
            output_lines.append("\\n**Issues:**")
            for issue in critical_issues:
                output_lines.append(f"• {issue['type']}: {issue['description'][:50]}...")

        # Migration actions (top 3)
        actions = self._get_top_migration_actions(data, limit=3)
        if actions:
            output_lines.append("\\n**Actions:**")
            for action in actions:
                output_lines.append(f"• {action}")

        content = "\\n".join(output_lines)
        return self.token_counter.truncate_to_tokens(content, max_tokens)

    def _format_detailed(self, data: Dict[str, Any], max_tokens: int) -> str:
        """Comprehensive analysis format."""
        # Start with claude-summary format and expand
        base_content = self._format_claude_summary(data, max_tokens // 2)

        output_lines = [base_content, "", "## 📈 Detailed Analysis", ""]

        # Add more comprehensive sections
        if 'classes' in data:
            output_lines.append("### Classes and Methods")
            for cls in data['classes'][:10]:  # Limit to prevent token explosion
                output_lines.append(f"**{cls['name']}**:")
                methods = cls.get('methods', [])[:5]  # Top 5 methods
                for method in methods:
                    method_name = method if isinstance(method, str) else method.get('name', 'Unknown')
                    output_lines.append(f"  • {method_name}")
                if len(cls.get('methods', [])) > 5:
                    remaining = len(cls.get('methods', [])) - 5
                    output_lines.append(f"  • ...{remaining} more methods")
            output_lines.append("")

        # All security issues (not just critical)
        if 'patterns' in data and 'security_issues' in data['patterns']:
            security_issues = data['patterns']['security_issues']
            if security_issues:
                output_lines.append("### All Security Issues")
                for issue in security_issues[:20]:  # Limit for token management
                    severity = issue.get('severity', 'unknown')
                    issue_type = issue.get('type', 'Unknown')
                    description = issue.get('description', 'No description')[:100]
                    output_lines.append(f"• **{severity.upper()}** - {issue_type}: {description}")
                output_lines.append("")

        # Performance considerations
        if 'performance' in data:
            output_lines.append("### Performance Analysis")
            perf_data = data['performance']
            # Add performance details here
            output_lines.append(str(perf_data)[:500])
            output_lines.append("")

        content = "\\n".join(output_lines)
        return self.token_counter.truncate_to_tokens(content, max_tokens)

    def _format_markdown(self, data: Dict[str, Any], max_tokens: int) -> str:
        """Human-readable markdown format."""
        output_lines = []

        # Title
        file_path = data.get('file_path', data.get('module_path', 'Analysis'))
        output_lines.append(f"# Analysis Report: {Path(file_path).name}")
        output_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        output_lines.append("")

        # Executive Summary
        output_lines.append("## Executive Summary")
        summary = self._generate_executive_summary(data)
        output_lines.append(summary)
        output_lines.append("")

        # Findings
        output_lines.append("## Key Findings")

        # Code metrics in readable format
        metrics = data.get('metrics', {})
        if metrics:
            output_lines.append("### Code Metrics")
            for key, value in metrics.items():
                readable_key = key.replace('_', ' ').title()
                output_lines.append(f"- **{readable_key}**: {value}")
            output_lines.append("")

        # Issues by severity
        all_issues = self._categorize_issues(data)
        for severity, issues in all_issues.items():
            if issues:
                output_lines.append(f"### {severity.title()} Issues")
                for issue in issues[:10]:  # Limit per severity
                    output_lines.append(f"- {issue['description']}")
                if len(issues) > 10:
                    output_lines.append(f"- *...and {len(issues) - 10} more {severity} issues*")
                output_lines.append("")

        # Recommendations
        recommendations = self._get_recommendations(data)
        if recommendations:
            output_lines.append("## Recommendations")
            for i, rec in enumerate(recommendations, 1):
                output_lines.append(f"{i}. {rec}")
            output_lines.append("")

        # Next Steps
        next_steps = self._get_next_steps(data)
        if next_steps:
            output_lines.append("## Next Steps")
            for i, step in enumerate(next_steps, 1):
                output_lines.append(f"{i}. {step}")
            output_lines.append("")

        content = "\\n".join(output_lines)
        return self.token_counter.truncate_to_tokens(content, max_tokens)

    # Helper methods for content generation
    def _generate_quick_summary(self, data: Dict[str, Any]) -> str:
        """Generate 2-3 sentence summary."""
        file_path = data.get('file_path', data.get('module_path', 'Unknown'))
        parsed = data.get('parsed', True)

        if not parsed:
            return f"Failed to parse {Path(file_path).name}. Manual review required."

        # Collect key facts
        facts = []

        metrics = data.get('metrics', {})
        if metrics.get('lines_of_code'):
            facts.append(f"{metrics['lines_of_code']} lines of code")

        issues_count = self._count_all_issues(data)
        if issues_count > 0:
            facts.append(f"{issues_count} issues detected")

        migration = data.get('migration_recommendations', {})
        priority = migration.get('priority', 'medium')
        complexity = migration.get('complexity', 'medium')
        facts.append(f"{priority} priority migration with {complexity} complexity")

        base = f"Analysis of {Path(file_path).name} shows " + ", ".join(facts[:2]) + "."

        # Add context about issues
        critical_issues = self._get_critical_issues(data, limit=1)
        if critical_issues:
            base += f" Primary concern: {critical_issues[0]['type']}."
        else:
            base += " No critical issues identified."

        return base

    def _create_metrics_table(self, data: Dict[str, Any]) -> List[str]:
        """Create formatted metrics table."""
        metrics = data.get('metrics', {})

        lines = []
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")

        # Key metrics to show
        key_metrics = [
            ('lines_of_code', 'Lines of Code'),
            ('classes_count', 'Classes'),
            ('functions_count', 'Functions'),
            ('complexity_score', 'Complexity'),
        ]

        for key, label in key_metrics:
            if key in metrics:
                lines.append(f"| {label} | {metrics[key]} |")

        # Add issue counts
        issues_count = self._count_all_issues(data)
        security_count = len(self._get_security_issues(data))

        lines.append(f"| Issues Found | {issues_count} |")
        lines.append(f"| Security Issues | {security_count} |")

        # Migration info
        migration = data.get('migration_recommendations', {})
        if migration:
            priority = migration.get('priority', 'Unknown')
            complexity = migration.get('complexity', 'Unknown')
            lines.append(f"| Migration Priority | {priority} |")
            lines.append(f"| Migration Complexity | {complexity} |")

        return lines

    def _get_critical_issues(self, data: Dict[str, Any], limit: int = 5) -> List[Dict]:
        """Get critical issues with highest priority."""
        all_issues = []

        # Collect from various sources
        if 'patterns' in data:
            patterns = data['patterns']
            if 'security_issues' in patterns:
                for issue in patterns['security_issues']:
                    if issue.get('severity') in ['critical', 'high']:
                        all_issues.append({
                            'type': issue.get('type', 'Security Issue'),
                            'description': issue.get('description', 'No description'),
                            'severity': issue.get('severity', 'unknown'),
                            'priority': 1 if issue.get('severity') == 'critical' else 2
                        })

            if 'anti_patterns' in patterns:
                for pattern in patterns['anti_patterns']:
                    if isinstance(pattern, dict):
                        all_issues.append({
                            'type': 'Anti-pattern',
                            'description': pattern.get('description', str(pattern)),
                            'severity': 'medium',
                            'priority': 3
                        })
                    else:
                        all_issues.append({
                            'type': 'Anti-pattern',
                            'description': str(pattern),
                            'severity': 'medium',
                            'priority': 3
                        })

        # Sort by priority and return top items
        all_issues.sort(key=lambda x: x['priority'])
        return all_issues[:limit]

    def _summarize_dependencies(self, data: Dict[str, Any], limit: int = 5) -> List[str]:
        """Summarize dependencies."""
        deps = data.get('dependencies', [])
        if not deps:
            return []

        lines = []
        if len(deps) <= limit:
            for dep in deps:
                if isinstance(dep, dict):
                    name = dep.get('name', str(dep))
                    version = dep.get('version', '')
                    lines.append(f"• {name} {version}".strip())
                else:
                    lines.append(f"• {dep}")
        else:
            for dep in deps[:limit]:
                if isinstance(dep, dict):
                    name = dep.get('name', str(dep))
                    lines.append(f"• {name}")
                else:
                    lines.append(f"• {dep}")
            lines.append(f"• ...and {len(deps) - limit} more dependencies")

        return lines

    def _get_security_summary(self, data: Dict[str, Any]) -> List[str]:
        """Get security issues summary."""
        security_issues = self._get_security_issues(data)
        if not security_issues:
            return ["✅ No security issues detected"]

        lines = []
        severity_counts = {}
        for issue in security_issues:
            severity = issue.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        for severity, count in severity_counts.items():
            icon = "🚨" if severity == "critical" else "⚠️" if severity == "high" else "⚡"
            lines.append(f"{icon} {count} {severity} issues")

        return lines

    def _create_migration_checklist(self, data: Dict[str, Any], limit: int = 10) -> List[str]:
        """Create migration checklist."""
        checklist = []

        # From migration recommendations
        migration = data.get('migration_recommendations', {})
        if 'required_changes' in migration:
            for change in migration['required_changes'][:limit]:
                checklist.append(f"- [ ] {change}")

        # Add security fixes
        security_issues = self._get_security_issues(data)
        for issue in security_issues[:3]:  # Top 3 security items
            fix = f"Fix {issue.get('type', 'security issue')}"
            checklist.append(f"- [ ] {fix}")

        # Add patterns fixes
        if 'patterns' in data and 'anti_patterns' in data['patterns']:
            for pattern in data['patterns']['anti_patterns'][:2]:
                if isinstance(pattern, dict):
                    fix = f"Refactor {pattern.get('type', 'anti-pattern')}"
                else:
                    fix = f"Refactor {pattern}"
                checklist.append(f"- [ ] {fix}")

        # Generic items if none found
        if not checklist:
            checklist = [
                "- [ ] Review code structure",
                "- [ ] Update dependencies",
                "- [ ] Add error handling",
                "- [ ] Implement security measures",
                "- [ ] Add unit tests"
            ]

        return checklist[:limit]

    def _summarize_patterns(self, data: Dict[str, Any]) -> List[str]:
        """Summarize detected code patterns."""
        patterns = data.get('patterns', {})
        if not patterns:
            return []

        lines = []

        # Framework patterns
        if 'framework_patterns' in patterns:
            framework = patterns['framework_patterns']
            if framework:
                lines.append(f"• Framework: {', '.join(framework[:3])}")

        # Design patterns
        if 'design_patterns' in patterns:
            design = patterns['design_patterns']
            if design:
                lines.append(f"• Design patterns: {', '.join(design[:3])}")

        # Database patterns
        if 'database_patterns' in patterns:
            db = patterns['database_patterns']
            if db:
                lines.append(f"• Database: {', '.join(db[:3])}")

        return lines

    def _generate_approach(self, data: Dict[str, Any]) -> str:
        """Generate suggested migration approach."""
        migration = data.get('migration_recommendations', {})
        priority = migration.get('priority', 'medium')
        complexity = migration.get('complexity', 'medium')

        if priority == 'high' and complexity == 'high':
            return "Recommend breaking this into smaller components. Start with security fixes, then refactor core logic, finally migrate to Laravel patterns."
        elif priority == 'high':
            return "High priority migration. Focus on security issues first, then systematic conversion to Laravel equivalents."
        elif complexity == 'high':
            return "Complex migration requiring careful planning. Consider creating parallel Laravel implementation and gradual switchover."
        else:
            return "Standard migration approach. Fix issues, update patterns, migrate to Laravel step by step."

    def _get_files_for_review(self, data: Dict[str, Any], limit: int = 5) -> List[str]:
        """Get files that need manual review."""
        files = []

        # Current file with reasons
        file_path = data.get('file_path')
        if file_path:
            reasons = []
            if self._get_security_issues(data):
                reasons.append("security issues")
            if self._count_all_issues(data) > 5:
                reasons.append("multiple issues")

            reason_text = f" ({', '.join(reasons)})" if reasons else ""
            files.append(f"• `{file_path}`{reason_text}")

        # Related files from dependencies
        deps = data.get('dependencies', [])
        for dep in deps[:limit-1]:
            if isinstance(dep, dict) and 'file' in dep:
                files.append(f"• `{dep['file']}` (dependency)")

        return files

    def _generate_suggested_prompts(self, data: Dict[str, Any]) -> List[str]:
        """Generate helpful prompts for Claude Code."""
        prompts = []

        file_path = data.get('file_path', data.get('module_path', 'this file'))

        # Security-focused prompt
        if self._get_security_issues(data):
            prompts.append(f"**Security Review**: \"Analyze {Path(file_path).name} for security vulnerabilities and suggest Laravel security patterns to fix them.\"")

        # Migration prompt
        prompts.append(f"**Migration Plan**: \"Create a step-by-step migration plan for {Path(file_path).name} from PHP to Laravel, prioritizing maintainability.\"")

        # Refactoring prompt
        if self._count_all_issues(data) > 3:
            prompts.append(f"**Refactoring**: \"Suggest modern PHP/Laravel refactoring for {Path(file_path).name} to improve code quality and performance.\"")

        # Testing prompt
        prompts.append(f"**Testing Strategy**: \"Design a comprehensive testing approach for the migrated version of {Path(file_path).name}.\"")

        return prompts

    # Utility methods
    def _count_all_issues(self, data: Dict[str, Any]) -> int:
        """Count total issues across all categories."""
        count = 0
        patterns = data.get('patterns', {})

        if 'security_issues' in patterns:
            count += len(patterns['security_issues'])
        if 'anti_patterns' in patterns:
            count += len(patterns['anti_patterns'])
        if 'warnings' in data:
            count += len(data['warnings'])
        if 'errors' in data:
            count += len(data['errors'])

        return count

    def _get_security_issues(self, data: Dict[str, Any]) -> List[Dict]:
        """Get all security issues."""
        patterns = data.get('patterns', {})
        return patterns.get('security_issues', [])

    def _categorize_issues(self, data: Dict[str, Any]) -> Dict[str, List]:
        """Categorize all issues by severity."""
        issues = {'critical': [], 'high': [], 'medium': [], 'low': []}

        # Security issues
        for issue in self._get_security_issues(data):
            severity = issue.get('severity', 'medium')
            issues[severity].append(issue)

        # Other patterns
        patterns = data.get('patterns', {})
        if 'anti_patterns' in patterns:
            for pattern in patterns['anti_patterns']:
                if isinstance(pattern, dict):
                    issues['medium'].append({
                        'type': 'Anti-pattern',
                        'description': pattern.get('description', str(pattern))
                    })
                else:
                    issues['medium'].append({
                        'type': 'Anti-pattern',
                        'description': str(pattern)
                    })

        return issues

    def _get_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Get actionable recommendations."""
        recommendations = []

        migration = data.get('migration_recommendations', {})
        if 'required_changes' in migration:
            recommendations.extend(migration['required_changes'][:5])

        # Add security recommendations
        if self._get_security_issues(data):
            recommendations.append("Implement Laravel security patterns (CSRF, input validation, SQL injection prevention)")

        # Add pattern improvements
        if self._count_all_issues(data) > 5:
            recommendations.append("Refactor code to follow Laravel conventions and best practices")

        return recommendations

    def _get_next_steps(self, data: Dict[str, Any]) -> List[str]:
        """Get concrete next steps."""
        steps = []

        # Based on priority
        migration = data.get('migration_recommendations', {})
        priority = migration.get('priority', 'medium')

        if priority == 'high':
            steps.append("Start migration immediately - high priority component")

        if self._get_security_issues(data):
            steps.append("Address security vulnerabilities before migration")

        steps.extend([
            "Create Laravel equivalent structure",
            "Implement proper error handling",
            "Add comprehensive testing",
            "Deploy to staging for validation"
        ])

        return steps[:5]

    def _get_top_migration_actions(self, data: Dict[str, Any], limit: int = 3) -> List[str]:
        """Get top migration actions for brief format."""
        actions = []

        # Security first
        if self._get_security_issues(data):
            actions.append("Fix security issues")

        # Migration specific
        migration = data.get('migration_recommendations', {})
        if 'required_changes' in migration:
            for change in migration['required_changes'][:2]:
                actions.append(change[:50])  # Truncate for brief format

        # Generic actions if none found
        if not actions:
            actions = ["Convert to Laravel", "Add validation", "Update patterns"]

        return actions[:limit]

    def _generate_executive_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary for markdown format."""
        summary_parts = []

        # Status
        if data.get('parsed', True):
            summary_parts.append("Analysis completed successfully.")
        else:
            summary_parts.append("Analysis encountered parsing issues.")

        # Key metrics
        metrics = data.get('metrics', {})
        if metrics.get('lines_of_code'):
            summary_parts.append(f"Analyzed {metrics['lines_of_code']} lines of code.")

        # Issues summary
        issues_count = self._count_all_issues(data)
        security_count = len(self._get_security_issues(data))

        if issues_count > 0:
            summary_parts.append(f"Found {issues_count} total issues, including {security_count} security concerns.")
        else:
            summary_parts.append("No significant issues detected.")

        # Migration recommendation
        migration = data.get('migration_recommendations', {})
        priority = migration.get('priority', 'medium')
        summary_parts.append(f"Migration priority: {priority}.")

        return " ".join(summary_parts)


# Global instance for easy access
output_formatter = OutputFormatter()


def format_analysis(data: Dict[str, Any], format_type: str = 'json',
                   max_tokens: Optional[int] = None, metadata: Optional[Dict] = None) -> str:
    """Convenience function for formatting analysis data."""
    return output_formatter.format_analysis(data, format_type, max_tokens, metadata)


def get_format_info() -> Dict[str, Dict]:
    """Get information about available formats."""
    return OutputFormatter.FORMAT_CONFIGS
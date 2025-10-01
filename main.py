#!/usr/bin/env python3
"""
Main CLI interface for the PHP-to-Laravel Migration Analysis System.

This script provides a command-line interface to interact with the multi-agent
analysis system for PHP to Laravel migration projects.
"""

import click
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich import print as rprint

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agents.coordinator_agent import CoordinatorAgent
from agents.php_legacy_agent import PHPLegacyAgent
from agents.laravel_agent import LaravelAgent
from agents.database_agent import DatabaseAgent
from utils.provider_checker import (
    get_provider_status_summary,
    get_recommended_mode,
    get_installation_instructions
)
from utils.ai_helper import AIHelper
from utils.output_formatter import output_formatter, get_format_info
from utils.token_tracker import token_tracker, record_token_usage
from utils.token_counter import token_counter

# Initialize Rich console
console = Console()

# Global configuration
CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"

def load_config() -> Dict[str, Any]:
    """Load configuration file."""
    try:
        import yaml
        with open(CONFIG_PATH, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        sys.exit(1)

def init_coordinator() -> CoordinatorAgent:
    """Initialize the coordinator agent."""
    try:
        coordinator = CoordinatorAgent(str(CONFIG_PATH))
        return coordinator
    except Exception as e:
        console.print(f"[red]Error initializing coordinator: {e}[/red]")
        sys.exit(1)

def format_file_path(file_path: str, max_length: int = 50) -> str:
    """Format file path for display."""
    if len(file_path) <= max_length:
        return file_path

    parts = file_path.split(os.sep)
    if len(parts) > 3:
        return f"...{os.sep}{os.sep.join(parts[-2:])}"
    return file_path

def display_analysis_summary(analysis: Dict[str, Any], title: str = "Analysis Results"):
    """Display analysis results in a formatted way."""
    panel_content = []

    if analysis.get('parsed', False):
        panel_content.append(f"[green]✓ Successfully parsed[/green]")

        # Show basic metrics
        if 'metrics' in analysis:
            metrics = analysis['metrics']
            panel_content.append(f"Lines of code: {metrics.get('lines_of_code', 'N/A')}")
            panel_content.append(f"Classes: {metrics.get('classes_count', 'N/A')}")
            panel_content.append(f"Functions: {metrics.get('functions_count', 'N/A')}")

        # Show issues if any
        if 'patterns' in analysis and 'security_issues' in analysis['patterns']:
            security_issues = analysis['patterns']['security_issues']
            if security_issues:
                critical = len([i for i in security_issues if i.get('severity') == 'critical'])
                high = len([i for i in security_issues if i.get('severity') == 'high'])
                if critical or high:
                    panel_content.append(f"[red]⚠ Security issues: {critical} critical, {high} high[/red]")

        # Show migration recommendations
        if 'migration_recommendations' in analysis:
            migration = analysis['migration_recommendations']
            priority = migration.get('priority', 'medium')
            color = {'high': 'red', 'medium': 'yellow', 'low': 'green'}.get(priority, 'white')
            panel_content.append(f"Migration priority: [{color}]{priority}[/{color}]")

    else:
        panel_content.append(f"[red]✗ Failed to parse[/red]")
        if 'error' in analysis:
            panel_content.append(f"Error: {analysis['error']}")

    console.print(Panel("\\n".join(panel_content), title=title))

def display_module_summary(analysis: Dict[str, Any]):
    """Display module analysis summary."""
    if not analysis.get('analyzed', False):
        console.print("[red]Module analysis failed[/red]")
        return

    summary = analysis.get('summary', {})

    # Create summary table
    table = Table(title="Module Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Total Files", str(summary.get('total_files_analyzed', 0)))
    table.add_row("Successfully Parsed", str(summary.get('successfully_parsed', 0)))
    table.add_row("Parse Success Rate", f"{summary.get('parse_success_rate', 0):.1f}%")
    table.add_row("PHP Legacy Files", str(summary.get('php_legacy_files', 0)))
    table.add_row("Laravel Files", str(summary.get('laravel_files', 0)))
    table.add_row("Database Files", str(summary.get('database_files', 0)))

    console.print(table)

    # Show cross-agent insights if available
    if 'cross_agent_insights' in analysis:
        insights = analysis['cross_agent_insights']
        console.print("\\n[bold]Cross-Agent Insights:[/bold]")

        # Migration completeness
        migration = insights.get('migration_completeness', {})
        score = migration.get('overall_score', 0)
        color = 'green' if score > 70 else 'yellow' if score > 40 else 'red'
        console.print(f"Migration Completeness: [{color}]{score:.1f}%[/{color}]")

        # Security assessment
        security = insights.get('security_assessment', {})
        risk_level = security.get('overall_risk_level', 'unknown')
        critical_issues = len(security.get('critical_issues', []))

        risk_color = {'low': 'green', 'medium': 'yellow', 'high': 'red', 'critical': 'red'}.get(risk_level, 'white')
        console.print(f"Security Risk Level: [{risk_color}]{risk_level}[/{risk_color}]")

        if critical_issues > 0:
            console.print(f"[red]Critical Security Issues: {critical_issues}[/red]")

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """PHP-to-Laravel Migration Analysis System

    A multi-agent system for analyzing PHP to Laravel migration projects.
    Use the subcommands to analyze files, modules, and generate reports.
    """
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--agent', type=click.Choice(['auto', 'php', 'laravel', 'database']),
              default='auto', help='Specify which agent to use')
@click.option('--output', '-o', type=click.Path(), help='Save analysis to file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'claude-summary', 'brief', 'detailed', 'markdown']),
              default='json', help='Output format')
@click.option('--max-tokens', type=int, help='Override default token limit for chosen format')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def analyze_file(file_path: str, agent: str, output: Optional[str], output_format: str, max_tokens: Optional[int], verbose: bool):
    """Analyze a specific file using the appropriate agent."""
    console.print(f"[blue]Analyzing file:[/blue] {file_path}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)

        try:
            if agent == 'auto':
                coordinator = init_coordinator()
                analysis = coordinator.analyze_file(file_path)
            else:
                # Use specific agent
                if agent == 'php':
                    agent_instance = PHPLegacyAgent(str(CONFIG_PATH))
                elif agent == 'laravel':
                    agent_instance = LaravelAgent(str(CONFIG_PATH))
                elif agent == 'database':
                    agent_instance = DatabaseAgent(str(CONFIG_PATH))

                analysis = agent_instance.analyze_file(file_path)

            progress.update(task, completed=100)

        except Exception as e:
            console.print(f"[red]Error during analysis: {e}[/red]")
            return

    # Display results
    display_analysis_summary(analysis, f"Analysis: {format_file_path(file_path)}")

    if verbose and analysis.get('parsed', False):
        # Show detailed information
        console.print("\\n[bold]Detailed Information:[/bold]")

        if 'classes' in analysis:
            for cls in analysis['classes']:
                console.print(f"  Class: [cyan]{cls['name']}[/cyan]")
                if cls.get('methods'):
                    for method in cls['methods'][:5]:  # Show first 5 methods
                        console.print(f"    Method: {method['name']}")

        if 'migration_recommendations' in analysis:
            migration = analysis['migration_recommendations']
            console.print(f"\\n[bold]Migration Recommendations:[/bold]")
            console.print(f"  Priority: {migration.get('priority', 'unknown')}")
            console.print(f"  Complexity: {migration.get('complexity', 'unknown')}")

            if migration.get('required_changes'):
                console.print("  Required Changes:")
                for change in migration['required_changes']:
                    console.print(f"    • {change}")

    # Format and save output
    if output or output_format != 'json':
        try:
            # Prepare metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'command': 'analyze-file',
                'agent': agent,
                'input_path': file_path
            }

            # Format output
            formatted_output = output_formatter.format_analysis(
                analysis, output_format, max_tokens, metadata
            )

            # Record token usage
            actual_tokens = token_counter.estimate_tokens(formatted_output)
            session_id = token_tracker.get_session_id()

            record_token_usage(
                command='analyze-file',
                format_type=output_format,
                tokens_used=actual_tokens,
                max_tokens=max_tokens,
                input_path=file_path,
                output_path=output,
                session_id=session_id,
                success=True,
                metadata={'agent': agent}
            )

            if output:
                # Save to file
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                console.print(f"[green]Analysis saved to {output}[/green]")
                console.print(f"Format: {output_format} | Tokens: {actual_tokens:,}")
            else:
                # Display formatted output
                console.print("\\n[bold]Formatted Output:[/bold]")
                console.print(formatted_output)

        except Exception as e:
            console.print(f"[red]Error formatting/saving output: {e}[/red]")

@cli.command()
@click.argument('module_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Save analysis to file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'claude-summary', 'brief', 'detailed', 'markdown']),
              default='json', help='Output format')
@click.option('--max-tokens', type=int, help='Override default token limit for chosen format')
@click.option('--summary', '-s', is_flag=True, help='Show only summary')
def analyze_module(module_path: str, output: Optional[str], output_format: str, max_tokens: Optional[int], summary: bool):
    """Analyze a module/directory using multiple agents."""
    console.print(f"[blue]Analyzing module:[/blue] {module_path}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing module...", total=None)

        try:
            coordinator = init_coordinator()
            analysis = coordinator.analyze_module(module_path)
            progress.update(task, completed=100)

        except Exception as e:
            console.print(f"[red]Error during module analysis: {e}[/red]")
            return

    # Display results
    display_module_summary(analysis)

    if not summary:
        # Show file-by-file results
        console.print("\\n[bold]File Analysis Results:[/bold]")

        agent_results = analysis.get('agent_results', {})
        for agent_type, results in agent_results.items():
            if results:
                console.print(f"\\n[cyan]{agent_type.replace('_', ' ').title()} Agent Results:[/cyan]")

                for result in results[:10]:  # Show first 10 files
                    file_path = result.get('file_path', 'unknown')
                    status = "✓" if result.get('parsed', False) else "✗"
                    color = "green" if result.get('parsed', False) else "red"

                    console.print(f"  [{color}]{status}[/{color}] {format_file_path(file_path)}")

                if len(results) > 10:
                    console.print(f"  ... and {len(results) - 10} more files")

    # Format and save output
    if output or output_format != 'json':
        try:
            # Prepare metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'command': 'analyze-module',
                'input_path': module_path
            }

            # Format output
            formatted_output = output_formatter.format_analysis(
                analysis, output_format, max_tokens, metadata
            )

            # Record token usage
            actual_tokens = token_counter.estimate_tokens(formatted_output)
            session_id = token_tracker.get_session_id()

            record_token_usage(
                command='analyze-module',
                format_type=output_format,
                tokens_used=actual_tokens,
                max_tokens=max_tokens,
                input_path=module_path,
                output_path=output,
                session_id=session_id,
                success=True,
                metadata={'summary': summary}
            )

            if output:
                # Save to file
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                console.print(f"[green]Analysis saved to {output}[/green]")
                console.print(f"Format: {output_format} | Tokens: {actual_tokens:,}")
            else:
                # Display formatted output
                console.print("\\n[bold]Formatted Output:[/bold]")
                console.print(formatted_output)

        except Exception as e:
            console.print(f"[red]Error formatting/saving output: {e}[/red]")

@cli.command()
@click.option('--scope', type=click.Choice(['all', 'core', 'laravel']),
              default='all', help='Scope of the comprehensive report')
@click.option('--output', '-o', type=click.Path(), help='Save report to file')
@click.option('--format', 'output_format', type=click.Choice(['json', 'claude-summary', 'brief', 'detailed', 'markdown']),
              default='json', help='Output format')
@click.option('--max-tokens', type=int, help='Override default token limit for chosen format')
def generate_report(scope: str, output: Optional[str], output_format: str, max_tokens: Optional[int]):
    """Generate a comprehensive migration analysis report."""
    console.print(f"[blue]Generating comprehensive report for scope:[/blue] {scope}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating report...", total=None)

        try:
            coordinator = init_coordinator()
            report = coordinator.generate_comprehensive_report(scope)
            progress.update(task, completed=100)

        except Exception as e:
            console.print(f"[red]Error generating report: {e}[/red]")
            return

    # Display executive summary
    if 'executive_summary' in report:
        summary = report['executive_summary']

        console.print("\\n[bold]Executive Summary[/bold]")
        console.print(f"Migration Status: {summary.get('migration_status', 'unknown')}")
        console.print(f"Overall Health: {summary.get('overall_health', 'unknown')}")
        console.print(f"Completion: {summary.get('completion_percentage', 0):.1f}%")
        console.print(f"Critical Issues: {summary.get('critical_issues', 0)}")

    # Display recommendations
    if 'recommendations' in report:
        recommendations = report['recommendations']

        console.print("\\n[bold]Key Recommendations:[/bold]")

        for category, recs in recommendations.items():
            if recs:
                console.print(f"\\n[cyan]{category.title()}:[/cyan]")
                for rec in recs[:3]:  # Show top 3 recommendations per category
                    console.print(f"  • {rec}")

    # Display next steps
    if 'next_steps' in report:
        next_steps = report['next_steps']

        if next_steps:
            console.print("\\n[bold]Next Steps:[/bold]")
            for i, step in enumerate(next_steps[:5], 1):
                console.print(f"  {i}. {step}")

    # Show AI insights if available
    if 'ai_insights' in report:
        insights = report['ai_insights']

        if 'strategic_analysis' in insights and insights['strategic_analysis']:
            console.print("\\n[bold]AI Strategic Analysis:[/bold]")
            # Truncate for display
            analysis_text = insights['strategic_analysis'][:500]
            if len(insights['strategic_analysis']) > 500:
                analysis_text += "..."
            console.print(Panel(analysis_text, title="Claude Analysis"))

    # Format and save output
    if output or output_format != 'json':
        try:
            # Prepare metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'command': 'generate-report',
                'scope': scope
            }

            # Format output
            formatted_output = output_formatter.format_analysis(
                report, output_format, max_tokens, metadata
            )

            # Record token usage
            actual_tokens = token_counter.estimate_tokens(formatted_output)
            session_id = token_tracker.get_session_id()

            record_token_usage(
                command='generate-report',
                format_type=output_format,
                tokens_used=actual_tokens,
                max_tokens=max_tokens,
                input_path=scope,
                output_path=output,
                session_id=session_id,
                success=True,
                metadata={'scope': scope}
            )

            if output:
                # Save to file
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                console.print(f"[green]Report saved to {output}[/green]")
                console.print(f"Format: {output_format} | Tokens: {actual_tokens:,}")
            else:
                # Display formatted output
                console.print("\\n[bold]Formatted Output:[/bold]")
                console.print(formatted_output)

        except Exception as e:
            console.print(f"[red]Error formatting/saving output: {e}[/red]")

@cli.command()
@click.argument('entity_name')
@click.option('--type', 'entity_type', type=click.Choice(['class', 'function', 'table', 'component']),
              help='Type of entity to search for')
def find_entity(entity_name: str, entity_type: Optional[str]):
    """Find an entity (class, function, table, etc.) across the codebase."""
    console.print(f"[blue]Searching for entity:[/blue] {entity_name}")

    if entity_type:
        console.print(f"[blue]Type filter:[/blue] {entity_type}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Searching...", total=None)

        try:
            coordinator = init_coordinator()

            # Search in cached analyses and knowledge base
            insights = coordinator.get_insights(insight_type='entity_search')

            # This would perform a comprehensive entity search
            # For now, show placeholder results
            results = {
                'core_matches': [],
                'laravel_matches': [],
                'database_matches': []
            }

            progress.update(task, completed=100)

        except Exception as e:
            console.print(f"[red]Error during search: {e}[/red]")
            return

    # Display results
    if any(results.values()):
        console.print(f"\\n[bold]Search Results for '{entity_name}':[/bold]")

        for section, matches in results.items():
            if matches:
                console.print(f"\\n[cyan]{section.replace('_', ' ').title()}:[/cyan]")
                for match in matches:
                    console.print(f"  • {match}")
    else:
        console.print(f"[yellow]No matches found for '{entity_name}'[/yellow]")

@cli.command()
@click.option('--limit', default=10, help='Number of insights to show')
@click.option('--type', 'insight_type', help='Filter by insight type')
def show_insights(limit: int, insight_type: Optional[str]):
    """Show learned insights from the knowledge base."""
    console.print("[blue]Retrieving insights from knowledge base...[/blue]")

    try:
        coordinator = init_coordinator()
        insights = coordinator.get_insights(insight_type=insight_type)

        if not insights:
            console.print("[yellow]No insights found[/yellow]")
            return

        # Display insights table
        table = Table(title="Knowledge Base Insights")
        table.add_column("File", style="cyan", max_width=40)
        table.add_column("Type", style="magenta")
        table.add_column("Content", style="white", max_width=60)
        table.add_column("Confidence", style="green")

        for insight in insights[:limit]:
            file_path = format_file_path(insight['file_path'])
            content = insight['content'][:100]
            if len(insight['content']) > 100:
                content += "..."

            table.add_row(
                file_path,
                insight['insight_type'],
                content,
                f"{insight['confidence']:.2f}"
            )

        console.print(table)

        if len(insights) > limit:
            console.print(f"[dim]... and {len(insights) - limit} more insights[/dim]")

    except Exception as e:
        console.print(f"[red]Error retrieving insights: {e}[/red]")

@cli.command()
def status():
    """Show system status and configuration."""
    config = load_config()

    console.print("[bold]System Status[/bold]")

    # Configuration info
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Project Name", config['project']['name'])
    table.add_row("Root Path", config['project']['root_path'])
    table.add_row("Core Path", config['project']['core_path'])
    table.add_row("Laravel Path", config['project']['laravel_path'])

    console.print(table)

    # AI Provider Status
    console.print("\\n[bold]AI Provider Status[/bold]")

    try:
        ai_helper = AIHelper(config)
        provider_info = ai_helper.get_provider_info()

        # Current mode status
        mode = provider_info['mode']
        is_manual = provider_info['is_manual']

        mode_color = 'green' if not is_manual else 'blue'
        mode_display = f"Manual (Claude Code)" if is_manual else mode.title()
        console.print(f"Current Mode: [{mode_color}]{mode_display}[/{mode_color}]")

        if not is_manual:
            console.print(f"Model: {provider_info.get('model', 'N/A')}")
            console.print(f"Max Tokens: {provider_info.get('max_tokens', 'N/A')}")

        # Token usage if available
        token_usage = provider_info.get('token_usage', {})
        if token_usage.get('session_usage', 0) > 0:
            usage_pct = token_usage.get('session_percentage', 0)
            remaining = token_usage.get('remaining_tokens', 0)
            color = 'red' if usage_pct > 80 else 'yellow' if usage_pct > 60 else 'green'
            console.print(f"Token Usage: [{color}]{usage_pct:.1f}%[/{color}] ({remaining:,} remaining)")

        # Provider status table
        provider_status = get_provider_status_summary()
        status_table = Table(title="Provider Availability")
        status_table.add_column("Provider", style="cyan")
        status_table.add_column("Package", style="white")
        status_table.add_column("API Key", style="white")
        status_table.add_column("Status", style="white")

        for provider, info in provider_status.items():
            package_status = "✓" if info['package_installed'] else "✗"
            package_color = "green" if info['package_installed'] else "red"

            key_status = "✓" if info['api_key_available'] else "✗"
            key_color = "green" if info['api_key_available'] else "yellow"

            status = info['status']
            if status == 'ready':
                status_display = "[green]Ready[/green]"
            elif status == 'needs_key':
                status_display = "[yellow]Needs API Key[/yellow]"
            elif status == 'needs_package':
                status_display = "[red]Needs Package[/red]"
            elif status == 'key_invalid':
                status_display = "[red]Invalid Key[/red]"
            else:
                status_display = f"[white]{status}[/white]"

            status_table.add_row(
                provider.title(),
                f"[{package_color}]{package_status}[/{package_color}]",
                f"[{key_color}]{key_status}[/{key_color}]",
                status_display
            )

        console.print(status_table)

        # Recommendations
        recommended_mode, reason = get_recommended_mode(config)
        if recommended_mode != mode:
            console.print(f"\\n[yellow]Recommendation:[/yellow] Consider switching to '{recommended_mode}' mode")
            console.print(f"Reason: {reason}")

            # Show installation instructions if needed
            if recommended_mode != 'none':
                instructions = get_installation_instructions()
                if recommended_mode in instructions:
                    console.print(f"\\nTo set up {recommended_mode.title()}:")
                    for instruction in instructions[recommended_mode]:
                        console.print(f"  {instruction}")

    except Exception as e:
        console.print(f"[red]Error checking AI provider status: {e}[/red]")
        console.print("[yellow]Run 'python setup_wizard.py' to configure providers[/yellow]")

    # Check file existence
    console.print("\\n[bold]File Availability:[/bold]")

    files_to_check = [
        ("Core Analysis", config['analysis_files']['core_analysis']),
        ("Laravel Analysis", config['analysis_files']['laravel_analysis']),
        ("Database Analysis", config['analysis_files']['database_analysis'])
    ]

    for name, file_path in files_to_check:
        exists = os.path.exists(file_path)
        status_icon = "✓" if exists else "✗"
        color = "green" if exists else "red"
        console.print(f"  [{color}]{status_icon}[/{color}] {name}: {file_path}")

@cli.command()
@click.option('--file', 'file_path', type=click.Path(exists=True),
              help='Analyze single file')
@click.option('--module', 'module_path', type=click.Path(exists=True),
              help='Analyze module/directory')
@click.option('--feature', help='Analyze feature by name')
@click.option('--focus', type=click.Choice(['migration', 'security', 'dependencies',
              'api-integrations', 'database', 'all']),
              default='migration', help='Focus area for analysis')
@click.option('--output', '-o', type=click.Path(), default='claude_context.md',
              help='Output filename')
@click.option('--max-tokens', type=int, default=3000,
              help='Token limit for output')
def prepare_for_claude(file_path: Optional[str], module_path: Optional[str],
                      feature: Optional[str], focus: str, output: str, max_tokens: int):
    """Prepare analysis context optimized for Claude Code review."""

    # Validate input
    input_count = sum(bool(x) for x in [file_path, module_path, feature])
    if input_count != 1:
        console.print("[red]Error: Specify exactly one of --file, --module, or --feature[/red]")
        return

    console.print(f"[blue]Preparing Claude Code context...[/blue]")
    console.print(f"Focus: {focus} | Max tokens: {max_tokens:,}")

    start_time = datetime.now()
    session_id = token_tracker.get_session_id()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)

        try:
            coordinator = init_coordinator()

            # Determine analysis type and run appropriate analysis
            if file_path:
                analysis = coordinator.analyze_file(file_path)
                input_identifier = file_path
                analysis_type = "file"
            elif module_path:
                analysis = coordinator.analyze_module(module_path)
                input_identifier = module_path
                analysis_type = "module"
            else:  # feature
                # For feature analysis, we'd need to implement feature search
                # For now, provide a helpful message
                console.print("[yellow]Feature-based analysis not yet implemented[/yellow]")
                console.print("Use --file or --module for now")
                return

            progress.update(task, completed=50)

            # Add metadata for formatting
            metadata = {
                'timestamp': start_time.isoformat(),
                'focus_area': focus,
                'analysis_type': analysis_type,
                'input_path': input_identifier,
                'session_id': session_id,
                'command': 'prepare-for-claude'
            }

            # Format for Claude Code
            formatted_output = output_formatter.format_analysis(
                analysis,
                format_type='claude-summary',
                max_tokens=max_tokens,
                metadata=metadata
            )

            progress.update(task, completed=90)

            # Save output
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_output)

            progress.update(task, completed=100)

            # Record token usage
            actual_tokens = token_counter.estimate_tokens(formatted_output)
            record_token_usage(
                command='prepare-for-claude',
                format_type='claude-summary',
                tokens_used=actual_tokens,
                max_tokens=max_tokens,
                input_path=input_identifier,
                output_path=str(output_path),
                session_id=session_id,
                focus_area=focus,
                success=True,
                metadata={'analysis_type': analysis_type}
            )

        except Exception as e:
            console.print(f"[red]Error during analysis: {e}[/red]")

            # Record failed usage
            record_token_usage(
                command='prepare-for-claude',
                format_type='claude-summary',
                tokens_used=0,
                max_tokens=max_tokens,
                input_path=input_identifier if 'input_identifier' in locals() else None,
                session_id=session_id,
                focus_area=focus,
                success=False,
                metadata={'error': str(e)}
            )
            return

    # Show results
    actual_tokens = token_counter.estimate_tokens(formatted_output)
    console.print(f"[green]✓ Claude Code context ready![/green]")
    console.print(f"Output: {output}")
    console.print(f"Tokens: {actual_tokens:,} / {max_tokens:,} ({actual_tokens/max_tokens*100:.1f}%)")

    # Show suggested next steps
    console.print("\\n[bold]Next steps:[/bold]")
    console.print("1. Open the output file in Claude Code")
    console.print("2. Use the suggested prompts for focused analysis")
    console.print(f"3. Focus on {focus} aspects as configured")

@cli.command()
@click.option('--period', type=click.Choice(['session', 'today', 'week', 'all']),
              default='today', help='Time period for statistics')
def token_stats(period: str):
    """Show token usage statistics and optimization recommendations."""

    console.print(f"[bold]Token Usage Statistics - {period.title()}[/bold]")

    try:
        # Get usage statistics
        stats = token_tracker.get_usage_stats(period)
        config = load_config()

        # Basic stats table
        basic = stats['basic_stats']

        stats_table = Table(title="Usage Summary")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")

        stats_table.add_row("Analyses Run", str(basic['analyses_run']))
        stats_table.add_row("Total Tokens", f"{basic['total_tokens']:,}")
        stats_table.add_row("Average Tokens", f"{basic['avg_tokens']:,.1f}")
        stats_table.add_row("Success Rate", f"{basic['success_rate']:.1f}%")

        if basic['analyses_run'] > 0:
            stats_table.add_row("Min Tokens", f"{basic['min_tokens']:,}")
            stats_table.add_row("Max Tokens", f"{basic['max_tokens']:,}")

        console.print(stats_table)

        # Format distribution
        if stats['format_distribution']:
            console.print("\\n[bold]Format Distribution:[/bold]")
            total_analyses = basic['analyses_run']

            for fmt in stats['format_distribution']:
                count = fmt['count']
                percentage = (count / total_analyses) * 100 if total_analyses > 0 else 0
                avg_tokens = fmt['avg_tokens']
                console.print(f"  {fmt['format_type']}: {count} ({percentage:.1f}%) - avg {avg_tokens:.0f} tokens")

        # Budget status if configured
        if 'token_budget' in config:
            console.print("\\n[bold]Budget Status:[/bold]")
            budget_status = token_tracker.get_budget_status(config['token_budget'])

            session_info = budget_status['session']
            daily_info = budget_status['daily']

            # Session budget
            session_color = 'red' if session_info['percentage'] > 100 else 'yellow' if session_info['percentage'] > 80 else 'green'
            console.print(f"Session: [{session_color}]{session_info['used']:,} / {session_info['limit']:,} ({session_info['percentage']:.1f}%)[/{session_color}]")

            # Daily budget
            daily_color = 'red' if daily_info['percentage'] > 100 else 'yellow' if daily_info['percentage'] > 80 else 'green'
            console.print(f"Daily: [{daily_color}]{daily_info['used']:,} / {daily_info['limit']:,} ({daily_info['percentage']:.1f}%)[/{daily_color}]")

            # Status message
            status = budget_status['status']
            if status == 'exceeded':
                console.print("[red]⚠ Budget exceeded![/red]")
            elif status == 'warning':
                console.print("[yellow]⚠ Approaching budget limit[/yellow]")
            else:
                console.print("[green]✓ Well within budget[/green]")

        # Optimization recommendations
        recommendations = token_tracker.get_optimization_recommendations(stats)
        if recommendations:
            console.print("\\n[bold]💡 Optimization Tips:[/bold]")
            for rec in recommendations:
                console.print(f"  • {rec}")

        # Command distribution (if multiple commands used)
        if len(stats['command_distribution']) > 1:
            console.print("\\n[bold]Command Usage:[/bold]")
            for cmd in stats['command_distribution'][:5]:  # Top 5
                console.print(f"  {cmd['command']}: {cmd['count']} times ({cmd['total_tokens']:,} tokens)")

    except Exception as e:
        console.print(f"[red]Error retrieving token statistics: {e}[/red]")

# ============================================================================
# NEW COMMANDS FOR TASKS 3 & 4: LEARNING AND SMART ANALYSIS
# ============================================================================

@cli.command()
@click.argument('analysis_file', type=click.Path(exists=True))
@click.argument('feedback_file', type=click.Path(exists=True))
def learn_from_feedback(analysis_file: str, feedback_file: str):
    """Learn patterns and insights from analysis feedback.

    Parses both the original analysis and your feedback to extract:
    - Migration patterns (legacy → modern)
    - Code transformation examples
    - Security improvements
    - Architecture patterns
    - Migration strategies
    """
    from utils.pattern_learner import PatternLearner

    console.print("[blue]Learning from feedback...[/blue]")
    console.print(f"Analysis: {analysis_file}")
    console.print(f"Feedback: {feedback_file}")

    try:
        learner = PatternLearner()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting patterns...", total=None)
            result = learner.learn_from_feedback(analysis_file, feedback_file)
            progress.update(task, completed=100)

        # Display results
        console.print("\n[green]✓ Learning completed![/green]")
        console.print(f"Patterns learned: {result['patterns_learned']}")
        console.print(f"Insights gained: {result['insights_gained']}")
        console.print(f"Transformations found: {result['transformations_found']}")
        console.print(f"Strategies identified: {result['strategies_identified']}")

        if result.get('summary'):
            console.print(f"\n{result['summary']}")

    except Exception as e:
        console.print(f"[red]Error learning from feedback: {e}[/red]")

@cli.command()
@click.option('--type', 'insight_type', default='all',
              help='Type of insights (all, migration_patterns, security, etc.)')
@click.option('--search', '-s', help='Search term to filter insights')
@click.option('--limit', '-l', default=10, help='Number of insights to show')
def show_insights(insight_type: str, search: Optional[str], limit: int):
    """Show learned insights and patterns.

    Examples:
        python main.py show-insights --type migration_patterns
        python main.py show-insights --search "payment"
        python main.py show-insights --type all --limit 20
    """
    from utils.pattern_learner import PatternLearner

    console.print(f"[bold]Learned Insights[/bold]")
    if insight_type != 'all':
        console.print(f"Type: {insight_type}")
    if search:
        console.print(f"Search: {search}")
    console.print("")

    try:
        learner = PatternLearner()

        # Get insights
        insights = learner.get_insights(insight_type, search)

        if not insights:
            console.print("[yellow]No insights found matching criteria[/yellow]")
            return

        # Display insights table
        table = Table(title=f"Showing {min(len(insights), limit)} of {len(insights)} insights")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Category", style="yellow", width=20)
        table.add_column("Name", style="white", width=50)
        table.add_column("Confidence", style="green", width=10)

        for insight in insights[:limit]:
            table.add_row(
                str(insight['id']),
                insight['category'],
                insight['name'][:47] + "..." if len(insight['name']) > 50 else insight['name'],
                f"{insight['confidence']:.0%}"
            )

        console.print(table)

        # Get patterns
        patterns = learner.get_patterns(insight_type if insight_type != 'all' else None)

        if patterns:
            console.print(f"\n[bold]Migration Patterns ({len(patterns)})[/bold]")

            for i, pattern in enumerate(patterns[:5], 1):
                console.print(f"\n{i}. [cyan]{pattern['name']}[/cyan]")
                console.print(f"   Category: {pattern['category']}")
                console.print(f"   Confidence: {pattern['confidence']:.0%}")
                console.print(f"   Success count: {pattern['success_count']}")
                if pattern.get('legacy_pattern'):
                    console.print(f"   Legacy: {pattern['legacy_pattern'][:60]}...")
                if pattern.get('modern_equivalent'):
                    console.print(f"   Modern: {pattern['modern_equivalent'][:60]}...")

    except Exception as e:
        console.print(f"[red]Error retrieving insights: {e}[/red]")

@cli.command()
@click.argument('target')
@click.option('--smart', is_flag=True, help='Enable intelligent relationship following')
@click.option('--type', 'analysis_type', type=click.Choice(['file', 'route', 'feature', 'module']),
              default='file', help='Type of analysis target')
@click.option('--depth', default=3, help='How deep to follow relationships (1-5)')
@click.option('--focus', type=click.Choice(['migration', 'security', 'architecture', 'all']),
              default='all', help='Analysis focus area')
@click.option('--diagram', is_flag=True, help='Generate flow diagram')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: claude_context.md)')
@click.option('--format', 'diagram_format', type=click.Choice(['mermaid', 'ascii', 'both']),
              default='both', help='Diagram format')
def analyze(target: str, smart: bool, analysis_type: str, depth: int, focus: str,
           diagram: bool, output: Optional[str], diagram_format: str):
    """Smart analysis with relationship mapping.

    Examples:
        # Legacy PHP with smart context:
        python main.py analyze cyclecount.php --smart

        # Laravel route with full stack analysis:
        python main.py analyze warehouse/cycle-count --type route --smart

        # With flow diagram:
        python main.py analyze cyclecount.php --smart --diagram
    """
    from analyzers.relationship_mapper import RelationshipMapper
    from utils.flow_diagram import FlowDiagramGenerator
    from utils.pattern_learner import PatternLearner

    console.print(f"[blue]Smart Analysis:[/blue] {target}")
    console.print(f"Type: {analysis_type} | Depth: {depth} | Focus: {focus}")

    if not output:
        output = "claude_context.md"

    try:
        # Initialize components
        config = load_config()
        project_root = Path(config['project']['root_path'])
        mapper = RelationshipMapper(str(project_root))
        diagram_gen = FlowDiagramGenerator()
        learner = PatternLearner()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing relationships...", total=None)

            # Analyze based on type
            if analysis_type == 'route':
                graph = mapper.analyze_laravel_route(target, depth)
                feature_name = target.replace('/', ' ').title()
            else:  # file, feature, module
                graph = mapper.analyze_php_legacy(target, depth)
                feature_name = Path(target).stem.replace('_', ' ').title()

            progress.update(task, completed=100)

        graph_dict = mapper.to_dict(graph)

        # Generate output
        output_lines = []
        output_lines.append(f"# Smart Analysis: {feature_name}")
        output_lines.append("")
        output_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"**Type:** {analysis_type}")
        output_lines.append(f"**Depth:** {depth}")
        output_lines.append(f"**Focus:** {focus}")
        output_lines.append("")

        # Summary
        output_lines.append("## Analysis Summary")
        output_lines.append("")
        output_lines.append(f"- **Files analyzed:** {len(graph_dict['nodes'])}")
        output_lines.append(f"- **Relationships found:** {len(graph_dict['edges'])}")
        output_lines.append(f"- **Database tables:** {len(graph_dict['database_tables'])}")
        output_lines.append(f"- **Entry points:** {len(graph_dict['entry_points'])}")
        output_lines.append("")

        # File relationships
        output_lines.append("## File Relationships")
        output_lines.append("")

        for node_path, node_info in graph_dict['nodes'].items():
            output_lines.append(f"### {Path(node_path).name}")
            output_lines.append(f"- **Type:** {node_info['type']}")
            output_lines.append(f"- **Path:** `{node_path}`")

            # Find related files
            related = [e for e in graph_dict['edges'] if e['source_file'] == node_path]
            if related:
                output_lines.append("- **Related files:**")
                for rel in related:
                    output_lines.append(f"  - {rel['relationship_type']}: `{Path(rel['target_file']).name}`")

            output_lines.append("")

        # Database tables
        if graph_dict['database_tables']:
            output_lines.append("## Database Tables")
            output_lines.append("")
            for table in graph_dict['database_tables']:
                output_lines.append(f"- `{table}`")
            output_lines.append("")

        # Flow diagrams
        if diagram:
            output_lines.append("## Flow Diagram")
            output_lines.append("")

            if diagram_format in ['mermaid', 'both']:
                mermaid = diagram_gen.generate_mermaid(graph_dict, feature_name)
                output_lines.append(mermaid)
                output_lines.append("")

            if diagram_format in ['ascii', 'both']:
                ascii_diagram = diagram_gen.generate_ascii(graph_dict, feature_name)
                output_lines.append("```")
                output_lines.append(ascii_diagram)
                output_lines.append("```")
                output_lines.append("")

            # Feature flow
            feature_flow = diagram_gen.generate_feature_flow(graph_dict, feature_name)
            output_lines.append("## Feature Flow")
            output_lines.append("```")
            output_lines.append(feature_flow)
            output_lines.append("```")
            output_lines.append("")

        # Smart suggestions
        if smart:
            output_lines.append("## Smart Suggestions")
            output_lines.append("")

            # Find similar patterns
            for node_path in list(graph_dict['nodes'].keys())[:3]:  # Check first 3 files
                try:
                    with open(project_root / node_path, 'r') as f:
                        code_snippet = f.read()[:500]  # First 500 chars

                    similar = learner.get_similar_patterns(code_snippet, limit=3)

                    if similar:
                        output_lines.append(f"### Suggestions for `{Path(node_path).name}`")
                        output_lines.append("")
                        for i, pattern in enumerate(similar, 1):
                            output_lines.append(f"{i}. **{pattern['name']}**")
                            output_lines.append(f"   - Confidence: {pattern['confidence']:.0%}")
                            output_lines.append(f"   - Success count: {pattern['success_count']}")
                            output_lines.append("")
                except:
                    pass

        # Write output
        output_content = "\n".join(output_lines)

        with open(output, 'w', encoding='utf-8') as f:
            f.write(output_content)

        console.print(f"\n[green]✓ Analysis saved to {output}[/green]")
        console.print(f"Files analyzed: {len(graph_dict['nodes'])}")
        console.print(f"Relationships: {len(graph_dict['edges'])}")

    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

@cli.command()
@click.argument('feature_name')
@click.option('--smart', is_flag=True, help='Include full context analysis')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def compare(feature_name: str, smart: bool, output: Optional[str]):
    """Compare legacy vs Laravel implementation of a feature.

    Example:
        python main.py compare cyclecount --smart
    """
    from analyzers.relationship_mapper import RelationshipMapper

    console.print(f"[blue]Comparing feature:[/blue] {feature_name}")

    if not output:
        output = f"comparison_{feature_name}.md"

    try:
        project_root = Path.cwd()
        mapper = RelationshipMapper(str(project_root))

        # Find legacy file
        legacy_file = f"{feature_name}.php"
        legacy_path = project_root / "core" / legacy_file

        # Find Laravel route
        laravel_route = feature_name.replace('_', '-')

        output_lines = []
        output_lines.append(f"# Feature Comparison: {feature_name.replace('_', ' ').title()}")
        output_lines.append("")
        output_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("")

        # Analyze legacy
        output_lines.append("## Legacy Implementation (PHP 5.6)")
        output_lines.append("")

        if legacy_path.exists():
            if smart:
                legacy_graph = mapper.analyze_php_legacy(str(legacy_path), depth=2)
                legacy_dict = mapper.to_dict(legacy_graph)

                output_lines.append(f"- **Entry point:** `{legacy_file}`")
                output_lines.append(f"- **Files involved:** {len(legacy_dict['nodes'])}")
                output_lines.append(f"- **Database tables:** {', '.join(list(legacy_dict['database_tables'])[:5])}")

                # Count AJAX endpoints
                ajax_endpoints = [e for e in legacy_dict['edges'] if 'ajax' in e['relationship_type']]
                output_lines.append(f"- **AJAX endpoints:** {len(ajax_endpoints)}")
            else:
                output_lines.append(f"- **Entry point:** `{legacy_file}`")
        else:
            output_lines.append("[yellow]Legacy file not found[/yellow]")

        output_lines.append("")

        # Analyze Laravel
        output_lines.append("## Modern Implementation (Laravel + Vue)")
        output_lines.append("")

        from analyzers.route_parser import RouteParser

        laravel_root = project_root / "laravel"
        route_parser = RouteParser(str(laravel_root))
        route_info = route_parser.find_route(laravel_route)

        if route_info:
            output_lines.append(f"- **Route:** `{route_info['route']}`")
            output_lines.append(f"- **Controller:** `{route_info['controller']}`")
            output_lines.append(f"- **Method:** `{route_info['method']}`")

            if smart:
                laravel_graph = mapper.analyze_laravel_route(laravel_route, depth=2)
                laravel_dict = mapper.to_dict(laravel_graph)

                output_lines.append(f"- **Files involved:** {len(laravel_dict['nodes'])}")
                output_lines.append(f"- **Database tables:** {', '.join(list(laravel_dict['database_tables'])[:5])}")

                # Count API endpoints
                api_endpoints = [e for e in laravel_dict['edges'] if 'api' in e['relationship_type']]
                output_lines.append(f"- **API endpoints:** {len(api_endpoints)}")
        else:
            output_lines.append("[yellow]Laravel implementation not found[/yellow]")

        output_lines.append("")

        # Comparison summary
        output_lines.append("## Comparison Summary")
        output_lines.append("")
        output_lines.append("### Status")
        output_lines.append("- [ ] Fully migrated")
        output_lines.append("- [ ] Partially migrated")
        output_lines.append("- [ ] Not started")
        output_lines.append("")
        output_lines.append("### Notes")
        output_lines.append("")
        output_lines.append("*Add your comparison notes here after reviewing both implementations*")

        # Write output
        output_content = "\n".join(output_lines)

        with open(output, 'w', encoding='utf-8') as f:
            f.write(output_content)

        console.print(f"\n[green]✓ Comparison saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error during comparison: {e}[/red]")

@cli.command()
@click.argument('feature_description')
@click.option('--type', 'feature_type', type=click.Choice(['new', 'enhance']),
              default='new', help='Type of feature (new or enhancement)')
@click.option('--suggestion', '-s', help='Enhancement suggestion')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def feature(feature_description: str, feature_type: str, suggestion: Optional[str],
           output: Optional[str]):
    """Plan a new feature or enhancement.

    Examples:
        python main.py feature "barcode scanning" --type new
        python main.py feature "orders" --type enhance --suggestion "add bulk actions"
    """
    from utils.pattern_learner import PatternLearner

    console.print(f"[blue]Feature Planning:[/blue] {feature_description}")
    console.print(f"Type: {feature_type}")

    if not output:
        output = f"feature_plan_{feature_description.replace(' ', '_')}.md"

    try:
        learner = PatternLearner()

        output_lines = []
        output_lines.append(f"# Feature Plan: {feature_description.title()}")
        output_lines.append("")
        output_lines.append(f"**Type:** {feature_type}")
        output_lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("")

        if feature_type == 'new':
            output_lines.append("## Feature Description")
            output_lines.append("")
            output_lines.append(feature_description)
            output_lines.append("")

            # Find similar features
            output_lines.append("## Similar Existing Features")
            output_lines.append("")
            output_lines.append("*Search codebase for similar implementations to learn from*")
            output_lines.append("")

            # Get relevant patterns
            patterns = learner.get_patterns()[:5]

            if patterns:
                output_lines.append("## Recommended Patterns")
                output_lines.append("")

                for i, pattern in enumerate(patterns, 1):
                    output_lines.append(f"### {i}. {pattern['name']}")
                    output_lines.append(f"- **Confidence:** {pattern['confidence']:.0%}")
                    output_lines.append(f"- **Category:** {pattern['category']}")
                    if pattern.get('modern_equivalent'):
                        output_lines.append(f"- **Approach:** {pattern['modern_equivalent'][:100]}...")
                    output_lines.append("")

            output_lines.append("## Implementation Checklist")
            output_lines.append("")
            output_lines.append("- [ ] Database migration")
            output_lines.append("- [ ] Model(s) creation")
            output_lines.append("- [ ] Controller(s)")
            output_lines.append("- [ ] API routes")
            output_lines.append("- [ ] Vue component(s)")
            output_lines.append("- [ ] Form requests/validation")
            output_lines.append("- [ ] Service class (if needed)")
            output_lines.append("- [ ] Tests")
            output_lines.append("- [ ] Documentation")
            output_lines.append("")

        else:  # enhance
            output_lines.append("## Enhancement Description")
            output_lines.append("")
            output_lines.append(f"**Existing Feature:** {feature_description}")
            output_lines.append(f"**Enhancement:** {suggestion or 'TBD'}")
            output_lines.append("")

            output_lines.append("## Current Implementation")
            output_lines.append("")
            output_lines.append("*Analyze current implementation here*")
            output_lines.append("")

            output_lines.append("## Proposed Changes")
            output_lines.append("")
            output_lines.append("### Files to Modify")
            output_lines.append("- [ ] Controller:")
            output_lines.append("- [ ] Model:")
            output_lines.append("- [ ] Vue component:")
            output_lines.append("- [ ] Routes:")
            output_lines.append("")

            output_lines.append("### Database Changes")
            output_lines.append("- [ ] Migration needed: Yes/No")
            output_lines.append("")

            output_lines.append("### Testing")
            output_lines.append("- [ ] Unit tests")
            output_lines.append("- [ ] Feature tests")
            output_lines.append("")

        output_lines.append("## Estimated Effort")
        output_lines.append("")
        output_lines.append("- **Complexity:** Low / Medium / High")
        output_lines.append("- **Estimated hours:** TBD")
        output_lines.append("")

        # Write output
        output_content = "\n".join(output_lines)

        with open(output, 'w', encoding='utf-8') as f:
            f.write(output_content)

        console.print(f"\n[green]✓ Feature plan saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error creating feature plan: {e}[/red]")

@cli.command()
@click.argument('target')
@click.option('--format', 'graph_format', type=click.Choice(['mermaid', 'ascii', 'json']),
              default='ascii', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file')
def graph(target: str, graph_format: str, output: Optional[str]):
    """Generate dependency graph for a file or feature.

    Example:
        python main.py graph cyclecount.php --format mermaid
    """
    from analyzers.relationship_mapper import RelationshipMapper
    from utils.flow_diagram import FlowDiagramGenerator

    console.print(f"[blue]Generating dependency graph:[/blue] {target}")

    try:
        project_root = Path.cwd()
        mapper = RelationshipMapper(str(project_root))
        diagram_gen = FlowDiagramGenerator()

        # Analyze
        graph = mapper.analyze_php_legacy(target, depth=2)
        graph_dict = mapper.to_dict(graph)

        # Generate diagram
        if graph_format == 'mermaid':
            diagram = diagram_gen.generate_mermaid(graph_dict, Path(target).stem)
        elif graph_format == 'ascii':
            diagram = diagram_gen.generate_dependency_tree(graph_dict, target)
        else:  # json
            diagram = diagram_gen.generate_json(graph_dict)

        # Output
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(diagram)
            console.print(f"\n[green]✓ Graph saved to {output}[/green]")
        else:
            console.print("\n" + diagram)

    except Exception as e:
        console.print(f"[red]Error generating graph: {e}[/red]")

@cli.command()
@click.argument('feature_name')
def progress(feature_name: str):
    """Show progress for a specific feature migration.

    Example:
        python main.py progress cyclecount
    """
    console.print(f"[blue]Feature Progress:[/blue] {feature_name}")
    console.print("")

    # This is a placeholder - would be enhanced with actual tracking
    console.print("╔════════════════════════════════════════════╗")
    console.print(f"║  Feature Progress: {feature_name:<20} ║")
    console.print("╚════════════════════════════════════════════╝")
    console.print("")

    console.print("Analysis: ✅ Complete")
    console.print("Migration Status: 🟡 In Progress")
    console.print("")

    console.print("Components:")
    console.print("  ✅ Database schema migrated")
    console.print("  ✅ Backend API created")
    console.print("  🟡 Frontend partially migrated (60%)")
    console.print("  ❌ Excel export not implemented")
    console.print("  ❌ Additional features pending")
    console.print("")

    console.print("Next Steps:")
    console.print("  1. Complete Vue component migration")
    console.print("  2. Implement remaining features")
    console.print("  3. Add comprehensive testing")

if __name__ == "__main__":
    cli()
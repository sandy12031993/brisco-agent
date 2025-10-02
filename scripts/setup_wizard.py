#!/usr/bin/env python3
"""
Interactive setup wizard for the PHP-to-Laravel Migration Analysis System.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Rich library not installed. Install with: pip install rich>=13.0.0")
    sys.exit(1)

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.provider_checker import (
    detect_available_providers,
    detect_available_api_keys,
    get_recommended_mode,
    validate_api_key,
    get_provider_status_summary,
    get_installation_instructions
)

console = Console()

class SetupWizard:
    """Interactive setup wizard for configuring AI providers."""

    def __init__(self):
        self.config_path = Path(__file__).parent / "config" / "config.yaml"
        self.config = self._load_current_config()

    def _load_current_config(self) -> Dict[str, Any]:
        """Load current configuration."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            console.print("[red]Config file not found![/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            sys.exit(1)

    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(config, file, default_flow_style=False, indent=2)
            console.print(f"[green]✓ Configuration saved to {self.config_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error saving config: {e}[/red]")
            sys.exit(1)

    def run(self):
        """Run the interactive setup wizard."""
        console.print(Panel.fit(
            "[bold blue]PHP-to-Laravel Migration Analysis System[/bold blue]\n"
            "[dim]AI Provider Setup Wizard[/dim]",
            border_style="blue"
        ))

        # Show current status
        self._show_current_status()

        # Main menu
        while True:
            choice = self._show_main_menu()

            if choice == "configure":
                self._configure_ai_provider()
            elif choice == "status":
                self._show_detailed_status()
            elif choice == "install":
                self._show_installation_guide()
            elif choice == "test":
                self._test_current_setup()
            elif choice == "reset":
                self._reset_to_manual()
            elif choice == "exit":
                break

        console.print("\n[green]Setup wizard completed![/green]")
        console.print("\nNext steps:")
        console.print("1. Run: [cyan]pip install -r requirements.txt[/cyan]")
        console.print("2. Test: [cyan]python main.py status[/cyan]")

    def _show_current_status(self):
        """Show current AI provider configuration."""
        current_mode = self.config.get('ai_provider', {}).get('mode', 'none')

        if current_mode == 'none':
            status_text = "[yellow]Manual Mode[/yellow] (Claude Code/Cursor workflow)"
            details = "No API key required - uses manual review workflow"
        else:
            status_text = f"[blue]{current_mode.title()}[/blue] API Mode"
            details = f"Using {current_mode} provider for AI analysis"

        console.print(Panel(
            f"[bold]Current Configuration:[/bold]\n"
            f"AI Provider: {status_text}\n"
            f"Details: {details}",
            title="System Status",
            border_style="green"
        ))

    def _show_main_menu(self) -> str:
        """Show main menu and get user choice."""
        console.print("\n[bold]What would you like to do?[/bold]")

        choices = [
            ("configure", "Configure AI provider"),
            ("status", "View detailed status"),
            ("install", "Show installation instructions"),
            ("test", "Test current setup"),
            ("reset", "Reset to manual mode"),
            ("exit", "Exit wizard")
        ]

        for i, (key, description) in enumerate(choices, 1):
            console.print(f"  {i}. {description}")

        while True:
            try:
                choice_num = int(Prompt.ask("\nEnter your choice", default="1"))
                if 1 <= choice_num <= len(choices):
                    return choices[choice_num - 1][0]
                else:
                    console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a number.[/red]")

    def _configure_ai_provider(self):
        """Configure AI provider settings."""
        console.print("\n[bold]AI Provider Configuration[/bold]")

        # Get current recommendation
        recommended_mode, reason = get_recommended_mode(self.config)

        console.print(f"\n[dim]Recommendation: {recommended_mode} ({reason})[/dim]")

        # Show available options
        console.print("\n[bold]Available AI modes:[/bold]")
        modes = [
            ("none", "Manual Mode", "Use Claude Code/Cursor for manual analysis (Default)"),
            ("anthropic", "Anthropic Claude", "Use Claude API for automated analysis"),
            ("openai", "OpenAI GPT", "Use OpenAI API for automated analysis"),
            ("cursor", "Cursor Integration", "Use Cursor's AI features (Coming soon)")
        ]

        for i, (mode, name, description) in enumerate(modes, 1):
            marker = " [green](Recommended)[/green]" if mode == recommended_mode else ""
            console.print(f"  {i}. [bold]{name}[/bold]{marker}")
            console.print(f"     {description}")

        # Get user choice
        while True:
            try:
                choice_num = int(Prompt.ask("\nSelect AI mode", default="1"))
                if 1 <= choice_num <= len(modes):
                    selected_mode = modes[choice_num - 1][0]
                    break
                else:
                    console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a number.[/red]")

        # Configure the selected mode
        if selected_mode == 'none':
            self._configure_manual_mode()
        elif selected_mode == 'anthropic':
            self._configure_anthropic()
        elif selected_mode == 'openai':
            self._configure_openai()
        elif selected_mode == 'cursor':
            self._configure_cursor()

    def _configure_manual_mode(self):
        """Configure manual mode settings."""
        console.print("\n[bold]Manual Mode Configuration[/bold]")

        console.print(Panel(
            "[green]Manual mode selected![/green]\n\n"
            "In manual mode, the system will:\n"
            "• Export analysis context to markdown files\n"
            "• Generate structured prompts for Claude Code/Cursor\n"
            "• Provide step-by-step analysis instructions\n"
            "• No API key required\n\n"
            "[dim]Perfect for users who prefer manual review or don't have API access.[/dim]",
            title="Manual Mode Benefits"
        ))

        # Configure export path
        current_path = self.config.get('ai_provider', {}).get('manual_export_path', 'claude_context')
        export_path = Prompt.ask(
            "Export directory for manual review files",
            default=current_path
        )

        # Update configuration
        if 'ai_provider' not in self.config:
            self.config['ai_provider'] = {}

        self.config['ai_provider']['mode'] = 'none'
        self.config['ai_provider']['manual_export_path'] = export_path
        self.config['ai_provider']['fallback_to_manual'] = True

        self._save_config(self.config)

        console.print(f"\n[green]✓ Manual mode configured successfully![/green]")
        console.print(f"Export path: [cyan]{export_path}[/cyan]")

    def _configure_anthropic(self):
        """Configure Anthropic Claude API."""
        console.print("\n[bold]Anthropic Claude Configuration[/bold]")

        # Check if package is installed
        available_providers = detect_available_providers()
        if not available_providers.get('anthropic', False):
            console.print("[yellow]⚠ Anthropic package not installed[/yellow]")
            if Confirm.ask("Install Anthropic package now?"):
                self._install_package("anthropic>=0.18.0")
            else:
                console.print("[red]Anthropic package required for this mode[/red]")
                return

        # Get API key
        current_key = os.getenv('ANTHROPIC_API_KEY')
        if current_key:
            console.print(f"[green]✓ Found API key in environment[/green]")
            use_existing = Confirm.ask("Use existing API key?", default=True)
            if use_existing:
                api_key = current_key
            else:
                api_key = self._get_api_key("Anthropic")
        else:
            console.print("API key not found in environment (ANTHROPIC_API_KEY)")
            api_key = self._get_api_key("Anthropic")

        if not api_key:
            console.print("[red]API key required for Anthropic mode[/red]")
            return

        # Validate API key
        console.print("Validating API key...")
        is_valid, message = validate_api_key('anthropic', api_key)

        if is_valid:
            console.print(f"[green]✓ {message}[/green]")

            # Update configuration
            if 'ai_provider' not in self.config:
                self.config['ai_provider'] = {}

            self.config['ai_provider']['mode'] = 'anthropic'
            self.config['ai_provider']['anthropic_api_key'] = '${ANTHROPIC_API_KEY}'

            # Set environment variable if not already set
            if not os.getenv('ANTHROPIC_API_KEY'):
                self._set_environment_variable('ANTHROPIC_API_KEY', api_key)

            self._save_config(self.config)
            console.print("[green]✓ Anthropic configuration completed![/green]")

        else:
            console.print(f"[red]✗ {message}[/red]")
            console.print("Please check your API key and try again.")

    def _configure_openai(self):
        """Configure OpenAI API."""
        console.print("\n[bold]OpenAI Configuration[/bold]")

        # Check if package is installed
        available_providers = detect_available_providers()
        if not available_providers.get('openai', False):
            console.print("[yellow]⚠ OpenAI package not installed[/yellow]")
            if Confirm.ask("Install OpenAI package now?"):
                self._install_package("openai>=1.0.0")
            else:
                console.print("[red]OpenAI package required for this mode[/red]")
                return

        # Get API key
        current_key = os.getenv('OPENAI_API_KEY')
        if current_key:
            console.print(f"[green]✓ Found API key in environment[/green]")
            use_existing = Confirm.ask("Use existing API key?", default=True)
            if use_existing:
                api_key = current_key
            else:
                api_key = self._get_api_key("OpenAI")
        else:
            console.print("API key not found in environment (OPENAI_API_KEY)")
            api_key = self._get_api_key("OpenAI")

        if not api_key:
            console.print("[red]API key required for OpenAI mode[/red]")
            return

        # Validate API key
        console.print("Validating API key...")
        is_valid, message = validate_api_key('openai', api_key)

        if is_valid:
            console.print(f"[green]✓ {message}[/green]")

            # Update configuration
            if 'ai_provider' not in self.config:
                self.config['ai_provider'] = {}

            self.config['ai_provider']['mode'] = 'openai'
            self.config['ai_provider']['openai_api_key'] = '${OPENAI_API_KEY}'

            # Set environment variable if not already set
            if not os.getenv('OPENAI_API_KEY'):
                self._set_environment_variable('OPENAI_API_KEY', api_key)

            self._save_config(self.config)
            console.print("[green]✓ OpenAI configuration completed![/green]")

        else:
            console.print(f"[red]✗ {message}[/red]")
            console.print("Please check your API key and try again.")

    def _configure_cursor(self):
        """Configure Cursor integration."""
        console.print("\n[bold]Cursor Integration[/bold]")

        console.print(Panel(
            "[yellow]Cursor integration is not yet available.[/yellow]\n\n"
            "This feature will be implemented when Cursor provides\n"
            "an official API for external integrations.\n\n"
            "For now, you can use manual mode with Cursor's\n"
            "built-in AI features.",
            title="Coming Soon"
        ))

    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from user input."""
        console.print(f"\nTo get your {provider} API key:")

        if provider == "Anthropic":
            console.print("1. Visit: [link]https://console.anthropic.com/[/link]")
            console.print("2. Sign in or create an account")
            console.print("3. Go to API Keys section")
            console.print("4. Create a new API key")
        elif provider == "OpenAI":
            console.print("1. Visit: [link]https://platform.openai.com/api-keys[/link]")
            console.print("2. Sign in or create an account")
            console.print("3. Create a new API key")

        api_key = Prompt.ask(f"\nEnter your {provider} API key (or press Enter to skip)", password=True)

        return api_key if api_key.strip() else None

    def _set_environment_variable(self, var_name: str, value: str):
        """Set environment variable for current session."""
        os.environ[var_name] = value
        console.print(f"[dim]Environment variable {var_name} set for current session[/dim]")
        console.print(f"[dim]To make permanent, add to your shell profile:[/dim]")
        console.print(f"[dim]export {var_name}=your_api_key_here[/dim]")

    def _install_package(self, package: str) -> bool:
        """Install a Python package."""
        try:
            import subprocess
            import sys

            console.print(f"Installing {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                console.print(f"[green]✓ {package} installed successfully[/green]")
                return True
            else:
                console.print(f"[red]✗ Failed to install {package}[/red]")
                console.print(f"Error: {result.stderr}")
                return False

        except Exception as e:
            console.print(f"[red]Installation error: {e}[/red]")
            return False

    def _show_detailed_status(self):
        """Show detailed status of all providers."""
        console.print("\n[bold]Detailed Provider Status[/bold]")

        status_summary = get_provider_status_summary()

        for provider, status in status_summary.items():
            # Determine status color
            if status['status'] == 'ready':
                status_color = 'green'
                status_icon = '✓'
            elif status['status'] in ['needs_key', 'key_invalid']:
                status_color = 'yellow'
                status_icon = '⚠'
            else:
                status_color = 'red'
                status_icon = '✗'

            console.print(f"\n[bold]{provider.title()}:[/bold]")
            console.print(f"  Package: {'✓' if status['package_installed'] else '✗'}")
            console.print(f"  API Key: {'✓' if status['api_key_available'] else '✗'}")
            console.print(f"  Status: [{status_color}]{status_icon} {status['status']}[/{status_color}]")
            console.print(f"  Message: {status['message']}")

    def _show_installation_guide(self):
        """Show installation guide for all providers."""
        console.print("\n[bold]Installation Guide[/bold]")

        instructions = get_installation_instructions()

        for provider, steps in instructions.items():
            console.print(f"\n[bold cyan]{provider.title()}:[/bold cyan]")
            for step in steps:
                if step.startswith('#'):
                    console.print(f"  [dim]{step}[/dim]")
                else:
                    console.print(f"  {step}")

    def _test_current_setup(self):
        """Test the current configuration."""
        console.print("\n[bold]Testing Current Setup[/bold]")

        current_mode = self.config.get('ai_provider', {}).get('mode', 'none')

        if current_mode == 'none':
            console.print("[green]✓ Manual mode - no testing required[/green]")
            console.print("Manual mode is always available")
        else:
            console.print(f"Testing {current_mode} configuration...")

            # Test API connection
            status_summary = get_provider_status_summary()
            provider_status = status_summary.get(current_mode, {})

            if provider_status.get('status') == 'ready':
                console.print(f"[green]✓ {current_mode.title()} is working correctly[/green]")
            else:
                console.print(f"[red]✗ {provider_status.get('message', 'Unknown error')}[/red]")

    def _reset_to_manual(self):
        """Reset configuration to manual mode."""
        if Confirm.ask("Reset to manual mode? This will disable AI API usage"):
            if 'ai_provider' not in self.config:
                self.config['ai_provider'] = {}

            self.config['ai_provider']['mode'] = 'none'
            self.config['ai_provider']['anthropic_api_key'] = None
            self.config['ai_provider']['openai_api_key'] = None
            self.config['ai_provider']['cursor_api_key'] = None

            self._save_config(self.config)
            console.print("[green]✓ Reset to manual mode[/green]")

def main():
    """Main entry point for setup wizard."""
    try:
        wizard = SetupWizard()
        wizard.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup wizard cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Setup wizard error: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
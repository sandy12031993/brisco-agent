"""
Provider detection and validation utility for AI providers.
"""

import os
import importlib
import logging
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

def detect_available_providers() -> Dict[str, bool]:
    """
    Check which AI providers are available based on installed packages.

    Returns:
        Dict mapping provider names to availability status
    """
    providers = {
        'anthropic': False,
        'openai': False,
        'cursor': False
    }

    # Check Anthropic
    try:
        import anthropic
        providers['anthropic'] = True
        logger.debug("Anthropic package found")
    except ImportError:
        logger.debug("Anthropic package not installed")

    # Check OpenAI
    try:
        import openai
        providers['openai'] = True
        logger.debug("OpenAI package found")
    except ImportError:
        logger.debug("OpenAI package not installed")

    # Check Cursor (placeholder - would depend on actual Cursor API package)
    try:
        # This would be the actual Cursor API package when available
        # import cursor_api
        # providers['cursor'] = True
        pass
    except ImportError:
        pass

    return providers

def detect_available_api_keys() -> Dict[str, bool]:
    """
    Check which API keys are available in environment variables.

    Returns:
        Dict mapping provider names to API key availability
    """
    api_keys = {
        'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'cursor': bool(os.getenv('CURSOR_API_KEY'))
    }

    return api_keys

def get_recommended_mode(config: Dict) -> Tuple[str, str]:
    """
    Recommend best AI mode based on available packages and API keys.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (recommended_mode, reason)
    """
    available_providers = detect_available_providers()
    available_keys = detect_available_api_keys()

    # Current mode from config
    current_mode = config.get('ai_provider', {}).get('mode', 'none')

    # Check if current mode is valid
    if current_mode != 'none':
        if available_providers.get(current_mode, False) and available_keys.get(current_mode, False):
            return current_mode, f"Current mode '{current_mode}' is working"
        elif available_providers.get(current_mode, False):
            return 'none', f"'{current_mode}' package available but API key missing"
        else:
            return 'none', f"'{current_mode}' package not installed"

    # Recommend based on availability
    for provider in ['anthropic', 'openai', 'cursor']:
        if available_providers.get(provider, False) and available_keys.get(provider, False):
            return provider, f"Found working {provider} setup"

    # Check for packages without keys
    for provider in ['anthropic', 'openai', 'cursor']:
        if available_providers.get(provider, False):
            return 'none', f"{provider} package available but needs API key"

    return 'none', "No AI packages installed - using manual mode"

def validate_api_key(provider: str, api_key: str) -> Tuple[bool, str]:
    """
    Test if an API key is valid for the specified provider.

    Args:
        provider: Provider name ('anthropic', 'openai', 'cursor')
        api_key: API key to validate

    Returns:
        Tuple of (is_valid, message)
    """
    if not api_key or api_key.strip() == '':
        return False, "API key is empty"

    try:
        if provider == 'anthropic':
            return _validate_anthropic_key(api_key)
        elif provider == 'openai':
            return _validate_openai_key(api_key)
        elif provider == 'cursor':
            return _validate_cursor_key(api_key)
        else:
            return False, f"Unknown provider: {provider}"

    except Exception as e:
        return False, f"Validation error: {str(e)}"

def _validate_anthropic_key(api_key: str) -> Tuple[bool, str]:
    """Validate Anthropic API key."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        # Make a minimal test request
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )

        return True, "Anthropic API key is valid"

    except ImportError:
        return False, "Anthropic package not installed"
    except anthropic.AuthenticationError:
        return False, "Invalid Anthropic API key"
    except anthropic.RateLimitError:
        return False, "Anthropic rate limit exceeded (key likely valid)"
    except Exception as e:
        return False, f"Anthropic validation error: {str(e)}"

def _validate_openai_key(api_key: str) -> Tuple[bool, str]:
    """Validate OpenAI API key."""
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)

        # Make a minimal test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10
        )

        return True, "OpenAI API key is valid"

    except ImportError:
        return False, "OpenAI package not installed"
    except openai.AuthenticationError:
        return False, "Invalid OpenAI API key"
    except openai.RateLimitError:
        return False, "OpenAI rate limit exceeded (key likely valid)"
    except Exception as e:
        return False, f"OpenAI validation error: {str(e)}"

def _validate_cursor_key(api_key: str) -> Tuple[bool, str]:
    """Validate Cursor API key (placeholder)."""
    # This would be implemented when Cursor API becomes available
    return False, "Cursor API validation not yet implemented"

def get_provider_status_summary() -> Dict[str, Dict]:
    """
    Get a comprehensive status summary for all providers.

    Returns:
        Dict with detailed status for each provider
    """
    available_providers = detect_available_providers()
    available_keys = detect_available_api_keys()

    status = {}

    for provider in ['anthropic', 'openai', 'cursor']:
        package_available = available_providers.get(provider, False)
        key_available = available_keys.get(provider, False)

        if package_available and key_available:
            # Validate the key
            env_key = os.getenv(f"{provider.upper()}_API_KEY")
            is_valid, message = validate_api_key(provider, env_key)

            status[provider] = {
                'package_installed': True,
                'api_key_available': True,
                'api_key_valid': is_valid,
                'status': 'ready' if is_valid else 'key_invalid',
                'message': message
            }
        elif package_available:
            status[provider] = {
                'package_installed': True,
                'api_key_available': False,
                'api_key_valid': False,
                'status': 'needs_key',
                'message': f"Package installed, set {provider.upper()}_API_KEY environment variable"
            }
        else:
            status[provider] = {
                'package_installed': False,
                'api_key_available': key_available,
                'api_key_valid': False,
                'status': 'needs_package',
                'message': f"Install package: pip install {provider}"
            }

    return status

def get_installation_instructions() -> Dict[str, List[str]]:
    """
    Get installation instructions for each provider.

    Returns:
        Dict mapping provider names to installation steps
    """
    instructions = {
        'anthropic': [
            "pip install anthropic>=0.18.0",
            "export ANTHROPIC_API_KEY=your_api_key_here",
            "# Get API key from: https://console.anthropic.com/"
        ],
        'openai': [
            "pip install openai>=1.0.0",
            "export OPENAI_API_KEY=your_api_key_here",
            "# Get API key from: https://platform.openai.com/api-keys"
        ],
        'cursor': [
            "# Cursor integration not yet available",
            "# Will be implemented when Cursor API is released"
        ]
    }

    return instructions

def resolve_api_key(provider: str, config_key: Optional[str]) -> Optional[str]:
    """
    Resolve API key from config or environment variables.

    Args:
        provider: Provider name
        config_key: API key from config (may be None or env var reference)

    Returns:
        Resolved API key or None
    """
    # Check if config_key is an environment variable reference
    if config_key and isinstance(config_key, str):
        if config_key.startswith('${') and config_key.endswith('}'):
            # Extract env var name: ${VAR_NAME} -> VAR_NAME
            env_var = config_key[2:-1]
            return os.getenv(env_var)
        elif config_key != 'null' and config_key is not None:
            # Direct API key
            return config_key

    # Fallback to standard environment variable
    env_var_map = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'cursor': 'CURSOR_API_KEY'
    }

    env_var = env_var_map.get(provider)
    if env_var:
        return os.getenv(env_var)

    return None
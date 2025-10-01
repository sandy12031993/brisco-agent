"""
Flexible AI helper that works with or without API keys.
Supports: Anthropic, OpenAI, Cursor, or Manual (Claude Code) mode.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
from datetime import datetime
import hashlib

from .provider_checker import resolve_api_key, validate_api_key

logger = logging.getLogger(__name__)

class TokenBudgetManager:
    """Manages token usage across sessions and requests."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('token_budget', {})
        self.max_per_analysis = self.config.get('max_tokens_per_analysis', 3000)
        self.max_per_session = self.config.get('max_tokens_per_session', 30000)
        self.warn_percentage = self.config.get('warn_at_percentage', 80)
        self.track_usage = self.config.get('track_usage', True)

        self.session_usage = 0
        self.request_count = 0

    def can_make_request(self, estimated_tokens: int) -> Tuple[bool, str]:
        """Check if a request can be made within budget."""
        if estimated_tokens > self.max_per_analysis:
            return False, f"Request exceeds per-analysis limit ({estimated_tokens} > {self.max_per_analysis})"

        if self.session_usage + estimated_tokens > self.max_per_session:
            return False, f"Request would exceed session limit ({self.session_usage + estimated_tokens} > {self.max_per_session})"

        return True, "Within budget"

    def record_usage(self, tokens_used: int):
        """Record token usage."""
        if self.track_usage:
            self.session_usage += tokens_used
            self.request_count += 1

            # Check if we're approaching limits
            session_percentage = (self.session_usage / self.max_per_session) * 100
            if session_percentage >= self.warn_percentage:
                logger.warning(f"Token usage at {session_percentage:.1f}% of session limit")

    def get_usage_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        return {
            'session_usage': self.session_usage,
            'session_limit': self.max_per_session,
            'session_percentage': (self.session_usage / self.max_per_session) * 100,
            'request_count': self.request_count,
            'remaining_tokens': self.max_per_session - self.session_usage
        }

class AIHelper:
    """
    Flexible AI helper that works with or without API keys.
    Supports: Anthropic, OpenAI, Cursor, or Manual (Claude Code) mode
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ai_config = config.get('ai_provider', {})
        self.mode = self.ai_config.get('mode', 'none')

        # Initialize token budget manager
        self.token_manager = TokenBudgetManager(config)

        # Initialize provider
        self.provider = None
        self.provider_config = {}

        if self.mode != 'none':
            self.provider, self.provider_config = self._init_provider()

        # Manual export settings
        self.manual_export_path = self.ai_config.get('manual_export_path', 'claude_context')
        self.fallback_to_manual = self.ai_config.get('fallback_to_manual', True)

        logger.info(f"AIHelper initialized in '{self.mode}' mode")

    def _init_provider(self) -> Tuple[Optional[Any], Dict[str, Any]]:
        """Initialize the selected AI provider."""
        provider_config = self.ai_config.get('token_limits', {}).get(self.mode, {})

        try:
            if self.mode == 'anthropic':
                return self._init_anthropic_provider(provider_config)
            elif self.mode == 'openai':
                return self._init_openai_provider(provider_config)
            elif self.mode == 'cursor':
                return self._init_cursor_provider(provider_config)
            else:
                logger.warning(f"Unknown provider mode: {self.mode}")
                return None, {}

        except Exception as e:
            logger.error(f"Failed to initialize {self.mode} provider: {e}")
            if self.fallback_to_manual:
                logger.info("Falling back to manual mode")
                self.mode = 'none'
            return None, {}

    def _init_anthropic_provider(self, config: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Initialize Anthropic provider."""
        try:
            import anthropic

            api_key = resolve_api_key('anthropic', self.ai_config.get('anthropic_api_key'))
            if not api_key:
                raise ValueError("Anthropic API key not found")

            # Validate API key
            is_valid, message = validate_api_key('anthropic', api_key)
            if not is_valid:
                raise ValueError(f"Invalid Anthropic API key: {message}")

            client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic provider initialized successfully")

            return client, config

        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic>=0.18.0")

    def _init_openai_provider(self, config: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Initialize OpenAI provider."""
        try:
            import openai

            api_key = resolve_api_key('openai', self.ai_config.get('openai_api_key'))
            if not api_key:
                raise ValueError("OpenAI API key not found")

            # Validate API key
            is_valid, message = validate_api_key('openai', api_key)
            if not is_valid:
                raise ValueError(f"Invalid OpenAI API key: {message}")

            client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI provider initialized successfully")

            return client, config

        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai>=1.0.0")

    def _init_cursor_provider(self, config: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
        """Initialize Cursor provider (placeholder)."""
        # This would be implemented when Cursor API becomes available
        raise NotImplementedError("Cursor provider not yet implemented")

    def analyze_with_ai(
        self,
        context: Dict[str, Any],
        prompt: str,
        max_tokens: Optional[int] = None,
        analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Analyze with AI if available, otherwise prepare for manual review.

        Args:
            context: Analysis context and data
            prompt: AI prompt for analysis
            max_tokens: Maximum tokens for response
            analysis_type: Type of analysis (for manual export naming)

        Returns:
            Analysis result with AI response or manual export info
        """
        if max_tokens is None:
            max_tokens = self.provider_config.get('max_tokens_per_request', 3000)

        # Check token budget
        can_proceed, budget_message = self.token_manager.can_make_request(max_tokens)
        if not can_proceed:
            logger.warning(f"Token budget exceeded: {budget_message}")
            return self._prepare_for_manual_review(context, prompt, max_tokens, analysis_type, budget_message)

        # Try API call if provider available
        if self.mode != 'none' and self.provider is not None:
            try:
                result = self._call_api(context, prompt, max_tokens)
                if result.get('success', False):
                    # Record token usage
                    tokens_used = result.get('tokens_used', max_tokens // 2)  # Estimate if not provided
                    self.token_manager.record_usage(tokens_used)
                    return result
                else:
                    logger.warning(f"API call failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"API call error: {e}")

            # Fallback to manual if API fails and fallback enabled
            if self.fallback_to_manual:
                logger.info("Falling back to manual review due to API failure")
                return self._prepare_for_manual_review(context, prompt, max_tokens, analysis_type, f"API failure: {str(e)}")

        # Manual mode or fallback
        return self._prepare_for_manual_review(context, prompt, max_tokens, analysis_type)

    def _call_api(self, context: Dict[str, Any], prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call the configured API provider."""
        try:
            if self.mode == 'anthropic':
                return self._call_anthropic_api(context, prompt, max_tokens)
            elif self.mode == 'openai':
                return self._call_openai_api(context, prompt, max_tokens)
            elif self.mode == 'cursor':
                return self._call_cursor_api(context, prompt, max_tokens)
            else:
                return {'success': False, 'error': f'Unknown provider: {self.mode}'}

        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {'success': False, 'error': str(e)}

    def _call_anthropic_api(self, context: Dict[str, Any], prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        try:
            # Prepare the message
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context:\n{context_str}\n\nAnalysis Request:\n{prompt}"

            response = self.provider.messages.create(
                model=self.provider_config.get('model', 'claude-3-5-sonnet-20241022'),
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": full_prompt}]
            )

            return {
                'success': True,
                'provider': 'anthropic',
                'response': response.content[0].text,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'model': self.provider_config.get('model'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': f'Anthropic API error: {str(e)}'}

    def _call_openai_api(self, context: Dict[str, Any], prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call OpenAI API."""
        try:
            # Prepare the message
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context:\n{context_str}\n\nAnalysis Request:\n{prompt}"

            response = self.provider.chat.completions.create(
                model=self.provider_config.get('model', 'gpt-4-turbo-preview'),
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=max_tokens
            )

            return {
                'success': True,
                'provider': 'openai',
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': self.provider_config.get('model'),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'success': False, 'error': f'OpenAI API error: {str(e)}'}

    def _call_cursor_api(self, context: Dict[str, Any], prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Call Cursor API (placeholder)."""
        return {'success': False, 'error': 'Cursor API not yet implemented'}

    def _prepare_for_manual_review(
        self,
        context: Dict[str, Any],
        prompt: str,
        max_tokens: int,
        analysis_type: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """Prepare analysis for manual review with Claude Code/Cursor."""
        try:
            # Create export directory
            export_dir = Path(self.manual_export_path)
            export_dir.mkdir(exist_ok=True)

            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            context_hash = hashlib.md5(json.dumps(context, sort_keys=True).encode()).hexdigest()[:8]
            filename = f"{analysis_type}_{timestamp}_{context_hash}.md"
            export_path = export_dir / filename

            # Prepare content for Claude Code
            content = self._format_for_claude_code(context, prompt, analysis_type, reason)

            # Write to file
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Manual review context exported to: {export_path}")

            return {
                'success': True,
                'mode': 'manual',
                'export_path': str(export_path),
                'analysis_type': analysis_type,
                'instructions': self._get_manual_instructions(),
                'reason': reason or 'Manual mode selected',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to prepare manual review: {e}")
            return {
                'success': False,
                'error': f'Manual export failed: {str(e)}',
                'mode': 'manual'
            }

    def _format_for_claude_code(self, context: Dict[str, Any], prompt: str, analysis_type: str, reason: str) -> str:
        """Format analysis context for Claude Code review."""
        content = f"""# Migration Analysis - {analysis_type.replace('_', ' ').title()}

**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Analysis Type**: {analysis_type}
**Reason**: {reason or 'Manual mode selected'}

## Analysis Request

{prompt}

## Context Data

```json
{json.dumps(context, indent=2)}
```

## Instructions for Claude Code Analysis

Please analyze the above context and provide insights on:

1. **Security Assessment**: Identify any critical security vulnerabilities
2. **Migration Recommendations**: Suggest Laravel equivalents and migration steps
3. **Code Quality**: Assess maintainability and best practices
4. **Architecture Patterns**: Identify patterns and suggest improvements
5. **Risk Assessment**: Evaluate migration complexity and potential issues

## Expected Output Format

```markdown
### Security Analysis
- [List critical security issues]
- [Recommend fixes]

### Migration Plan
- [Priority: High/Medium/Low]
- [Required Laravel components]
- [Step-by-step migration approach]

### Code Quality Assessment
- [Maintainability score]
- [Technical debt items]
- [Refactoring recommendations]

### Risks and Mitigation
- [Potential migration risks]
- [Mitigation strategies]
- [Testing recommendations]
```

## Additional Context

- **Project**: PHP 5.6 to Laravel 7.4 + Vue.js migration
- **Scope**: {len(context.get('files', []))} files analyzed
- **Focus Areas**: Security, modernization, maintainability

---

*This context was generated by the PHP-to-Laravel Migration Analysis System*
*For questions about the analysis system, refer to the README.md*
"""
        return content

    def _get_manual_instructions(self) -> List[str]:
        """Get instructions for manual analysis workflow."""
        return [
            "Open the exported .md file in Claude Code or Cursor",
            "Review the context and analysis request",
            "Provide analysis following the suggested format",
            "Save results back to the claude_context directory",
            "Use the insights to update your migration planning"
        ]

    def is_manual_mode(self) -> bool:
        """Check if running in manual mode (no API)."""
        return self.mode == 'none' or self.provider is None

    def get_provider_info(self) -> Dict[str, Any]:
        """Get current provider information."""
        info = {
            'mode': self.mode,
            'is_manual': self.is_manual_mode(),
            'provider_available': self.provider is not None,
            'fallback_enabled': self.fallback_to_manual,
            'token_usage': self.token_manager.get_usage_summary()
        }

        if self.provider is not None:
            info.update({
                'model': self.provider_config.get('model'),
                'max_tokens': self.provider_config.get('max_tokens_per_request'),
                'context_window': self.provider_config.get('context_window')
            })

        return info

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4

    def can_handle_context(self, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if context size is within limits."""
        context_str = json.dumps(context)
        estimated_tokens = self.estimate_tokens(context_str)

        max_context = self.provider_config.get('context_window', 200000)

        if estimated_tokens > max_context * 0.8:  # Leave room for prompt and response
            return False, f"Context too large: {estimated_tokens} tokens (limit: {max_context * 0.8})"

        return True, "Context size acceptable"

    def split_large_context(self, context: Dict[str, Any], max_size: int = None) -> List[Dict[str, Any]]:
        """Split large context into smaller chunks for processing."""
        if max_size is None:
            max_size = self.provider_config.get('context_window', 200000) // 2

        # Simple splitting by files (more sophisticated splitting could be implemented)
        if 'files' in context and len(context['files']) > 1:
            chunks = []
            current_chunk = {k: v for k, v in context.items() if k != 'files'}
            current_size = self.estimate_tokens(json.dumps(current_chunk))

            for file_data in context['files']:
                file_size = self.estimate_tokens(json.dumps(file_data))

                if current_size + file_size > max_size and current_chunk.get('files'):
                    # Start new chunk
                    chunks.append(current_chunk)
                    current_chunk = {k: v for k, v in context.items() if k != 'files'}
                    current_chunk['files'] = []
                    current_size = self.estimate_tokens(json.dumps(current_chunk))

                current_chunk.setdefault('files', []).append(file_data)
                current_size += file_size

            if current_chunk.get('files'):
                chunks.append(current_chunk)

            return chunks

        return [context]
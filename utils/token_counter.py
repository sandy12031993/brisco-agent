"""
Token counting and text truncation utilities for managing output within token budgets.
"""

import json
import re
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path


class TokenCounter:
    """Utility for estimating token counts and managing text within token budgets."""

    # Approximation: ~4 characters per token (conservative estimate)
    CHARS_PER_TOKEN = 4

    def __init__(self):
        self.token_counts = {}

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text using character approximation.

        Args:
            text: Input text to estimate

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        # Clean up text for more accurate counting
        cleaned_text = self._clean_text(text)

        # Base character count
        char_count = len(cleaned_text)

        # Adjust for common patterns that affect tokenization
        token_estimate = char_count / self.CHARS_PER_TOKEN

        # Account for common token patterns
        token_estimate *= self._get_token_multiplier(cleaned_text)

        return int(token_estimate)

    def _clean_text(self, text: str) -> str:
        """Clean text for token estimation."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text

    def _get_token_multiplier(self, text: str) -> float:
        """
        Adjust token estimate based on text patterns.

        Different types of content tokenize differently:
        - Code: More tokens per character
        - Natural language: Fewer tokens per character
        - JSON/structured data: Variable
        """
        # Count patterns that affect tokenization
        code_indicators = len(re.findall(r'[{}()[\];,.]', text))
        word_count = len(text.split())

        if word_count == 0:
            return 1.0

        # Higher ratio of punctuation suggests code/structured data
        punctuation_ratio = code_indicators / len(text) if text else 0

        if punctuation_ratio > 0.1:
            return 1.2  # Code uses more tokens
        elif punctuation_ratio < 0.02:
            return 0.9  # Natural language uses fewer tokens
        else:
            return 1.0  # Balanced content

    def truncate_to_tokens(self, text: str, max_tokens: int, suffix: str = "...") -> str:
        """
        Truncate text to fit within token budget.

        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            suffix: Suffix to add when truncating

        Returns:
            Truncated text that fits within token budget
        """
        current_tokens = self.estimate_tokens(text)

        if current_tokens <= max_tokens:
            return text

        # Reserve tokens for suffix
        suffix_tokens = self.estimate_tokens(suffix)
        available_tokens = max_tokens - suffix_tokens

        if available_tokens <= 0:
            return suffix[:max_tokens * self.CHARS_PER_TOKEN]

        # Estimate character limit
        target_chars = available_tokens * self.CHARS_PER_TOKEN

        # Truncate text, trying to break at word boundaries
        if len(text) <= target_chars:
            return text

        # Find last space before target
        truncate_pos = target_chars
        space_pos = text.rfind(' ', 0, truncate_pos)

        if space_pos > target_chars * 0.8:  # If space is reasonably close
            truncate_pos = space_pos

        truncated = text[:truncate_pos] + suffix

        # Verify we're within budget
        if self.estimate_tokens(truncated) > max_tokens:
            # More aggressive truncation
            reduction_factor = 0.9
            while self.estimate_tokens(truncated) > max_tokens and reduction_factor > 0.5:
                new_length = int(len(text) * reduction_factor)
                truncated = text[:new_length] + suffix
                reduction_factor -= 0.1

        return truncated

    def format_data_for_tokens(self, data: Dict[str, Any], max_tokens: int,
                              priority_order: List[str] = None) -> Dict[str, Any]:
        """
        Format data structure to fit within token budget, prioritizing important fields.

        Args:
            data: Data structure to format
            max_tokens: Maximum tokens allowed
            priority_order: Order of field importance (high to low priority)

        Returns:
            Formatted data that fits within token budget
        """
        if not priority_order:
            priority_order = ['errors', 'critical_issues', 'security_issues',
                            'warnings', 'recommendations', 'summary', 'info']

        # Calculate current size
        current_text = json.dumps(data, indent=2)
        current_tokens = self.estimate_tokens(current_text)

        if current_tokens <= max_tokens:
            return data

        # Start with a copy and progressively reduce
        formatted_data = data.copy()

        # First pass: truncate long lists in priority order
        for field in priority_order:
            if field in formatted_data and isinstance(formatted_data[field], list):
                # Keep most important items, summarize rest
                items = formatted_data[field]
                if len(items) > 5:
                    formatted_data[field] = items[:5]
                    formatted_data[f"{field}_summary"] = f"Showing top 5 of {len(items)} {field}"

                # Check if we're within budget now
                current_text = json.dumps(formatted_data, indent=2)
                if self.estimate_tokens(current_text) <= max_tokens:
                    break

        # Second pass: truncate long text fields
        for key, value in formatted_data.items():
            if isinstance(value, str) and len(value) > 200:
                # Allocate tokens proportionally
                field_budget = max_tokens // (len(formatted_data) + 1)
                formatted_data[key] = self.truncate_to_tokens(value, field_budget)

        # Final check
        current_text = json.dumps(formatted_data, indent=2)
        if self.estimate_tokens(current_text) > max_tokens:
            # More aggressive reduction - keep only highest priority fields
            essential_fields = priority_order[:3] + ['summary']
            formatted_data = {k: v for k, v in formatted_data.items()
                            if k in essential_fields or not k.endswith('_summary')}

        return formatted_data

    def estimate_file_analysis_tokens(self, file_path: str) -> int:
        """
        Estimate tokens needed for file analysis based on file size and type.

        Args:
            file_path: Path to file to analyze

        Returns:
            Estimated tokens for analysis output
        """
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            extension = path.suffix.lower()

            # Base estimation based on file size
            # Rough approximation: analysis output is ~10% of file size in tokens
            base_tokens = (file_size // self.CHARS_PER_TOKEN) * 0.1

            # Adjust based on file type
            multipliers = {
                '.php': 1.5,    # PHP files have more complex analysis
                '.js': 1.3,     # JavaScript analysis
                '.vue': 1.4,    # Vue components
                '.sql': 1.2,    # SQL analysis
                '.json': 0.8,   # JSON is more structured
                '.txt': 0.5,    # Plain text
                '.md': 0.6,     # Markdown
            }

            multiplier = multipliers.get(extension, 1.0)
            estimated_tokens = int(base_tokens * multiplier)

            # Set reasonable bounds
            min_tokens = 100
            max_tokens = 10000

            return max(min_tokens, min(estimated_tokens, max_tokens))

        except Exception:
            # Default estimation if file operations fail
            return 1000

    def get_summary_stats(self, texts: List[str]) -> Dict[str, Any]:
        """
        Get token statistics for a list of texts.

        Args:
            texts: List of texts to analyze

        Returns:
            Dictionary with token statistics
        """
        if not texts:
            return {
                'total_tokens': 0,
                'average_tokens': 0,
                'min_tokens': 0,
                'max_tokens': 0,
                'count': 0
            }

        token_counts = [self.estimate_tokens(text) for text in texts]

        return {
            'total_tokens': sum(token_counts),
            'average_tokens': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts),
            'count': len(token_counts)
        }

    def optimize_json_for_tokens(self, data: Any, max_tokens: int) -> str:
        """
        Optimize JSON output for token efficiency.

        Args:
            data: Data to serialize
            max_tokens: Maximum tokens allowed

        Returns:
            JSON string optimized for token count
        """
        # Try different JSON formatting approaches
        formats_to_try = [
            # Most compact
            lambda d: json.dumps(d, separators=(',', ':')),
            # Slightly readable
            lambda d: json.dumps(d, separators=(',', ': ')),
            # Standard formatting
            lambda d: json.dumps(d, indent=2),
        ]

        for format_func in formats_to_try:
            json_str = format_func(data)
            if self.estimate_tokens(json_str) <= max_tokens:
                return json_str

        # If still too large, truncate the data
        formatted_data = self.format_data_for_tokens(data, max_tokens)
        return json.dumps(formatted_data, separators=(',', ':'))


# Global instance for easy access
token_counter = TokenCounter()


def estimate_tokens(text: str) -> int:
    """Convenience function for token estimation."""
    return token_counter.estimate_tokens(text)


def truncate_to_tokens(text: str, max_tokens: int, suffix: str = "...") -> str:
    """Convenience function for text truncation."""
    return token_counter.truncate_to_tokens(text, max_tokens, suffix)


def format_for_tokens(data: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
    """Convenience function for data formatting."""
    return token_counter.format_data_for_tokens(data, max_tokens)
"""
Token usage tracking system for monitoring and optimizing analysis output.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .token_counter import token_counter


class TokenTracker:
    """
    Tracks token usage across analysis sessions for budget management and optimization.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to knowledge directory
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
            knowledge_dir.mkdir(exist_ok=True)
            db_path = knowledge_dir / "token_usage.db"

        self.db_path = str(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize the token usage database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    command TEXT NOT NULL,
                    format_type TEXT NOT NULL,
                    input_path TEXT,
                    output_path TEXT,
                    tokens_used INTEGER NOT NULL,
                    max_tokens INTEGER,
                    estimated_tokens INTEGER,
                    session_id TEXT,
                    focus_area TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON token_usage(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_command ON token_usage(command)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session ON token_usage(session_id)
            """)

    def record_usage(self, command: str, format_type: str, tokens_used: int,
                    max_tokens: Optional[int] = None, input_path: Optional[str] = None,
                    output_path: Optional[str] = None, estimated_tokens: Optional[int] = None,
                    session_id: Optional[str] = None, focus_area: Optional[str] = None,
                    success: bool = True, metadata: Optional[Dict] = None):
        """
        Record token usage for an analysis operation.

        Args:
            command: CLI command used
            format_type: Output format type
            tokens_used: Actual tokens used
            max_tokens: Maximum tokens allowed
            input_path: Input file/directory path
            output_path: Output file path
            estimated_tokens: Estimated tokens before analysis
            session_id: Session identifier
            focus_area: Focus area (migration, security, etc.)
            success: Whether operation succeeded
            metadata: Additional metadata
        """
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO token_usage
                (timestamp, command, format_type, input_path, output_path,
                 tokens_used, max_tokens, estimated_tokens, session_id,
                 focus_area, success, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, command, format_type, input_path, output_path,
                  tokens_used, max_tokens, estimated_tokens, session_id,
                  focus_area, success, metadata_json))

    def get_usage_stats(self, period: str = 'today') -> Dict[str, Any]:
        """
        Get token usage statistics for a specified period.

        Args:
            period: 'session', 'today', 'week', or 'all'

        Returns:
            Dictionary with usage statistics
        """
        # Calculate time filter
        now = datetime.now()
        if period == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_time = now - timedelta(days=7)
        elif period == 'session':
            # Get current session (last 2 hours of activity)
            start_time = now - timedelta(hours=2)
        else:  # 'all'
            start_time = datetime.min

        start_time_str = start_time.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Basic stats
            stats_query = """
                SELECT
                    COUNT(*) as analyses_run,
                    SUM(tokens_used) as total_tokens,
                    AVG(tokens_used) as avg_tokens,
                    MIN(tokens_used) as min_tokens,
                    MAX(tokens_used) as max_tokens,
                    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_analyses,
                    COUNT(CASE WHEN success = 0 THEN 1 END) as failed_analyses
                FROM token_usage
                WHERE timestamp >= ?
            """

            basic_stats = conn.execute(stats_query, (start_time_str,)).fetchone()

            # Format distribution
            format_query = """
                SELECT
                    format_type,
                    COUNT(*) as count,
                    SUM(tokens_used) as total_tokens,
                    AVG(tokens_used) as avg_tokens
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY format_type
                ORDER BY count DESC
            """

            format_stats = conn.execute(format_query, (start_time_str,)).fetchall()

            # Command distribution
            command_query = """
                SELECT
                    command,
                    COUNT(*) as count,
                    SUM(tokens_used) as total_tokens
                FROM token_usage
                WHERE timestamp >= ?
                GROUP BY command
                ORDER BY count DESC
            """

            command_stats = conn.execute(command_query, (start_time_str,)).fetchall()

            # Focus area distribution
            focus_query = """
                SELECT
                    focus_area,
                    COUNT(*) as count,
                    AVG(tokens_used) as avg_tokens
                FROM token_usage
                WHERE timestamp >= ? AND focus_area IS NOT NULL
                GROUP BY focus_area
                ORDER BY count DESC
            """

            focus_stats = conn.execute(focus_query, (start_time_str,)).fetchall()

            # Efficiency metrics
            efficiency_query = """
                SELECT
                    AVG(CASE WHEN estimated_tokens > 0
                        THEN CAST(tokens_used AS FLOAT) / estimated_tokens
                        ELSE NULL END) as avg_efficiency_ratio,
                    COUNT(CASE WHEN estimated_tokens > 0 AND tokens_used <= estimated_tokens
                          THEN 1 END) as under_estimate_count,
                    COUNT(CASE WHEN estimated_tokens > 0 AND tokens_used > estimated_tokens
                          THEN 1 END) as over_estimate_count
                FROM token_usage
                WHERE timestamp >= ? AND estimated_tokens > 0
            """

            efficiency_stats = conn.execute(efficiency_query, (start_time_str,)).fetchone()

        # Compile results
        return {
            'period': period,
            'start_time': start_time_str,
            'basic_stats': {
                'analyses_run': basic_stats['analyses_run'] or 0,
                'total_tokens': basic_stats['total_tokens'] or 0,
                'avg_tokens': round(basic_stats['avg_tokens'] or 0, 1),
                'min_tokens': basic_stats['min_tokens'] or 0,
                'max_tokens': basic_stats['max_tokens'] or 0,
                'successful_analyses': basic_stats['successful_analyses'] or 0,
                'failed_analyses': basic_stats['failed_analyses'] or 0,
                'success_rate': round((basic_stats['successful_analyses'] or 0) /
                                    max(basic_stats['analyses_run'] or 1, 1) * 100, 1)
            },
            'format_distribution': [dict(row) for row in format_stats],
            'command_distribution': [dict(row) for row in command_stats],
            'focus_distribution': [dict(row) for row in focus_stats],
            'efficiency_metrics': {
                'avg_efficiency_ratio': round(efficiency_stats['avg_efficiency_ratio'] or 1.0, 2),
                'under_estimate_count': efficiency_stats['under_estimate_count'] or 0,
                'over_estimate_count': efficiency_stats['over_estimate_count'] or 0
            }
        }

    def get_budget_status(self, budget_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check current usage against configured budgets.

        Args:
            budget_config: Budget configuration from config

        Returns:
            Budget status information
        """
        # Get session and daily usage
        session_stats = self.get_usage_stats('session')
        daily_stats = self.get_usage_stats('today')

        session_tokens = session_stats['basic_stats']['total_tokens']
        daily_tokens = daily_stats['basic_stats']['total_tokens']

        # Extract budget limits
        max_per_session = budget_config.get('max_tokens_per_session', 30000)
        max_per_day = budget_config.get('max_tokens_per_day', 100000)
        warn_percentage = budget_config.get('warn_at_percentage', 80)

        # Calculate percentages
        session_percentage = (session_tokens / max_per_session) * 100
        daily_percentage = (daily_tokens / max_per_day) * 100

        # Determine status
        if session_percentage >= 100 or daily_percentage >= 100:
            status = 'exceeded'
        elif session_percentage >= warn_percentage or daily_percentage >= warn_percentage:
            status = 'warning'
        else:
            status = 'ok'

        return {
            'status': status,
            'session': {
                'used': session_tokens,
                'limit': max_per_session,
                'percentage': round(session_percentage, 1),
                'remaining': max(0, max_per_session - session_tokens)
            },
            'daily': {
                'used': daily_tokens,
                'limit': max_per_day,
                'percentage': round(daily_percentage, 1),
                'remaining': max(0, max_per_day - daily_tokens)
            },
            'warn_threshold': warn_percentage
        }

    def get_optimization_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """
        Generate optimization recommendations based on usage patterns.

        Args:
            stats: Usage statistics from get_usage_stats()

        Returns:
            List of recommendation strings
        """
        recommendations = []
        basic = stats['basic_stats']
        formats = stats['format_distribution']
        efficiency = stats['efficiency_metrics']

        # Analyze format usage
        if formats:
            # Check if using inefficient formats
            total_analyses = basic['analyses_run']
            detailed_usage = sum(f['count'] for f in formats if f['format_type'] == 'detailed')
            detailed_percentage = (detailed_usage / total_analyses) * 100 if total_analyses > 0 else 0

            if detailed_percentage > 50:
                recommendations.append("Consider using 'brief' or 'claude-summary' formats for routine analysis")

            # Check for high token usage
            if basic['avg_tokens'] > 4000:
                recommendations.append("Average token usage is high - consider shorter formats or focused analysis")

            # Look for format efficiency
            efficient_formats = [f for f in formats
                               if f['format_type'] in ['brief', 'claude-summary'] and f['avg_tokens'] < 2000]
            if not efficient_formats and total_analyses > 5:
                recommendations.append("Try 'brief' format for quick scans and overviews")

        # Analyze estimation accuracy
        if efficiency['avg_efficiency_ratio'] > 1.2:
            recommendations.append("Token estimates are conservative - consider increasing max_tokens limits")
        elif efficiency['avg_efficiency_ratio'] < 0.8:
            recommendations.append("Token usage often exceeds estimates - consider more detailed analysis")

        # Check failure rate
        if basic['success_rate'] < 90:
            recommendations.append("High failure rate detected - check input validation and error handling")

        # General efficiency tips
        if basic['analyses_run'] > 10:
            recommendations.append("For bulk analysis, consider using focused analysis with specific focus areas")

        if not recommendations:
            recommendations.append("Token usage patterns look optimal")

        return recommendations

    def cleanup_old_records(self, days_to_keep: int = 30):
        """
        Clean up old token usage records.

        Args:
            days_to_keep: Number of days of records to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                DELETE FROM token_usage
                WHERE timestamp < ?
            """, (cutoff_str,))

            deleted_count = result.rowcount

        return deleted_count

    def export_usage_data(self, output_path: str, period: str = 'all'):
        """
        Export usage data to JSON file.

        Args:
            output_path: Path to output JSON file
            period: Period to export ('today', 'week', 'all')
        """
        stats = self.get_usage_stats(period)

        # Get detailed records
        now = datetime.now()
        if period == 'today':
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_time = now - timedelta(days=7)
        else:  # 'all'
            start_time = datetime.min

        start_time_str = start_time.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            records = conn.execute("""
                SELECT * FROM token_usage
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (start_time_str,)).fetchall()

        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'period': period,
            'statistics': stats,
            'records': [dict(record) for record in records]
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        return len(records)

    def get_session_id(self) -> str:
        """Generate session ID based on current time."""
        return datetime.now().strftime("%Y%m%d_%H%M")

    def estimate_remaining_budget(self, budget_config: Dict[str, Any],
                                 planned_operations: List[Dict]) -> Dict[str, Any]:
        """
        Estimate if planned operations will fit within budget.

        Args:
            budget_config: Budget configuration
            planned_operations: List of planned operations with estimated tokens

        Returns:
            Budget projection information
        """
        budget_status = self.get_budget_status(budget_config)

        total_planned_tokens = sum(op.get('estimated_tokens', 1000) for op in planned_operations)

        session_remaining = budget_status['session']['remaining']
        daily_remaining = budget_status['daily']['remaining']

        session_fits = total_planned_tokens <= session_remaining
        daily_fits = total_planned_tokens <= daily_remaining

        return {
            'planned_tokens': total_planned_tokens,
            'session_remaining': session_remaining,
            'daily_remaining': daily_remaining,
            'fits_in_session': session_fits,
            'fits_in_daily': daily_fits,
            'recommended_format': 'brief' if total_planned_tokens > session_remaining else 'claude-summary'
        }


# Global instance for easy access
token_tracker = TokenTracker()


def record_token_usage(command: str, format_type: str, tokens_used: int, **kwargs):
    """Convenience function for recording token usage."""
    return token_tracker.record_usage(command, format_type, tokens_used, **kwargs)


def get_token_stats(period: str = 'today') -> Dict[str, Any]:
    """Convenience function for getting token statistics."""
    return token_tracker.get_usage_stats(period)


def check_budget_status(budget_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for checking budget status."""
    return token_tracker.get_budget_status(budget_config)
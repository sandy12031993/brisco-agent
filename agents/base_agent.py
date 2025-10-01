"""
Base Agent class for the PHP-to-Laravel migration analysis system.
"""

import json
import sqlite3
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import yaml

class BaseAgent(ABC):
    """Abstract base class for all analysis agents."""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.knowledge_db = self._init_knowledge_db()
        self.patterns = self._load_patterns()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the agent."""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, self.config['logging']['level']))

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(self.config['logging']['format'])
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _init_knowledge_db(self) -> sqlite3.Connection:
        """Initialize SQLite database for persistent knowledge."""
        db_path = Path(self.config['project']['root_path']) / ".agent" / self.config['knowledge']['insights_db']
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))

        # Create tables if they don't exist
        conn.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                file_path TEXT,
                insight_type TEXT,
                content TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                pattern_name TEXT,
                pattern_data TEXT,
                usage_count INTEGER DEFAULT 1,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_file TEXT,
                target_file TEXT,
                migration_type TEXT,
                status TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        return conn

    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns from JSON file."""
        patterns_path = Path(self.config['project']['root_path']) / ".agent" / self.config['knowledge']['patterns_file']

        if patterns_path.exists():
            with open(patterns_path, 'r') as file:
                return json.load(file)

        return {}

    def save_insight(self, file_path: str, insight_type: str, content: str, confidence: float = 0.8):
        """Save an insight to the knowledge database."""
        self.knowledge_db.execute(
            'INSERT INTO insights (agent_name, file_path, insight_type, content, confidence) VALUES (?, ?, ?, ?, ?)',
            (self.__class__.__name__, file_path, insight_type, content, confidence)
        )
        self.knowledge_db.commit()
        self.logger.info(f"Saved insight: {insight_type} for {file_path}")

    def get_insights(self, file_path: Optional[str] = None, insight_type: Optional[str] = None) -> List[Dict]:
        """Retrieve insights from the knowledge database."""
        query = 'SELECT * FROM insights WHERE agent_name = ?'
        params = [self.__class__.__name__]

        if file_path:
            query += ' AND file_path = ?'
            params.append(file_path)

        if insight_type:
            query += ' AND insight_type = ?'
            params.append(insight_type)

        query += ' ORDER BY created_at DESC'

        cursor = self.knowledge_db.execute(query, params)
        columns = [description[0] for description in cursor.description]

        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def save_pattern(self, pattern_name: str, pattern_data: Dict[str, Any]):
        """Save a learned pattern."""
        # Check if pattern exists
        cursor = self.knowledge_db.execute(
            'SELECT id, usage_count FROM patterns WHERE agent_name = ? AND pattern_name = ?',
            (self.__class__.__name__, pattern_name)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing pattern
            self.knowledge_db.execute(
                'UPDATE patterns SET pattern_data = ?, usage_count = ?, last_used = CURRENT_TIMESTAMP WHERE id = ?',
                (json.dumps(pattern_data), existing[1] + 1, existing[0])
            )
        else:
            # Insert new pattern
            self.knowledge_db.execute(
                'INSERT INTO patterns (agent_name, pattern_name, pattern_data) VALUES (?, ?, ?)',
                (self.__class__.__name__, pattern_name, json.dumps(pattern_data))
            )

        self.knowledge_db.commit()
        self.logger.info(f"Saved pattern: {pattern_name}")

    def get_patterns(self, pattern_name: Optional[str] = None) -> List[Dict]:
        """Retrieve learned patterns."""
        query = 'SELECT * FROM patterns WHERE agent_name = ?'
        params = [self.__class__.__name__]

        if pattern_name:
            query += ' AND pattern_name = ?'
            params.append(pattern_name)

        query += ' ORDER BY usage_count DESC, last_used DESC'

        cursor = self.knowledge_db.execute(query, params)
        columns = [description[0] for description in cursor.description]

        results = []
        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            result['pattern_data'] = json.loads(result['pattern_data'])
            results.append(result)

        return results

    @abstractmethod
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a specific file. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def analyze_module(self, module_path: str) -> Dict[str, Any]:
        """Analyze a module/directory. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a file. Must be implemented by subclasses."""
        pass

    def __del__(self):
        """Cleanup database connection."""
        if hasattr(self, 'knowledge_db'):
            self.knowledge_db.close()
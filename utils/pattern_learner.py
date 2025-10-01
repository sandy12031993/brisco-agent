#!/usr/bin/env python3
"""
Pattern Learning System for Migration Analysis.

This module handles learning from feedback and building pattern recognition
for improved migration recommendations.
"""

import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict


class PatternLearner:
    """Learns patterns from feedback and analysis to improve recommendations."""

    def __init__(self, knowledge_dir: str = None):
        """Initialize the pattern learner.

        Args:
            knowledge_dir: Directory to store knowledge files
        """
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
        else:
            knowledge_dir = Path(knowledge_dir)

        self.knowledge_dir = knowledge_dir
        self.knowledge_dir.mkdir(exist_ok=True)

        self.patterns_file = self.knowledge_dir / "patterns.json"
        self.insights_db = self.knowledge_dir / "learned_insights.db"

        self._init_patterns()
        self._init_database()

    def _init_patterns(self):
        """Initialize patterns file if it doesn't exist."""
        if not self.patterns_file.exists():
            initial_patterns = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "patterns": [],
                "categories": [
                    "frontend_backend_flow",
                    "security_improvements",
                    "api_integration",
                    "database_patterns",
                    "architecture_patterns",
                    "fresh_development"
                ]
            }
            self._save_patterns(initial_patterns)

    def _init_database(self):
        """Initialize the insights database."""
        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT,
                category TEXT,
                name TEXT,
                description TEXT,
                legacy_pattern TEXT,
                modern_equivalent TEXT,
                confidence REAL DEFAULT 0.5,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                created_at TEXT,
                last_used TEXT,
                related_files TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_file TEXT,
                feedback_file TEXT,
                patterns_learned INTEGER,
                insights_gained INTEGER,
                created_at TEXT,
                summary TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_transformations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT,
                before_code TEXT,
                after_code TEXT,
                language TEXT,
                framework TEXT,
                category TEXT,
                success_rate REAL,
                times_applied INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT,
                strategy_type TEXT,
                description TEXT,
                success_rate REAL,
                difficulty TEXT,
                estimated_hours REAL,
                dependencies TEXT,
                created_at TEXT,
                times_used INTEGER DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def _load_patterns(self) -> Dict:
        """Load patterns from file."""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r') as f:
                    data = json.load(f)
                    # Ensure 'patterns' key exists
                    if 'patterns' not in data:
                        data['patterns'] = []
                    return data
            except (json.JSONDecodeError, Exception):
                # If file is corrupted, return empty structure
                return {"patterns": []}
        return {"patterns": []}

    def _save_patterns(self, patterns: Dict):
        """Save patterns to file."""
        patterns["last_updated"] = datetime.now().isoformat()
        with open(self.patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

    def learn_from_feedback(self, analysis_file: str, feedback_file: str) -> Dict[str, Any]:
        """Learn patterns from analysis and feedback files.

        Args:
            analysis_file: Path to original analysis file
            feedback_file: Path to feedback markdown file

        Returns:
            Summary of learning results
        """
        analysis_path = Path(analysis_file)
        feedback_path = Path(feedback_file)

        if not analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {analysis_file}")
        if not feedback_path.exists():
            raise FileNotFoundError(f"Feedback file not found: {feedback_file}")

        # Read files
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_content = f.read()

        with open(feedback_path, 'r', encoding='utf-8') as f:
            feedback_content = f.read()

        # Extract insights from feedback
        patterns_learned = self._extract_patterns_from_feedback(feedback_content, analysis_content)
        insights_gained = self._extract_insights(feedback_content, analysis_content)
        transformations = self._extract_code_transformations(feedback_content)
        strategies = self._extract_migration_strategies(feedback_content)

        # Store learned patterns
        self._store_patterns(patterns_learned)
        self._store_insights(insights_gained)
        self._store_transformations(transformations)
        self._store_strategies(strategies)

        # Record feedback session
        self._record_feedback_session(
            str(analysis_path),
            str(feedback_path),
            len(patterns_learned),
            len(insights_gained)
        )

        return {
            "patterns_learned": len(patterns_learned),
            "insights_gained": len(insights_gained),
            "transformations_found": len(transformations),
            "strategies_identified": len(strategies),
            "summary": self._generate_learning_summary(
                patterns_learned, insights_gained, transformations, strategies
            )
        }

    def _extract_patterns_from_feedback(self, feedback: str, analysis: str) -> List[Dict]:
        """Extract migration patterns from feedback."""
        patterns = []

        # Look for pattern descriptions in feedback
        pattern_sections = re.findall(
            r'#+\s*Pattern[:\s]+(.+?)\n(.+?)(?=\n#+|\Z)',
            feedback,
            re.DOTALL | re.IGNORECASE
        )

        for pattern_name, pattern_content in pattern_sections:
            pattern = self._parse_pattern(pattern_name.strip(), pattern_content)
            if pattern:
                patterns.append(pattern)

        # Look for code examples with before/after
        code_patterns = self._extract_code_patterns(feedback)
        patterns.extend(code_patterns)

        return patterns

    def _parse_pattern(self, name: str, content: str) -> Optional[Dict]:
        """Parse a pattern from feedback content."""
        # Extract legacy and modern patterns
        legacy_match = re.search(r'Legacy[:\s]+(.+?)(?=Modern|$)', content, re.DOTALL | re.IGNORECASE)
        modern_match = re.search(r'Modern[:\s]+(.+?)(?=\n#+|$)', content, re.DOTALL | re.IGNORECASE)

        if not (legacy_match and modern_match):
            return None

        # Determine category
        category = self._categorize_pattern(name, content)

        return {
            "id": f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(name)}",
            "name": name,
            "category": category,
            "legacy_pattern": legacy_match.group(1).strip(),
            "modern_equivalent": modern_match.group(1).strip(),
            "confidence": 0.8,
            "success_count": 0,
            "related_files": []
        }

    def _extract_code_patterns(self, feedback: str) -> List[Dict]:
        """Extract before/after code patterns from feedback."""
        patterns = []

        # Find code blocks with before/after labels
        code_blocks = re.findall(
            r'```(\w+)?\n(.+?)```',
            feedback,
            re.DOTALL
        )

        # Group consecutive code blocks as before/after pairs
        for i in range(0, len(code_blocks) - 1, 2):
            lang1, code1 = code_blocks[i]
            lang2, code2 = code_blocks[i + 1]

            # Check if this looks like a before/after pattern
            before_idx = feedback.find(code1)
            after_idx = feedback.find(code2)

            if after_idx > before_idx:
                between_text = feedback[before_idx:after_idx].lower()
                if any(keyword in between_text for keyword in ['after', 'becomes', 'modern', 'laravel', '->', '=>']):
                    pattern_name = self._infer_pattern_name(code1, code2)
                    patterns.append({
                        "id": f"code_pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                        "name": pattern_name,
                        "category": "code_transformation",
                        "legacy_pattern": code1.strip(),
                        "modern_equivalent": code2.strip(),
                        "confidence": 0.9,
                        "success_count": 1,
                        "related_files": []
                    })

        return patterns

    def _extract_insights(self, feedback: str, analysis: str) -> List[Dict]:
        """Extract insights from feedback."""
        insights = []

        # Look for recommendation sections
        recommendations = re.findall(
            r'#+\s*Recommendation[s]?[:\s]+(.+?)(?=\n#+|\Z)',
            feedback,
            re.DOTALL | re.IGNORECASE
        )

        for rec in recommendations:
            # Split into individual recommendations
            lines = [line.strip() for line in rec.split('\n') if line.strip()]
            for line in lines:
                if line.startswith(('-', '*', '•', '1.', '2.', '3.')):
                    insight_text = re.sub(r'^[-*•\d.)\s]+', '', line).strip()
                    if len(insight_text) > 20:  # Meaningful insights only
                        insights.append({
                            "category": self._categorize_insight(insight_text),
                            "name": insight_text[:100],
                            "description": insight_text,
                            "confidence": 0.75
                        })

        return insights

    def _extract_code_transformations(self, feedback: str) -> List[Dict]:
        """Extract code transformation examples."""
        transformations = []

        # Find transformation sections
        transform_sections = re.findall(
            r'#+\s*(?:Transform|Migration|Convert)[:\s]+(.+?)\n(.+?)(?=\n#+|\Z)',
            feedback,
            re.DOTALL | re.IGNORECASE
        )

        for title, content in transform_sections:
            code_blocks = re.findall(r'```(\w+)?\n(.+?)```', content, re.DOTALL)

            if len(code_blocks) >= 2:
                lang1, before = code_blocks[0]
                lang2, after = code_blocks[1]

                transformations.append({
                    "pattern_id": f"transform_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "before_code": before.strip(),
                    "after_code": after.strip(),
                    "language": lang2 or lang1 or "php",
                    "framework": "Laravel" if "laravel" in content.lower() else "PHP",
                    "category": self._categorize_transformation(title, content),
                    "success_rate": 0.8
                })

        return transformations

    def _extract_migration_strategies(self, feedback: str) -> List[Dict]:
        """Extract migration strategies from feedback."""
        strategies = []

        # Look for strategy sections
        strategy_sections = re.findall(
            r'#+\s*(?:Strategy|Approach|Plan)[:\s]+(.+?)\n(.+?)(?=\n#+|\Z)',
            feedback,
            re.DOTALL | re.IGNORECASE
        )

        for title, content in strategy_sections:
            strategies.append({
                "feature_name": title.strip(),
                "strategy_type": self._categorize_strategy(content),
                "description": content.strip()[:500],
                "success_rate": 0.7,
                "difficulty": self._estimate_difficulty(content),
                "estimated_hours": self._estimate_hours(content),
                "dependencies": self._extract_dependencies(content)
            })

        return strategies

    def _store_patterns(self, patterns: List[Dict]):
        """Store learned patterns."""
        if not patterns:
            return

        # Store in JSON file
        data = self._load_patterns()

        for pattern in patterns:
            # Check if pattern already exists
            existing = next(
                (p for p in data["patterns"] if p["name"] == pattern["name"]),
                None
            )

            if existing:
                # Update confidence if pattern seen again
                existing["confidence"] = min(1.0, existing["confidence"] + 0.05)
                existing["success_count"] += 1
            else:
                data["patterns"].append(pattern)

        self._save_patterns(data)

        # Also store in database for insights query
        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        for pattern in patterns:
            # Check if already exists in database
            cursor.execute(
                "SELECT id FROM insights WHERE name = ?",
                (pattern["name"],)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                cursor.execute('''
                    UPDATE insights
                    SET confidence = MIN(1.0, confidence + 0.05),
                        success_count = success_count + 1,
                        last_used = ?
                    WHERE name = ?
                ''', (datetime.now().isoformat(), pattern["name"]))
            else:
                # Insert new pattern as insight
                cursor.execute('''
                    INSERT INTO insights (
                        pattern_id, category, name, description,
                        legacy_pattern, modern_equivalent, confidence,
                        success_count, created_at, last_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    pattern.get("id", f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    pattern.get("category", "migration_patterns"),
                    pattern["name"],
                    pattern.get("description", ""),
                    pattern.get("legacy_pattern", ""),
                    pattern.get("modern_equivalent", ""),
                    pattern.get("confidence", 0.8),
                    pattern.get("success_count", 0),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

        conn.commit()
        conn.close()

    def _store_insights(self, insights: List[Dict]):
        """Store insights in database."""
        if not insights:
            return

        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        for insight in insights:
            cursor.execute('''
                INSERT INTO insights (
                    pattern_id, category, name, description,
                    confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                f"insight_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                insight["category"],
                insight["name"],
                insight["description"],
                insight["confidence"],
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def _store_transformations(self, transformations: List[Dict]):
        """Store code transformations."""
        if not transformations:
            return

        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        for trans in transformations:
            cursor.execute('''
                INSERT INTO code_transformations (
                    pattern_id, before_code, after_code, language,
                    framework, category, success_rate, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trans["pattern_id"],
                trans["before_code"],
                trans["after_code"],
                trans["language"],
                trans["framework"],
                trans["category"],
                trans["success_rate"],
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def _store_strategies(self, strategies: List[Dict]):
        """Store migration strategies."""
        if not strategies:
            return

        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        for strategy in strategies:
            cursor.execute('''
                INSERT INTO migration_strategies (
                    feature_name, strategy_type, description,
                    success_rate, difficulty, estimated_hours,
                    dependencies, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                strategy["feature_name"],
                strategy["strategy_type"],
                strategy["description"],
                strategy["success_rate"],
                strategy["difficulty"],
                strategy.get("estimated_hours", 0),
                strategy.get("dependencies", ""),
                datetime.now().isoformat()
            ))

        conn.commit()
        conn.close()

    def _record_feedback_session(self, analysis_file: str, feedback_file: str,
                                 patterns_count: int, insights_count: int):
        """Record a feedback learning session."""
        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO feedback (
                analysis_file, feedback_file, patterns_learned,
                insights_gained, created_at, summary
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            analysis_file,
            feedback_file,
            patterns_count,
            insights_count,
            datetime.now().isoformat(),
            f"Learned {patterns_count} patterns and {insights_count} insights"
        ))

        conn.commit()
        conn.close()

    def get_insights(self, insight_type: str = "all", search: str = None) -> List[Dict]:
        """Retrieve learned insights.

        Args:
            insight_type: Type of insights to retrieve
            search: Search term to filter insights

        Returns:
            List of insights
        """
        conn = sqlite3.connect(self.insights_db)
        cursor = conn.cursor()

        if insight_type == "all":
            query = "SELECT * FROM insights"
            params = []
        else:
            query = "SELECT * FROM insights WHERE category = ?"
            params = [insight_type]

        if search:
            if params:
                query += " AND (name LIKE ? OR description LIKE ?)"
            else:
                query += " WHERE (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY confidence DESC, success_count DESC"

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

    def get_patterns(self, category: str = None) -> List[Dict]:
        """Get learned patterns.

        Args:
            category: Optional category filter

        Returns:
            List of patterns
        """
        data = self._load_patterns()
        patterns = data.get("patterns", [])

        if category:
            patterns = [p for p in patterns if p.get("category") == category]

        # Sort by confidence and success count
        patterns.sort(key=lambda x: (x.get("confidence", 0), x.get("success_count", 0)), reverse=True)

        return patterns

    def get_similar_patterns(self, code_snippet: str, limit: int = 5) -> List[Dict]:
        """Find patterns similar to the given code snippet.

        Args:
            code_snippet: Code to find similar patterns for
            limit: Maximum number of patterns to return

        Returns:
            List of similar patterns
        """
        patterns = self.get_patterns()

        # Simple similarity scoring based on keyword matching
        scored_patterns = []
        keywords = set(re.findall(r'\b\w+\b', code_snippet.lower()))

        for pattern in patterns:
            legacy = pattern.get("legacy_pattern", "").lower()
            score = len(keywords & set(re.findall(r'\b\w+\b', legacy)))

            if score > 0:
                scored_patterns.append((score, pattern))

        # Sort by score and return top matches
        scored_patterns.sort(reverse=True)
        return [pattern for _, pattern in scored_patterns[:limit]]

    # Helper methods for categorization

    def _categorize_pattern(self, name: str, content: str) -> str:
        """Categorize a pattern based on its content."""
        name_lower = name.lower()
        content_lower = content.lower()

        if any(kw in name_lower or kw in content_lower
               for kw in ['ajax', 'api', 'endpoint', 'request']):
            return "frontend_backend_flow"
        elif any(kw in name_lower or kw in content_lower
                 for kw in ['security', 'sql injection', 'xss', 'csrf']):
            return "security_improvements"
        elif any(kw in name_lower or kw in content_lower
                 for kw in ['database', 'query', 'eloquent', 'model']):
            return "database_patterns"
        elif any(kw in name_lower or kw in content_lower
                 for kw in ['architecture', 'service', 'repository', 'pattern']):
            return "architecture_patterns"
        elif any(kw in name_lower or kw in content_lower
                 for kw in ['new feature', 'fresh', 'implement']):
            return "fresh_development"
        else:
            return "api_integration"

    def _categorize_insight(self, text: str) -> str:
        """Categorize an insight."""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ['migrate', 'convert', 'transform']):
            return "migration_patterns"
        elif any(kw in text_lower for kw in ['security', 'vulnerable', 'protect']):
            return "security"
        elif any(kw in text_lower for kw in ['performance', 'optimize', 'cache']):
            return "performance"
        elif any(kw in text_lower for kw in ['test', 'testing', 'coverage']):
            return "testing"
        else:
            return "general"

    def _categorize_transformation(self, title: str, content: str) -> str:
        """Categorize a code transformation."""
        combined = (title + " " + content).lower()

        if 'controller' in combined:
            return "controller"
        elif 'model' in combined or 'eloquent' in combined:
            return "model"
        elif 'vue' in combined or 'component' in combined:
            return "frontend"
        elif 'api' in combined or 'route' in combined:
            return "api"
        else:
            return "general"

    def _categorize_strategy(self, content: str) -> str:
        """Categorize a migration strategy."""
        content_lower = content.lower()

        if 'incremental' in content_lower or 'step by step' in content_lower:
            return "incremental"
        elif 'big bang' in content_lower or 'complete rewrite' in content_lower:
            return "big_bang"
        elif 'parallel' in content_lower or 'side by side' in content_lower:
            return "parallel"
        else:
            return "custom"

    def _estimate_difficulty(self, content: str) -> str:
        """Estimate difficulty from content."""
        content_lower = content.lower()

        if any(kw in content_lower for kw in ['complex', 'difficult', 'challenging']):
            return "high"
        elif any(kw in content_lower for kw in ['simple', 'easy', 'straightforward']):
            return "low"
        else:
            return "medium"

    def _estimate_hours(self, content: str) -> float:
        """Extract hour estimate from content."""
        # Look for hour mentions
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hr)', content, re.IGNORECASE)
        if hour_match:
            return float(hour_match.group(1))

        # Estimate based on difficulty keywords
        if 'complex' in content.lower():
            return 16.0
        elif 'moderate' in content.lower():
            return 8.0
        else:
            return 4.0

    def _extract_dependencies(self, content: str) -> str:
        """Extract dependencies from content."""
        dependencies = []

        # Look for "depends on", "requires", etc.
        dep_matches = re.findall(
            r'(?:depends on|requires|needs)\s+([^\n,]+)',
            content,
            re.IGNORECASE
        )

        for match in dep_matches:
            dependencies.append(match.strip())

        return ", ".join(dependencies[:5]) if dependencies else ""

    def _infer_pattern_name(self, before_code: str, after_code: str) -> str:
        """Infer a pattern name from before/after code."""
        # Simple heuristic based on code content
        if '$_POST' in before_code and 'Request' in after_code:
            return "Form handling: PHP POST → Laravel Request"
        elif '$.ajax' in before_code and 'axios' in after_code:
            return "AJAX: jQuery → Axios"
        elif 'mysql_' in before_code and 'DB::' in after_code:
            return "Database: mysql functions → Laravel DB"
        elif 'include' in before_code and 'use' in after_code:
            return "Dependencies: include → namespace/use"
        else:
            return "Code transformation"

    def _generate_learning_summary(self, patterns, insights, transformations, strategies) -> str:
        """Generate a summary of what was learned."""
        parts = []

        if patterns:
            parts.append(f"{len(patterns)} migration patterns")
        if insights:
            parts.append(f"{len(insights)} insights")
        if transformations:
            parts.append(f"{len(transformations)} code transformations")
        if strategies:
            parts.append(f"{len(strategies)} migration strategies")

        if not parts:
            return "No new learnings extracted"

        return "Learned: " + ", ".join(parts)

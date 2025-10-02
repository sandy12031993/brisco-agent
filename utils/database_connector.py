"""
Database connector utility for direct MySQL database analysis.
Uses SQLAlchemy to inspect live database schemas.
"""

from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Connect to MySQL database and extract schema information."""

    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = 'root', password: str = '', database: str = ''):
        """Initialize database connection.

        Args:
            host: Database host (default: localhost)
            port: Database port (default: 3306)
            user: Database user (default: root)
            password: Database password
            database: Database name to analyze
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.engine = None
        self.inspector = None
        self.metadata = None

    def connect(self) -> bool:
        """Establish connection to database.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create connection string
            connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

            # Create engine
            self.engine = create_engine(connection_string, echo=False)

            # Test connection
            with self.engine.connect() as conn:
                pass

            # Create inspector
            self.inspector = inspect(self.engine)

            # Create metadata
            self.metadata = MetaData()
            self.metadata.reflect(bind=self.engine)

            logger.info(f"Connected to database: {self.database} at {self.host}")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def get_all_tables(self) -> List[str]:
        """Get list of all table names in the database.

        Returns:
            List of table names
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        return self.inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get detailed schema information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table schema details
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        try:
            # Get columns
            columns = []
            for column in self.inspector.get_columns(table_name):
                columns.append({
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'default': column.get('default'),
                    'autoincrement': column.get('autoincrement', False),
                    'comment': column.get('comment', '')
                })

            # Get primary key
            primary_key = self.inspector.get_pk_constraint(table_name)

            # Get indexes
            indexes = []
            for index in self.inspector.get_indexes(table_name):
                indexes.append({
                    'name': index['name'],
                    'columns': index['column_names'],
                    'unique': index['unique']
                })

            # Get foreign keys
            foreign_keys = []
            for fk in self.inspector.get_foreign_keys(table_name):
                foreign_keys.append({
                    'name': fk['name'],
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns'],
                    'on_delete': fk.get('ondelete'),
                    'on_update': fk.get('onupdate')
                })

            # Get table comment
            table_comment = None
            try:
                table_info = self.inspector.get_table_comment(table_name)
                table_comment = table_info.get('text') if table_info else None
            except:
                pass

            return {
                'table_name': table_name,
                'columns': columns,
                'column_count': len(columns),
                'primary_key': primary_key,
                'indexes': indexes,
                'foreign_keys': foreign_keys,
                'table_comment': table_comment
            }

        except SQLAlchemyError as e:
            logger.error(f"Error getting schema for table {table_name}: {e}")
            return {
                'table_name': table_name,
                'error': str(e)
            }

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all tables in the database.

        Returns:
            Dictionary mapping table names to their schemas
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        tables = self.get_all_tables()
        schemas = {}

        for table_name in tables:
            schemas[table_name] = self.get_table_schema(table_name)

        return schemas

    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the entire database.

        Returns:
            Dictionary with database summary
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        tables = self.get_all_tables()
        total_columns = 0
        total_indexes = 0
        total_foreign_keys = 0
        tables_with_pk = 0

        for table_name in tables:
            schema = self.get_table_schema(table_name)
            if 'error' not in schema:
                total_columns += schema['column_count']
                total_indexes += len(schema['indexes'])
                total_foreign_keys += len(schema['foreign_keys'])
                if schema['primary_key'] and schema['primary_key'].get('constrained_columns'):
                    tables_with_pk += 1

        return {
            'database_name': self.database,
            'total_tables': len(tables),
            'total_columns': total_columns,
            'total_indexes': total_indexes,
            'total_foreign_keys': total_foreign_keys,
            'tables_with_primary_key': tables_with_pk,
            'tables_without_primary_key': len(tables) - tables_with_pk,
            'table_list': tables
        }

    def get_table_relationships(self) -> List[Dict[str, Any]]:
        """Get all foreign key relationships in the database.

        Returns:
            List of relationships
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        relationships = []
        tables = self.get_all_tables()

        for table_name in tables:
            schema = self.get_table_schema(table_name)
            if 'error' not in schema:
                for fk in schema['foreign_keys']:
                    relationships.append({
                        'from_table': table_name,
                        'from_columns': fk['constrained_columns'],
                        'to_table': fk['referred_table'],
                        'to_columns': fk['referred_columns'],
                        'constraint_name': fk['name'],
                        'on_delete': fk['on_delete'],
                        'on_update': fk['on_update']
                    })

        return relationships

    def search_tables(self, pattern: str) -> List[str]:
        """Search for tables matching a pattern.

        Args:
            pattern: Search pattern (case-insensitive)

        Returns:
            List of matching table names
        """
        if not self.inspector:
            raise RuntimeError("Not connected to database. Call connect() first.")

        tables = self.get_all_tables()
        pattern_lower = pattern.lower()
        return [t for t in tables if pattern_lower in t.lower()]

    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info(f"Closed connection to database: {self.database}")

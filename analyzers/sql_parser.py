"""
SQL and database schema parser for database analysis.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

@dataclass
class TableSchema:
    name: str
    columns: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    engine: Optional[str]
    charset: Optional[str]

@dataclass
class DatabaseRelationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    constraint_name: str
    on_delete: str
    on_update: str

class SQLParser:
    """Parser for SQL files and database schema analysis."""

    def __init__(self):
        self.tables = {}
        self.relationships = []
        self.views = {}
        self.procedures = {}
        self.triggers = {}

    def parse_sql_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a SQL file and extract schema information."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_sql_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_sql_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse SQL content and extract all relevant information."""
        # Clean and normalize SQL
        content = self._clean_sql_content(content)

        # Reset state for new file
        self.tables = {}
        self.relationships = []
        self.views = {}
        self.procedures = {}
        self.triggers = {}

        # Parse different SQL elements
        self._parse_create_table_statements(content)
        self._parse_alter_table_statements(content)
        self._parse_foreign_keys(content)
        self._parse_indexes(content)
        self._parse_views(content)
        self._parse_procedures(content)
        self._parse_triggers(content)

        # Analyze schema patterns
        patterns = self._analyze_schema_patterns()

        return {
            'file_path': file_path,
            'parsed': True,
            'tables': {name: self._table_to_dict(table) for name, table in self.tables.items()},
            'relationships': [self._relationship_to_dict(rel) for rel in self.relationships],
            'views': self.views,
            'procedures': self.procedures,
            'triggers': self.triggers,
            'patterns': patterns,
            'metrics': self._calculate_schema_metrics()
        }

    def _clean_sql_content(self, content: str) -> str:
        """Clean and normalize SQL content."""
        # Remove comments
        content = re.sub(r'--.*?\n', '\n', content)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)

        return content

    def _parse_create_table_statements(self, content: str):
        """Parse CREATE TABLE statements."""
        # Pattern for CREATE TABLE
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?\s*\((.*?)\)(?:\s*ENGINE\s*=\s*(\w+))?(?:\s*CHARSET\s*=\s*(\w+))?'

        for match in re.finditer(table_pattern, content, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1)
            columns_def = match.group(2)
            engine = match.group(3)
            charset = match.group(4)

            # Parse columns and constraints
            columns, indexes, foreign_keys, constraints = self._parse_table_definition(columns_def)

            table = TableSchema(
                name=table_name,
                columns=columns,
                indexes=indexes,
                foreign_keys=foreign_keys,
                constraints=constraints,
                engine=engine,
                charset=charset
            )

            self.tables[table_name] = table

    def _parse_table_definition(self, definition: str) -> tuple:
        """Parse table definition for columns, indexes, and constraints."""
        columns = []
        indexes = []
        foreign_keys = []
        constraints = []

        # Split by commas, but be careful with nested parentheses
        parts = self._split_table_definition(definition)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if part.upper().startswith('PRIMARY KEY'):
                # Primary key constraint
                pk_match = re.search(r'PRIMARY\s+KEY\s*\((.*?)\)', part, re.IGNORECASE)
                if pk_match:
                    pk_columns = [col.strip().strip('`') for col in pk_match.group(1).split(',')]
                    indexes.append({
                        'name': 'PRIMARY',
                        'type': 'PRIMARY',
                        'columns': pk_columns,
                        'unique': True
                    })

            elif part.upper().startswith('UNIQUE'):
                # Unique constraint
                unique_match = re.search(r'UNIQUE\s+(?:KEY\s+)?(?:`?(\w+)`?\s*)?\((.*?)\)', part, re.IGNORECASE)
                if unique_match:
                    index_name = unique_match.group(1) or 'unique_key'
                    unique_columns = [col.strip().strip('`') for col in unique_match.group(2).split(',')]
                    indexes.append({
                        'name': index_name,
                        'type': 'UNIQUE',
                        'columns': unique_columns,
                        'unique': True
                    })

            elif part.upper().startswith('KEY') or part.upper().startswith('INDEX'):
                # Regular index
                key_match = re.search(r'(?:KEY|INDEX)\s+`?(\w+)`?\s*\((.*?)\)', part, re.IGNORECASE)
                if key_match:
                    index_name = key_match.group(1)
                    index_columns = [col.strip().strip('`') for col in key_match.group(2).split(',')]
                    indexes.append({
                        'name': index_name,
                        'type': 'INDEX',
                        'columns': index_columns,
                        'unique': False
                    })

            elif part.upper().startswith('FOREIGN KEY'):
                # Foreign key constraint
                fk_match = re.search(
                    r'FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+`?(\w+)`?\s*\(([^)]+)\)(?:\s+ON\s+DELETE\s+(\w+))?(?:\s+ON\s+UPDATE\s+(\w+))?',
                    part, re.IGNORECASE
                )
                if fk_match:
                    from_columns = [col.strip().strip('`') for col in fk_match.group(1).split(',')]
                    ref_table = fk_match.group(2)
                    ref_columns = [col.strip().strip('`') for col in fk_match.group(3).split(',')]
                    on_delete = fk_match.group(4) or 'RESTRICT'
                    on_update = fk_match.group(5) or 'RESTRICT'

                    for i, from_col in enumerate(from_columns):
                        ref_col = ref_columns[i] if i < len(ref_columns) else ref_columns[0]
                        foreign_keys.append({
                            'from_column': from_col,
                            'reference_table': ref_table,
                            'reference_column': ref_col,
                            'on_delete': on_delete,
                            'on_update': on_update
                        })

            elif part.upper().startswith('CONSTRAINT'):
                # Named constraint
                constraints.append({
                    'definition': part,
                    'type': 'CONSTRAINT'
                })

            else:
                # Regular column definition
                column = self._parse_column_definition(part)
                if column:
                    columns.append(column)

        return columns, indexes, foreign_keys, constraints

    def _split_table_definition(self, definition: str) -> List[str]:
        """Split table definition by commas, respecting parentheses."""
        parts = []
        current_part = ""
        paren_count = 0

        for char in definition:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                parts.append(current_part.strip())
                current_part = ""
                continue

            current_part += char

        if current_part.strip():
            parts.append(current_part.strip())

        return parts

    def _parse_column_definition(self, definition: str) -> Optional[Dict[str, Any]]:
        """Parse a single column definition."""
        # Basic pattern for column definition
        col_pattern = r'`?(\w+)`?\s+(\w+)(?:\(([^)]+)\))?(?:\s+(UNSIGNED))?(?:\s+(NOT\s+NULL|NULL))?(?:\s+DEFAULT\s+([^,\s]+))?(?:\s+(AUTO_INCREMENT))?(?:\s+(PRIMARY\s+KEY))?'

        match = re.search(col_pattern, definition, re.IGNORECASE)
        if not match:
            return None

        column_name = match.group(1)
        data_type = match.group(2).upper()
        type_params = match.group(3)
        unsigned = bool(match.group(4))
        nullable = match.group(5)
        default_value = match.group(6)
        auto_increment = bool(match.group(7))
        primary_key = bool(match.group(8))

        # Parse type parameters
        length = None
        precision = None
        scale = None

        if type_params:
            if ',' in type_params:
                # Decimal/Float with precision and scale
                parts = type_params.split(',')
                precision = int(parts[0].strip())
                scale = int(parts[1].strip()) if len(parts) > 1 else None
            else:
                # Length parameter
                try:
                    length = int(type_params.strip())
                except ValueError:
                    length = type_params.strip()

        # Determine nullability
        is_nullable = True
        if nullable:
            is_nullable = 'NULL' in nullable.upper() and 'NOT NULL' not in nullable.upper()
        if primary_key:
            is_nullable = False

        return {
            'name': column_name,
            'type': data_type,
            'length': length,
            'precision': precision,
            'scale': scale,
            'unsigned': unsigned,
            'nullable': is_nullable,
            'default': default_value,
            'auto_increment': auto_increment,
            'primary_key': primary_key
        }

    def _parse_alter_table_statements(self, content: str):
        """Parse ALTER TABLE statements."""
        alter_pattern = r'ALTER\s+TABLE\s+`?(\w+)`?\s+(.*?)(?=ALTER\s+TABLE|CREATE\s+|INSERT\s+|$)'

        for match in re.finditer(alter_pattern, content, re.IGNORECASE | re.DOTALL):
            table_name = match.group(1)
            alter_commands = match.group(2)

            if table_name in self.tables:
                self._process_alter_commands(table_name, alter_commands)

    def _process_alter_commands(self, table_name: str, commands: str):
        """Process ALTER TABLE commands."""
        # Add column
        add_col_pattern = r'ADD\s+(?:COLUMN\s+)?`?(\w+)`?\s+(.+?)(?=,|\s*$)'
        for match in re.finditer(add_col_pattern, commands, re.IGNORECASE):
            column_name = match.group(1)
            column_def = match.group(2)
            column = self._parse_column_definition(f"{column_name} {column_def}")
            if column:
                self.tables[table_name].columns.append(column)

        # Add foreign key
        add_fk_pattern = r'ADD\s+FOREIGN\s+KEY\s*\(([^)]+)\)\s+REFERENCES\s+`?(\w+)`?\s*\(([^)]+)\)'
        for match in re.finditer(add_fk_pattern, commands, re.IGNORECASE):
            from_columns = [col.strip().strip('`') for col in match.group(1).split(',')]
            ref_table = match.group(2)
            ref_columns = [col.strip().strip('`') for col in match.group(3).split(',')]

            for i, from_col in enumerate(from_columns):
                ref_col = ref_columns[i] if i < len(ref_columns) else ref_columns[0]
                self.tables[table_name].foreign_keys.append({
                    'from_column': from_col,
                    'reference_table': ref_table,
                    'reference_column': ref_col,
                    'on_delete': 'RESTRICT',
                    'on_update': 'RESTRICT'
                })

    def _parse_foreign_keys(self, content: str):
        """Parse standalone foreign key definitions."""
        # This would handle foreign keys defined outside of CREATE TABLE
        pass

    def _parse_indexes(self, content: str):
        """Parse standalone index definitions."""
        index_pattern = r'CREATE\s+(?:(UNIQUE)\s+)?INDEX\s+`?(\w+)`?\s+ON\s+`?(\w+)`?\s*\(([^)]+)\)'

        for match in re.finditer(index_pattern, content, re.IGNORECASE):
            is_unique = bool(match.group(1))
            index_name = match.group(2)
            table_name = match.group(3)
            index_columns = [col.strip().strip('`') for col in match.group(4).split(',')]

            if table_name in self.tables:
                self.tables[table_name].indexes.append({
                    'name': index_name,
                    'type': 'UNIQUE' if is_unique else 'INDEX',
                    'columns': index_columns,
                    'unique': is_unique
                })

    def _parse_views(self, content: str):
        """Parse CREATE VIEW statements."""
        view_pattern = r'CREATE\s+VIEW\s+`?(\w+)`?\s+AS\s+(.*?)(?=CREATE\s+|INSERT\s+|$)'

        for match in re.finditer(view_pattern, content, re.IGNORECASE | re.DOTALL):
            view_name = match.group(1)
            view_definition = match.group(2).strip()

            self.views[view_name] = {
                'name': view_name,
                'definition': view_definition,
                'dependencies': self._extract_view_dependencies(view_definition)
            }

    def _extract_view_dependencies(self, definition: str) -> List[str]:
        """Extract table dependencies from view definition."""
        # Simple pattern to find table names in FROM and JOIN clauses
        table_pattern = r'(?:FROM|JOIN)\s+`?(\w+)`?'
        dependencies = []

        for match in re.finditer(table_pattern, definition, re.IGNORECASE):
            table_name = match.group(1)
            if table_name not in dependencies:
                dependencies.append(table_name)

        return dependencies

    def _parse_procedures(self, content: str):
        """Parse stored procedures."""
        proc_pattern = r'CREATE\s+PROCEDURE\s+`?(\w+)`?\s*\((.*?)\)\s+(.*?)(?=CREATE\s+PROCEDURE|CREATE\s+FUNCTION|$)'

        for match in re.finditer(proc_pattern, content, re.IGNORECASE | re.DOTALL):
            proc_name = match.group(1)
            parameters = match.group(2)
            body = match.group(3)

            self.procedures[proc_name] = {
                'name': proc_name,
                'parameters': parameters.strip(),
                'body': body.strip()
            }

    def _parse_triggers(self, content: str):
        """Parse triggers."""
        trigger_pattern = r'CREATE\s+TRIGGER\s+`?(\w+)`?\s+(BEFORE|AFTER)\s+(INSERT|UPDATE|DELETE)\s+ON\s+`?(\w+)`?\s+FOR\s+EACH\s+ROW\s+(.*?)(?=CREATE\s+TRIGGER|CREATE\s+PROCEDURE|$)'

        for match in re.finditer(trigger_pattern, content, re.IGNORECASE | re.DOTALL):
            trigger_name = match.group(1)
            timing = match.group(2)
            event = match.group(3)
            table_name = match.group(4)
            body = match.group(5)

            self.triggers[trigger_name] = {
                'name': trigger_name,
                'timing': timing,
                'event': event,
                'table': table_name,
                'body': body.strip()
            }

    def _analyze_schema_patterns(self) -> Dict[str, Any]:
        """Analyze database schema patterns."""
        patterns = {
            'naming_conventions': self._analyze_naming_conventions(),
            'normalization': self._analyze_normalization(),
            'indexing_patterns': self._analyze_indexing_patterns(),
            'relationship_patterns': self._analyze_relationship_patterns(),
            'data_types': self._analyze_data_type_usage(),
            'constraints': self._analyze_constraint_usage()
        }

        return patterns

    def _analyze_naming_conventions(self) -> Dict[str, Any]:
        """Analyze naming convention patterns."""
        conventions = {
            'table_naming': 'mixed',
            'column_naming': 'mixed',
            'consistent_casing': True,
            'use_prefixes': False,
            'use_underscores': True
        }

        table_names = list(self.tables.keys())
        if table_names:
            # Check for consistent casing
            all_lower = all(name.islower() for name in table_names)
            all_upper = all(name.isupper() for name in table_names)
            conventions['consistent_casing'] = all_lower or all_upper

            if all_lower:
                conventions['table_naming'] = 'lowercase'
            elif all_upper:
                conventions['table_naming'] = 'uppercase'

            # Check for underscore usage
            conventions['use_underscores'] = any('_' in name for name in table_names)

        return conventions

    def _analyze_normalization(self) -> Dict[str, Any]:
        """Analyze database normalization level."""
        normalization = {
            'estimated_level': '3NF',
            'potential_violations': [],
            'recommendations': []
        }

        # Basic analysis - could be more sophisticated
        for table_name, table in self.tables.items():
            # Check for potential 1NF violations (repeating groups)
            for column in table.columns:
                if 'json' in column['type'].lower() or 'text' in column['type'].lower():
                    normalization['potential_violations'].append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'Potential repeating group in text/json field'
                    })

        return normalization

    def _analyze_indexing_patterns(self) -> Dict[str, Any]:
        """Analyze indexing patterns."""
        indexing = {
            'total_indexes': 0,
            'unique_indexes': 0,
            'composite_indexes': 0,
            'missing_indexes': [],
            'over_indexed_tables': []
        }

        for table_name, table in self.tables.items():
            table_indexes = len(table.indexes)
            indexing['total_indexes'] += table_indexes

            for index in table.indexes:
                if index['unique']:
                    indexing['unique_indexes'] += 1
                if len(index['columns']) > 1:
                    indexing['composite_indexes'] += 1

            # Check for potential missing indexes on foreign keys
            for fk in table.foreign_keys:
                fk_column = fk['from_column']
                has_index = any(fk_column in idx['columns'] for idx in table.indexes)
                if not has_index:
                    indexing['missing_indexes'].append({
                        'table': table_name,
                        'column': fk_column,
                        'reason': 'Foreign key without index'
                    })

            # Check for over-indexing
            if table_indexes > len(table.columns) * 0.5:
                indexing['over_indexed_tables'].append(table_name)

        return indexing

    def _analyze_relationship_patterns(self) -> Dict[str, Any]:
        """Analyze relationship patterns."""
        relationships = {
            'total_foreign_keys': 0,
            'cascade_patterns': {},
            'circular_references': [],
            'orphaned_tables': []
        }

        all_fks = []
        referenced_tables = set()

        for table_name, table in self.tables.items():
            for fk in table.foreign_keys:
                all_fks.append({
                    'from_table': table_name,
                    'from_column': fk['from_column'],
                    'to_table': fk['reference_table'],
                    'to_column': fk['reference_column'],
                    'on_delete': fk['on_delete'],
                    'on_update': fk['on_update']
                })
                referenced_tables.add(fk['reference_table'])

        relationships['total_foreign_keys'] = len(all_fks)

        # Analyze cascade patterns
        cascade_counts = {}
        for fk in all_fks:
            on_delete = fk['on_delete']
            cascade_counts[on_delete] = cascade_counts.get(on_delete, 0) + 1

        relationships['cascade_patterns'] = cascade_counts

        # Find orphaned tables (tables with no relationships)
        all_table_names = set(self.tables.keys())
        tables_with_fks = set(fk['from_table'] for fk in all_fks)
        relationships['orphaned_tables'] = list(all_table_names - tables_with_fks - referenced_tables)

        return relationships

    def _analyze_data_type_usage(self) -> Dict[str, Any]:
        """Analyze data type usage patterns."""
        type_usage = {}
        total_columns = 0

        for table in self.tables.values():
            for column in table.columns:
                data_type = column['type']
                type_usage[data_type] = type_usage.get(data_type, 0) + 1
                total_columns += 1

        # Convert to percentages
        type_percentages = {
            dtype: (count / total_columns) * 100
            for dtype, count in type_usage.items()
        }

        return {
            'type_counts': type_usage,
            'type_percentages': type_percentages,
            'most_common_types': sorted(type_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        }

    def _analyze_constraint_usage(self) -> Dict[str, Any]:
        """Analyze constraint usage patterns."""
        constraints = {
            'primary_keys': 0,
            'foreign_keys': 0,
            'unique_constraints': 0,
            'check_constraints': 0,
            'tables_without_pk': []
        }

        for table_name, table in self.tables.items():
            has_pk = False

            for index in table.indexes:
                if index['type'] == 'PRIMARY':
                    constraints['primary_keys'] += 1
                    has_pk = True
                elif index['type'] == 'UNIQUE':
                    constraints['unique_constraints'] += 1

            if not has_pk:
                constraints['tables_without_pk'].append(table_name)

            constraints['foreign_keys'] += len(table.foreign_keys)

        return constraints

    def _calculate_schema_metrics(self) -> Dict[str, Any]:
        """Calculate schema metrics."""
        total_tables = len(self.tables)
        total_columns = sum(len(table.columns) for table in self.tables.values())
        total_indexes = sum(len(table.indexes) for table in self.tables.values())
        total_fks = sum(len(table.foreign_keys) for table in self.tables.values())

        return {
            'total_tables': total_tables,
            'total_columns': total_columns,
            'total_indexes': total_indexes,
            'total_foreign_keys': total_fks,
            'total_views': len(self.views),
            'total_procedures': len(self.procedures),
            'total_triggers': len(self.triggers),
            'avg_columns_per_table': total_columns / total_tables if total_tables > 0 else 0,
            'avg_indexes_per_table': total_indexes / total_tables if total_tables > 0 else 0,
            'referential_integrity_score': (total_fks / total_tables) if total_tables > 0 else 0
        }

    def parse_laravel_migration(self, file_path: str) -> Dict[str, Any]:
        """Parse a Laravel migration file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_laravel_migration_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_laravel_migration_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Laravel migration content."""
        migration_info = {
            'file_path': file_path,
            'parsed': True,
            'type': 'laravel_migration',
            'operations': [],
            'tables_affected': [],
            'migration_type': 'unknown'
        }

        # Extract migration class name
        class_match = re.search(r'class\s+(\w+)\s+extends', content)
        if class_match:
            migration_info['class_name'] = class_match.group(1)

        # Parse up() method
        up_match = re.search(r'public\s+function\s+up\(\)\s*\{(.*?)\}', content, re.DOTALL)
        if up_match:
            up_content = up_match.group(1)
            migration_info['operations'].extend(self._parse_migration_operations(up_content))

        # Parse down() method
        down_match = re.search(r'public\s+function\s+down\(\)\s*\{(.*?)\}', content, re.DOTALL)
        if down_match:
            down_content = down_match.group(1)
            migration_info['rollback_operations'] = self._parse_migration_operations(down_content)

        # Determine migration type
        if any('create' in op.get('operation', '').lower() for op in migration_info['operations']):
            migration_info['migration_type'] = 'create_table'
        elif any('drop' in op.get('operation', '').lower() for op in migration_info['operations']):
            migration_info['migration_type'] = 'drop_table'
        else:
            migration_info['migration_type'] = 'alter_table'

        return migration_info

    def _parse_migration_operations(self, content: str) -> List[Dict[str, Any]]:
        """Parse Laravel migration operations."""
        operations = []

        # Schema::create
        create_matches = re.findall(r'Schema::create\([\'"](\w+)[\'"]', content)
        for table_name in create_matches:
            operations.append({
                'operation': 'create_table',
                'table': table_name
            })

        # Schema::table (alter)
        alter_matches = re.findall(r'Schema::table\([\'"](\w+)[\'"]', content)
        for table_name in alter_matches:
            operations.append({
                'operation': 'alter_table',
                'table': table_name
            })

        # Schema::drop
        drop_matches = re.findall(r'Schema::drop\([\'"](\w+)[\'"]', content)
        for table_name in drop_matches:
            operations.append({
                'operation': 'drop_table',
                'table': table_name
            })

        return operations

    def _table_to_dict(self, table: TableSchema) -> Dict[str, Any]:
        """Convert TableSchema to dictionary."""
        return {
            'name': table.name,
            'columns': table.columns,
            'indexes': table.indexes,
            'foreign_keys': table.foreign_keys,
            'constraints': table.constraints,
            'engine': table.engine,
            'charset': table.charset
        }

    def _relationship_to_dict(self, relationship: DatabaseRelationship) -> Dict[str, Any]:
        """Convert DatabaseRelationship to dictionary."""
        return {
            'from_table': relationship.from_table,
            'from_column': relationship.from_column,
            'to_table': relationship.to_table,
            'to_column': relationship.to_column,
            'constraint_name': relationship.constraint_name,
            'on_delete': relationship.on_delete,
            'on_update': relationship.on_update
        }
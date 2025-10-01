#!/usr/bin/env python3
"""
Flow Diagram Generator.

Generates flow diagrams from relationship graphs in various formats:
- Mermaid (for GitHub/docs)
- ASCII (for terminal)
- JSON (for external tools)
"""

import json
from typing import Dict, List, Any, Set
from pathlib import Path


class FlowDiagramGenerator:
    """Generates flow diagrams from relationship graphs."""

    def __init__(self):
        """Initialize the diagram generator."""
        self.node_shapes = {
            "php_legacy": "rectangle",
            "laravel_controller": "rounded",
            "laravel_model": "cylinder",
            "vue_component": "diamond",
            "javascript": "hexagon",
            "database": "database"
        }

        self.relationship_styles = {
            "include": "dotted",
            "ajax_get": "solid",
            "ajax_post": "solid",
            "form_post": "thick",
            "route": "solid",
            "api_get": "solid",
            "api_post": "solid",
            "uses_model": "dotted",
            "renders_view": "dashed"
        }

    def generate_mermaid(self, graph: Dict, title: str = "File Relationships") -> str:
        """Generate Mermaid diagram from relationship graph.

        Args:
            graph: Relationship graph dictionary
            title: Diagram title

        Returns:
            Mermaid markdown string
        """
        lines = ["```mermaid", "graph TD"]

        # Add title
        if title:
            lines.append(f"    title[{title}]")
            lines.append("")

        # Generate node IDs
        node_ids = self._generate_node_ids(graph['nodes'])

        # Add nodes
        for node_path, node_info in graph['nodes'].items():
            node_id = node_ids[node_path]
            node_label = self._format_node_label(node_path)
            node_type = node_info.get('type', 'unknown')

            # Choose shape based on type
            if node_type == 'database':
                lines.append(f"    {node_id}[({node_label})]")
            elif node_type == 'vue_component':
                lines.append(f"    {node_id}{{{node_label}}}")
            elif node_type == 'laravel_model':
                lines.append(f"    {node_id}[({node_label})]")
            elif node_type == 'javascript':
                lines.append(f"    {node_id}{{{{{node_label}}}}}")
            else:
                lines.append(f"    {node_id}[{node_label}]")

            # Add styling based on type
            lines.append(self._get_mermaid_style(node_id, node_type))

        lines.append("")

        # Add edges
        for edge in graph['edges']:
            source_id = node_ids.get(edge['source_file'])
            target_id = node_ids.get(edge['target_file'])

            if not (source_id and target_id):
                continue

            rel_type = edge['relationship_type']
            label = self._format_edge_label(rel_type, edge.get('context', ''))

            # Choose arrow style
            if 'ajax' in rel_type or 'api' in rel_type:
                arrow = "==>"
            elif rel_type.startswith('form'):
                arrow = "==>>"
            elif rel_type in ['include', 'uses_model']:
                arrow = "-.->",
            else:
                arrow = "-->"

            if label:
                lines.append(f"    {source_id} {arrow}|{label}| {target_id}")
            else:
                lines.append(f"    {source_id} {arrow} {target_id}")

        # Add database tables as separate nodes
        if graph.get('database_tables'):
            lines.append("")
            lines.append("    %% Database Tables")
            for i, table in enumerate(graph['database_tables']):
                table_id = f"DB{i}"
                lines.append(f"    {table_id}[(Database: {table})]")
                lines.append(f"    style {table_id} fill:#f9f,stroke:#333")

        lines.append("```")
        return "\n".join(lines)

    def generate_ascii(self, graph: Dict, title: str = "File Relationships") -> str:
        """Generate ASCII diagram from relationship graph.

        Args:
            graph: Relationship graph dictionary
            title: Diagram title

        Returns:
            ASCII diagram string
        """
        lines = []

        # Add title
        if title:
            lines.append("╔" + "═" * (len(title) + 2) + "╗")
            lines.append(f"║ {title} ║")
            lines.append("╚" + "═" * (len(title) + 2) + "╝")
            lines.append("")

        # Build tree structure from entry points
        entry_points = graph.get('entry_points', [])
        if not entry_points and graph['nodes']:
            entry_points = [list(graph['nodes'].keys())[0]]

        for entry in entry_points:
            tree_lines = self._build_ascii_tree(entry, graph, set())
            lines.extend(tree_lines)
            lines.append("")

        # Add database tables
        if graph.get('database_tables'):
            lines.append("Database Tables:")
            for table in graph['database_tables']:
                lines.append(f"  └─ {table}")
            lines.append("")

        return "\n".join(lines)

    def generate_json(self, graph: Dict) -> str:
        """Generate JSON representation of the graph.

        Args:
            graph: Relationship graph dictionary

        Returns:
            JSON string
        """
        return json.dumps(graph, indent=2)

    def generate_dependency_tree(self, graph: Dict, root_file: str) -> str:
        """Generate a dependency tree view (ASCII).

        Args:
            graph: Relationship graph dictionary
            root_file: Root file to start from

        Returns:
            ASCII tree string
        """
        lines = []
        lines.append(f"Dependency Tree: {Path(root_file).name}")
        lines.append("")

        visited = set()
        tree_lines = self._build_dependency_tree_recursive(root_file, graph, visited, 0)
        lines.extend(tree_lines)

        # Add summary
        lines.append("")
        lines.append("Summary:")
        lines.append(f"  └─ Total files: {len(graph['nodes'])}")
        lines.append(f"  └─ Dependencies: {len(graph['edges'])}")
        lines.append(f"  └─ Database tables: {len(graph.get('database_tables', []))}")

        return "\n".join(lines)

    def generate_feature_flow(self, graph: Dict, feature_name: str) -> str:
        """Generate a feature flow diagram showing user → frontend → backend → database.

        Args:
            graph: Relationship graph dictionary
            feature_name: Name of the feature

        Returns:
            ASCII flow diagram
        """
        lines = []
        lines.append(f"Feature Flow: {feature_name}")
        lines.append("=" * (len(feature_name) + 14))
        lines.append("")

        # Categorize files by layer
        layers = {
            'Frontend': [],
            'Backend': [],
            'Database': []
        }

        for node_path, node_info in graph['nodes'].items():
            node_type = node_info.get('type', '')

            if node_type in ['vue_component', 'javascript']:
                layers['Frontend'].append(node_path)
            elif node_type in ['php_legacy', 'laravel_controller']:
                layers['Backend'].append(node_path)
            elif node_type in ['laravel_model', 'database']:
                layers['Database'].append(node_path)

        # Draw flow
        lines.append("User Request")
        lines.append("    ↓")

        if layers['Frontend']:
            lines.append("┌─────────────────────────────┐")
            lines.append("│ Frontend Layer              │")
            lines.append("├─────────────────────────────┤")
            for file in layers['Frontend']:
                lines.append(f"│ • {Path(file).name:<26} │")
            lines.append("└─────────────────────────────┘")
            lines.append("    ↓")

        if layers['Backend']:
            lines.append("┌─────────────────────────────┐")
            lines.append("│ Backend Layer               │")
            lines.append("├─────────────────────────────┤")
            for file in layers['Backend']:
                lines.append(f"│ • {Path(file).name:<26} │")
            lines.append("└─────────────────────────────┘")
            lines.append("    ↓")

        if layers['Database'] or graph.get('database_tables'):
            lines.append("┌─────────────────────────────┐")
            lines.append("│ Database Layer              │")
            lines.append("├─────────────────────────────┤")
            for file in layers['Database']:
                lines.append(f"│ • {Path(file).name:<26} │")
            for table in list(graph.get('database_tables', []))[:5]:
                lines.append(f"│ • Table: {table:<19} │")
            lines.append("└─────────────────────────────┘")

        return "\n".join(lines)

    # Helper methods

    def _generate_node_ids(self, nodes: Dict) -> Dict[str, str]:
        """Generate short IDs for nodes."""
        node_ids = {}
        for i, node_path in enumerate(nodes.keys()):
            # Create readable ID from filename
            filename = Path(node_path).stem
            # Remove special chars
            clean_name = ''.join(c for c in filename if c.isalnum())
            node_id = f"{clean_name}{i}" if clean_name else f"N{i}"
            node_ids[node_path] = node_id
        return node_ids

    def _format_node_label(self, node_path: str) -> str:
        """Format node label for display."""
        # Show just the filename
        return Path(node_path).name

    def _format_edge_label(self, rel_type: str, context: str = "") -> str:
        """Format edge label for display."""
        labels = {
            "include": "includes",
            "ajax_get": "GET",
            "ajax_post": "POST",
            "ajax_put": "PUT",
            "ajax_delete": "DELETE",
            "form_post": "POST",
            "form_get": "GET",
            "api_get": "API GET",
            "api_post": "API POST",
            "api_put": "API PUT",
            "api_delete": "API DELETE",
            "uses_model": "uses",
            "renders_view": "renders",
            "route": "route",
            "script": "script"
        }

        label = labels.get(rel_type, rel_type)

        if context and context != label:
            label = f"{label}:{context}"

        return label

    def _get_mermaid_style(self, node_id: str, node_type: str) -> str:
        """Get Mermaid styling for node type."""
        styles = {
            "php_legacy": f"style {node_id} fill:#fdd,stroke:#333",
            "laravel_controller": f"style {node_id} fill:#dfd,stroke:#333",
            "laravel_model": f"style {node_id} fill:#ddf,stroke:#333",
            "vue_component": f"style {node_id} fill:#ffd,stroke:#333",
            "javascript": f"style {node_id} fill:#fdf,stroke:#333",
            "database": f"style {node_id} fill:#dff,stroke:#333"
        }
        return styles.get(node_type, f"style {node_id} fill:#eee,stroke:#333")

    def _build_ascii_tree(self, node_path: str, graph: Dict, visited: Set[str],
                         level: int = 0, prefix: str = "") -> List[str]:
        """Build ASCII tree recursively."""
        lines = []

        if node_path in visited:
            return lines

        visited.add(node_path)

        # Node label
        node_name = Path(node_path).name
        node_type = graph['nodes'].get(node_path, {}).get('type', '')

        # Add node
        if level == 0:
            lines.append(node_name)
        else:
            lines.append(f"{prefix}└─ {node_name}")

        # Find children
        children = [edge for edge in graph['edges'] if edge['source_file'] == node_path]

        for i, edge in enumerate(children):
            target = edge['target_file']
            rel_type = self._format_edge_label(edge['relationship_type'])

            is_last = i == len(children) - 1
            new_prefix = prefix + ("   " if level > 0 else "")

            # Add relationship line
            if level == 0:
                lines.append(f"├─ {rel_type}")
            else:
                lines.append(f"{new_prefix}   ├─ {rel_type}")

            # Recursively add children
            child_lines = self._build_ascii_tree(
                target, graph, visited, level + 1,
                new_prefix + ("   " if is_last else "│  ")
            )
            lines.extend(child_lines)

        return lines

    def _build_dependency_tree_recursive(self, node_path: str, graph: Dict,
                                        visited: Set[str], level: int) -> List[str]:
        """Build dependency tree recursively."""
        lines = []

        if node_path in visited or level > 10:  # Prevent infinite recursion
            return lines

        visited.add(node_path)

        indent = "  " * level
        node_name = Path(node_path).name
        node_info = graph['nodes'].get(node_path, {})

        # Group edges by type
        edges_by_type = {}
        for edge in graph['edges']:
            if edge['source_file'] == node_path:
                rel_type = edge['relationship_type']
                if rel_type not in edges_by_type:
                    edges_by_type[rel_type] = []
                edges_by_type[rel_type].append(edge['target_file'])

        # Display grouped dependencies
        for rel_type, targets in edges_by_type.items():
            lines.append(f"{indent}├─ {rel_type.replace('_', ' ').title()}")
            for target in targets:
                target_name = Path(target).name
                lines.append(f"{indent}│  └─ {target_name}")

                # Recurse for some relationship types
                if rel_type in ['include', 'uses_model', 'renders_view']:
                    child_lines = self._build_dependency_tree_recursive(
                        target, graph, visited, level + 1
                    )
                    lines.extend(child_lines)

        return lines

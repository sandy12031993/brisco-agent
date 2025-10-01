#!/usr/bin/env python3
"""
Intelligent File Relationship Mapper.

This module analyzes file relationships to understand complete feature flows:
- PHP files and their includes/AJAX endpoints
- Laravel routes and their controller/view relationships
- Vue components and their API calls
- Database table relationships
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class FileRelationship:
    """Represents a relationship between files."""
    source_file: str
    target_file: str
    relationship_type: str  # include, ajax, route, api_call, render, etc.
    line_number: Optional[int] = None
    context: str = ""
    confidence: float = 1.0


@dataclass
class RelationshipGraph:
    """Graph of file relationships."""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[FileRelationship] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    database_tables: Set[str] = field(default_factory=set)


class RelationshipMapper:
    """Maps relationships between files in a codebase."""

    def __init__(self, project_root: str):
        """Initialize the relationship mapper.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.legacy_root = self.project_root / "core"
        self.laravel_root = self.project_root / "laravel"

    def analyze_php_legacy(self, file_path: str, depth: int = 3) -> RelationshipGraph:
        """Analyze a legacy PHP file and its relationships.

        Args:
            file_path: Path to the PHP file
            depth: How deep to follow relationships

        Returns:
            RelationshipGraph with all related files
        """
        graph = RelationshipGraph()
        visited = set()

        self._analyze_php_file_recursive(file_path, graph, visited, depth)

        return graph

    def _analyze_php_file_recursive(self, file_path: str, graph: RelationshipGraph,
                                    visited: Set[str], depth: int):
        """Recursively analyze PHP file relationships."""
        if depth <= 0 or file_path in visited:
            return

        visited.add(file_path)

        # Add node
        graph.nodes[file_path] = {
            "type": "php_legacy",
            "language": "php",
            "analyzed": True
        }

        if file_path not in graph.entry_points:
            graph.entry_points.append(file_path)

        # Read file content
        try:
            full_path = self._resolve_path(file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            graph.nodes[file_path]["error"] = str(e)
            return

        # Find includes/requires
        includes = self._find_php_includes(content, file_path)
        for include_file, line_num in includes:
            graph.edges.append(FileRelationship(
                source_file=file_path,
                target_file=include_file,
                relationship_type="include",
                line_number=line_num
            ))
            self._analyze_php_file_recursive(include_file, graph, visited, depth - 1)

        # Find AJAX endpoints
        ajax_calls = self._find_ajax_calls(content, file_path)
        for endpoint, line_num, method in ajax_calls:
            graph.edges.append(FileRelationship(
                source_file=file_path,
                target_file=endpoint,
                relationship_type=f"ajax_{method.lower()}",
                line_number=line_num,
                context=method
            ))
            self._analyze_php_file_recursive(endpoint, graph, visited, depth - 1)

        # Find JavaScript files
        js_files = self._find_linked_js(content, file_path)
        for js_file, line_num in js_files:
            graph.edges.append(FileRelationship(
                source_file=file_path,
                target_file=js_file,
                relationship_type="script",
                line_number=line_num
            ))
            # Analyze JS file for more AJAX calls
            self._analyze_js_file(js_file, graph, visited, depth - 1)

        # Find database tables
        tables = self._find_database_tables(content)
        graph.database_tables.update(tables)

        # Find form submissions
        form_targets = self._find_form_submissions(content)
        for target, line_num, method in form_targets:
            graph.edges.append(FileRelationship(
                source_file=file_path,
                target_file=target,
                relationship_type=f"form_{method.lower()}",
                line_number=line_num,
                context=method
            ))

    def _analyze_js_file(self, file_path: str, graph: RelationshipGraph,
                        visited: Set[str], depth: int):
        """Analyze a JavaScript file for AJAX calls."""
        if depth <= 0 or file_path in visited:
            return

        visited.add(file_path)

        graph.nodes[file_path] = {
            "type": "javascript",
            "language": "javascript"
        }

        try:
            full_path = self._resolve_path(file_path)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return

        # Find AJAX/fetch calls
        ajax_calls = self._find_ajax_calls(content, file_path)
        for endpoint, line_num, method in ajax_calls:
            graph.edges.append(FileRelationship(
                source_file=file_path,
                target_file=endpoint,
                relationship_type=f"ajax_{method.lower()}",
                line_number=line_num,
                context=method
            ))

    def analyze_laravel_route(self, route_path: str, depth: int = 3) -> RelationshipGraph:
        """Analyze a Laravel route and its complete stack.

        Args:
            route_path: Route path (e.g., 'warehouse/cycle-count')
            depth: How deep to follow relationships

        Returns:
            RelationshipGraph with all related files
        """
        graph = RelationshipGraph()
        visited = set()

        # Find route definition
        route_info = self._find_route_definition(route_path)

        if not route_info:
            return graph

        # Start analysis from controller
        controller_file = route_info["controller_file"]
        method = route_info["method"]

        self._analyze_laravel_controller(controller_file, method, graph, visited, depth)

        return graph

    def _analyze_laravel_controller(self, controller_file: str, method: str,
                                    graph: RelationshipGraph, visited: Set[str], depth: int):
        """Analyze Laravel controller and its relationships."""
        if depth <= 0 or controller_file in visited:
            return

        visited.add(controller_file)

        graph.nodes[controller_file] = {
            "type": "laravel_controller",
            "language": "php",
            "method": method
        }

        if controller_file not in graph.entry_points:
            graph.entry_points.append(controller_file)

        try:
            full_path = self._resolve_path(controller_file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            graph.nodes[controller_file]["error"] = str(e)
            return

        # Find the specific method
        method_content = self._extract_method_content(content, method)

        if method_content:
            # Find models used
            models = self._find_models_used(method_content)
            for model in models:
                model_file = f"app/Models/{model}.php"
                graph.edges.append(FileRelationship(
                    source_file=controller_file,
                    target_file=model_file,
                    relationship_type="uses_model",
                    context=model
                ))
                graph.nodes[model_file] = {
                    "type": "laravel_model",
                    "language": "php"
                }

            # Find services used
            services = self._find_services_used(method_content)
            for service in services:
                service_file = f"app/Services/{service}.php"
                graph.edges.append(FileRelationship(
                    source_file=controller_file,
                    target_file=service_file,
                    relationship_type="uses_service",
                    context=service
                ))

            # Find views rendered
            views = self._find_views_rendered(method_content)
            for view in views:
                view_file = self._view_to_file(view)
                graph.edges.append(FileRelationship(
                    source_file=controller_file,
                    target_file=view_file,
                    relationship_type="renders_view",
                    context=view
                ))
                # Analyze Vue component
                self._analyze_vue_component(view_file, graph, visited, depth - 1)

            # Find database tables
            tables = self._find_database_tables(method_content)
            graph.database_tables.update(tables)

    def _analyze_vue_component(self, component_file: str, graph: RelationshipGraph,
                               visited: Set[str], depth: int):
        """Analyze Vue component and its API calls."""
        if depth <= 0 or component_file in visited:
            return

        visited.add(component_file)

        graph.nodes[component_file] = {
            "type": "vue_component",
            "language": "javascript"
        }

        try:
            full_path = self._resolve_path(component_file)
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return

        # Find API calls
        api_calls = self._find_api_calls(content)
        for endpoint, line_num, method in api_calls:
            graph.edges.append(FileRelationship(
                source_file=component_file,
                target_file=endpoint,
                relationship_type=f"api_{method.lower()}",
                line_number=line_num,
                context=method
            ))

            # Follow API endpoint back to controller
            route_info = self._find_route_definition(endpoint)
            if route_info:
                controller_file = route_info["controller_file"]
                controller_method = route_info["method"]
                graph.edges.append(FileRelationship(
                    source_file=endpoint,
                    target_file=controller_file,
                    relationship_type="route_to_controller",
                    context=controller_method
                ))

    # Detection methods

    def _find_php_includes(self, content: str, current_file: str) -> List[Tuple[str, int]]:
        """Find include/require statements in PHP."""
        includes = []
        patterns = [
            r'(?:include|require)(?:_once)?\s*[(\s]+[\'"](.+?)[\'"]',
            r'(?:include|require)(?:_once)?\s+[\'"](.+?)[\'"]'
        ]

        for i, line in enumerate(content.split('\n'), 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    include_path = match.group(1)
                    # Resolve relative path
                    resolved = self._resolve_include_path(include_path, current_file)
                    if resolved:
                        includes.append((resolved, i))

        return includes

    def _find_ajax_calls(self, content: str, current_file: str) -> List[Tuple[str, int, str]]:
        """Find AJAX calls (jQuery, axios, fetch)."""
        ajax_calls = []

        patterns = [
            # jQuery AJAX
            (r'\$\.ajax\s*\(\s*\{[^}]*url\s*:\s*[\'"]([^\'"\s]+)[\'"]', 'POST'),
            (r'\$\.post\s*\([\'"]([^\'"\s]+)[\'"]', 'POST'),
            (r'\$\.get\s*\([\'"]([^\'"\s]+)[\'"]', 'GET'),
            # Fetch API
            (r'fetch\s*\([\'"]([^\'"\s]+)[\'"]', 'GET'),
            # Axios
            (r'axios\.get\s*\([\'"]([^\'"\s]+)[\'"]', 'GET'),
            (r'axios\.post\s*\([\'"]([^\'"\s]+)[\'"]', 'POST'),
            (r'axios\.put\s*\([\'"]([^\'"\s]+)[\'"]', 'PUT'),
            (r'axios\.delete\s*\([\'"]([^\'"\s]+)[\'"]', 'DELETE'),
            (r'axios\s*\(\s*\{[^}]*url\s*:\s*[\'"]([^\'"\s]+)[\'"]', 'POST'),
        ]

        for i, line in enumerate(content.split('\n'), 1):
            for pattern, method in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    url = match.group(1)
                    # Resolve relative URLs
                    if not url.startswith('http'):
                        url = self._resolve_url_path(url, current_file)
                    ajax_calls.append((url, i, method))

        return ajax_calls

    def _find_linked_js(self, content: str, current_file: str) -> List[Tuple[str, int]]:
        """Find linked JavaScript files."""
        js_files = []

        pattern = r'<script[^>]*src=[\'"]([^\'"\s]+\.js)[\'"]'

        for i, line in enumerate(content.split('\n'), 1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                js_path = match.group(1)
                resolved = self._resolve_include_path(js_path, current_file)
                if resolved:
                    js_files.append((resolved, i))

        return js_files

    def _find_form_submissions(self, content: str) -> List[Tuple[str, int, str]]:
        """Find HTML form submission targets."""
        forms = []

        pattern = r'<form[^>]*action=[\'"]([^\'"\s]+)[\'"][^>]*method=[\'"]([^\'"\s]+)[\'"]'

        for i, line in enumerate(content.split('\n'), 1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                action = match.group(1)
                method = match.group(2).upper()
                forms.append((action, i, method))

        return forms

    def _find_database_tables(self, content: str) -> Set[str]:
        """Find database table references."""
        tables = set()

        patterns = [
            # Direct queries
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            # Laravel DB facade
            r'DB::table\s*\([\'"]([^\'"\s]+)[\'"]',
            # Eloquent (try to infer table from model name)
            r'([A-Z][a-zA-Z]*)::'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                table = match.group(1)
                # Filter out common keywords
                if table.lower() not in ['select', 'where', 'and', 'or', 'on']:
                    tables.add(table)

        return tables

    def _find_route_definition(self, route_path: str) -> Optional[Dict]:
        """Find route definition in Laravel route files."""
        route_files = [
            self.laravel_root / "routes" / "web.php",
            self.laravel_root / "routes" / "api.php"
        ]

        for route_file in route_files:
            if not route_file.exists():
                continue

            with open(route_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for route definition
            patterns = [
                rf'Route::(?:get|post|put|patch|delete)\s*\([\'"]/?{re.escape(route_path)}[\'"],\s*\[([^\]]+)\]',
                rf'Route::(?:get|post|put|patch|delete)\s*\([\'"]/?{re.escape(route_path)}[\'"],\s*[\'"]([^\'"\s]+)@([^\'"\s]+)[\'"]'
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    if '@' in match.group(0):
                        # Old-style: 'Controller@method'
                        controller_class = match.group(1)
                        method = match.group(2)
                    else:
                        # New-style: [Controller::class, 'method']
                        array_content = match.group(1)
                        controller_match = re.search(r'([A-Z]\w+)::class', array_content)
                        method_match = re.search(r'[\'"](\w+)[\'"]', array_content)

                        if controller_match and method_match:
                            controller_class = controller_match.group(1)
                            method = method_match.group(1)
                        else:
                            continue

                    # Convert controller class to file path
                    controller_file = f"app/Http/Controllers/{controller_class}.php"

                    return {
                        "route": route_path,
                        "controller": controller_class,
                        "controller_file": controller_file,
                        "method": method,
                        "route_file": str(route_file)
                    }

        return None

    def _find_models_used(self, content: str) -> List[str]:
        """Find Eloquent models used in code."""
        models = []

        # Look for model usage patterns
        patterns = [
            r'([A-Z][a-zA-Z]+)::(?:find|where|create|update)',
            r'use\s+App\\Models\\([A-Z][a-zA-Z]+)',
            r'new\s+([A-Z][a-zA-Z]+)\s*\('
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                model = match.group(1)
                if model not in models:
                    models.append(model)

        return models

    def _find_services_used(self, content: str) -> List[str]:
        """Find services used in code."""
        services = []

        patterns = [
            r'use\s+App\\Services\\([A-Z][a-zA-Z]+)',
            r'new\s+([A-Z][a-zA-Z]+Service)\s*\(',
            r'\$this->([a-z][a-zA-Z]+Service)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                service = match.group(1)
                if service not in services:
                    services.append(service)

        return services

    def _find_views_rendered(self, content: str) -> List[str]:
        """Find views/components rendered."""
        views = []

        patterns = [
            r'view\s*\([\'"]([^\'"\s]+)[\'"]',
            r'return\s+view\s*\([\'"]([^\'"\s]+)[\'"]',
            r'@extends\s*\([\'"]([^\'"\s]+)[\'"]',
            r'Inertia::render\s*\([\'"]([^\'"\s]+)[\'"]'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                view = match.group(1)
                if view not in views:
                    views.append(view)

        return views

    def _find_api_calls(self, content: str) -> List[Tuple[str, int, str]]:
        """Find API calls in Vue/JS component."""
        api_calls = []

        patterns = [
            (r'axios\.get\s*\([\'"]([^\'"\s]+)[\'"]', 'GET'),
            (r'axios\.post\s*\([\'"]([^\'"\s]+)[\'"]', 'POST'),
            (r'axios\.put\s*\([\'"]([^\'"\s]+)[\'"]', 'PUT'),
            (r'axios\.delete\s*\([\'"]([^\'"\s]+)[\'"]', 'DELETE'),
            (r'this\.\$http\.get\s*\([\'"]([^\'"\s]+)[\'"]', 'GET'),
            (r'this\.\$http\.post\s*\([\'"]([^\'"\s]+)[\'"]', 'POST'),
            (r'fetch\s*\([\'"]([^\'"\s]+)[\'"]', 'GET')
        ]

        for i, line in enumerate(content.split('\n'), 1):
            for pattern, method in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    url = match.group(1)
                    # Clean up URL (remove leading /api if present for matching)
                    clean_url = url.lstrip('/')
                    api_calls.append((clean_url, i, method))

        return api_calls

    def _extract_method_content(self, content: str, method_name: str) -> str:
        """Extract the content of a specific method from a class."""
        # Find the method
        pattern = rf'public\s+function\s+{re.escape(method_name)}\s*\([^)]*\)\s*\{{'

        match = re.search(pattern, content)
        if not match:
            return ""

        start = match.end()

        # Find matching closing brace
        brace_count = 1
        i = start

        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1

        return content[start:i-1]

    def _view_to_file(self, view_name: str) -> str:
        """Convert Laravel view name to file path."""
        # Laravel views: 'admin.users.index' -> 'resources/views/admin/users/index.blade.php'
        # Inertia: 'Users/Index' -> 'resources/js/Pages/Users/Index.vue'

        if '/' in view_name:
            # Likely Inertia/Vue
            return f"resources/js/Pages/{view_name}.vue"
        else:
            # Blade view
            path = view_name.replace('.', '/')
            return f"resources/views/{path}.blade.php"

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path to full path."""
        # Try different roots
        candidates = [
            self.project_root / file_path,
            self.legacy_root / file_path,
            self.laravel_root / file_path
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        # Return first candidate even if doesn't exist
        return candidates[0]

    def _resolve_include_path(self, include_path: str, current_file: str) -> Optional[str]:
        """Resolve an include path relative to current file."""
        current_dir = Path(current_file).parent

        # Try as absolute from project root
        absolute = self.project_root / include_path.lstrip('./')
        if absolute.exists():
            try:
                return str(absolute.relative_to(self.project_root))
            except ValueError:
                # Path is outside project root, use absolute path
                return str(absolute)

        # Try relative to current file
        relative = current_dir / include_path
        if relative.exists():
            try:
                return str(relative.relative_to(self.project_root))
            except ValueError:
                # Path is outside project root, use absolute path
                return str(relative)

        return None

    def _resolve_url_path(self, url: str, current_file: str) -> str:
        """Resolve a URL to a file path."""
        # Remove query parameters
        url = url.split('?')[0]

        # For legacy PHP, URLs often map directly to files
        if url.endswith('.php'):
            return url.lstrip('/')

        # For API calls, keep as is
        return url.lstrip('/')

    def to_dict(self, graph: RelationshipGraph) -> Dict:
        """Convert graph to dictionary for JSON serialization."""
        return {
            "nodes": graph.nodes,
            "edges": [asdict(edge) for edge in graph.edges],
            "entry_points": graph.entry_points,
            "database_tables": list(graph.database_tables)
        }

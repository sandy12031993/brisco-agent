#!/usr/bin/env python3
"""
JavaScript Route Parser.

Parses Vue Router route files (.routes.js) and maps them to Vue components.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional


class JSRouteParser:
    """Parses JavaScript route files and maps them to Vue components."""

    def __init__(self, laravel_root: str):
        """Initialize JS route parser.

        Args:
            laravel_root: Root directory of Laravel project
        """
        self.laravel_root = Path(laravel_root)
        self.routes_dir = self.laravel_root / "resources" / "app" / "src" / "routes"

    def find_route(self, route_path: str) -> Optional[Dict]:
        """Find route definition by path.

        Args:
            route_path: Route path to search for (e.g., 'warehouse/cycle-count')

        Returns:
            Route information dict or None
        """
        # Normalize route path
        normalized_path = route_path.strip('/')

        # Search all .routes.js files recursively
        if not self.routes_dir.exists():
            return None

        for route_file in self.routes_dir.rglob("*.routes.js"):
            route_info = self._search_route_file(route_file, normalized_path)
            if route_info:
                return route_info

        return None

    def list_all_routes(self) -> List[Dict]:
        """List all routes in JavaScript route files.

        Returns:
            List of route information
        """
        all_routes = []

        if not self.routes_dir.exists():
            return all_routes

        for route_file in self.routes_dir.rglob("*.routes.js"):
            routes = self._parse_all_routes(route_file)
            all_routes.extend(routes)

        return all_routes

    def _search_route_file(self, file_path: Path, route_path: str) -> Optional[Dict]:
        """Search for a specific route in a route file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            routes = self._extract_routes_from_content(content, str(file_path))

            # Find matching route
            for route in routes:
                if route['path'].strip('/') == route_path:
                    return route

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

        return None

    def _parse_all_routes(self, file_path: Path) -> List[Dict]:
        """Parse all routes from a route file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._extract_routes_from_content(content, str(file_path))

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def _extract_routes_from_content(self, content: str, file_path: str) -> List[Dict]:
        """Extract route objects from JavaScript content.

        Parses route definitions like:
        {
          name: 'CycleCount',
          path: '/warehouse/cycle-count',
          component: () => import('@/views/pages/Warehouse/cycleCount'),
        }
        """
        routes = []

        # Split content by route objects - look for objects with path property
        # We need to handle nested braces in meta objects
        # Strategy: Find 'path: ' and capture until we find a matching closing brace

        # Find all positions where path: appears
        path_positions = [m.start() for m in re.finditer(r'path\s*:\s*[\'"]', content)]

        for pos in path_positions:
            # Find the opening brace before this path
            # Go backwards to find the nearest {
            opening_brace = content.rfind('{', 0, pos)
            if opening_brace == -1:
                continue

            # Now find the matching closing brace
            # Track brace depth to handle nested objects
            depth = 1
            i = opening_brace + 1
            closing_brace = -1

            while i < len(content) and depth > 0:
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        closing_brace = i
                        break
                i += 1

            if closing_brace == -1:
                continue

            # Extract the route object
            route_obj = content[opening_brace:closing_brace + 1]

            # Extract path
            path_match = re.search(r'path\s*:\s*[\'"]([^\'"]+)[\'"]', route_obj)
            if not path_match:
                continue

            path = path_match.group(1)

            # Extract name
            name_match = re.search(r'name\s*:\s*[\'"]([^\'"]+)[\'"]', route_obj)
            name = name_match.group(1) if name_match else None

            # Extract component import
            component_info = self._extract_component_import(route_obj)

            # Extract meta
            meta = self._extract_meta(route_obj)

            routes.append({
                'path': path.strip('/'),
                'name': name,
                'component': component_info['component'],
                'component_file': component_info['component_file'],
                'meta': meta,
                'route_file': file_path,
                'route_type': 'web'
            })

        return routes

    def _extract_component_import(self, route_obj: str) -> Dict[str, Optional[str]]:
        """Extract component import path from route definition.

        Handles:
        - component: () => import('@/views/pages/Warehouse/cycleCount')
        - component: SomeComponent
        """
        # Dynamic import pattern
        import_match = re.search(
            r'component\s*:\s*\(\)\s*=>\s*import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            route_obj
        )

        if import_match:
            import_path = import_match.group(1)
            # Convert @/ to actual path
            component_file = self._resolve_component_path(import_path)
            return {
                'component': import_path,
                'component_file': component_file
            }

        # Direct component reference
        component_match = re.search(r'component\s*:\s*(\w+)', route_obj)
        if component_match:
            component_name = component_match.group(1)
            return {
                'component': component_name,
                'component_file': None  # Would need to track imports
            }

        return {
            'component': None,
            'component_file': None
        }

    def _resolve_component_path(self, import_path: str) -> Optional[str]:
        """Resolve Vue component import path to actual file path.

        Args:
            import_path: Import path like '@/views/pages/Warehouse/cycleCount'

        Returns:
            Actual file path or None
        """
        # Remove @ alias
        if import_path.startswith('@/'):
            import_path = import_path[2:]
        elif import_path.startswith('./'):
            import_path = import_path[2:]

        # Convert to path
        component_path = Path(self.laravel_root) / "resources" / "app" / "src" / import_path

        # Try different patterns (order matters!)
        # 1. Directory with index.vue (most common pattern)
        # 2. File with .vue extension
        # 3. Directory with index.js
        # 4. File with .js extension
        for pattern in ['/index.vue', '.vue', '/index.js', '.js']:
            full_path = Path(str(component_path) + pattern)
            if full_path.exists():
                return str(full_path)

        # Return expected path even if not found (prefer index.vue pattern)
        return str(component_path) + '/index.vue'

    def _extract_meta(self, route_obj: str) -> Dict:
        """Extract meta object from route definition."""
        meta_match = re.search(r'meta\s*:\s*\{([^}]+)\}', route_obj)

        if not meta_match:
            return {}

        meta_content = meta_match.group(1)
        meta = {}

        # Extract simple key-value pairs
        # title: 'Cycle Count'
        kv_matches = re.finditer(r'(\w+)\s*:\s*[\'"]([^\'"]+)[\'"]', meta_content)
        for kv_match in kv_matches:
            key = kv_match.group(1)
            value = kv_match.group(2)
            meta[key] = value

        # Extract boolean values
        # requiresAuth: true
        bool_matches = re.finditer(r'(\w+)\s*:\s*(true|false)', meta_content)
        for bool_match in bool_matches:
            key = bool_match.group(1)
            value = bool_match.group(2) == 'true'
            meta[key] = value

        return meta

    def get_route_component_file(self, route_path: str) -> Optional[str]:
        """Get the Vue component file path for a route.

        Args:
            route_path: Route path to search for

        Returns:
            Component file path or None
        """
        route_info = self.find_route(route_path)
        if route_info:
            return route_info.get('component_file')
        return None

    def find_routes_by_component(self, component_file: str) -> List[Dict]:
        """Find all routes that use a specific component.

        Args:
            component_file: Component file path

        Returns:
            List of routes using this component
        """
        all_routes = self.list_all_routes()
        return [r for r in all_routes if r['component_file'] == component_file]

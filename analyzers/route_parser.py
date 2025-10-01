#!/usr/bin/env python3
"""
Laravel Route Parser.

Parses Laravel route files and understands route → controller → method mapping.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class RouteParser:
    """Parses Laravel routes and maps them to controllers."""

    def __init__(self, laravel_root: str):
        """Initialize route parser.

        Args:
            laravel_root: Root directory of Laravel project
        """
        self.laravel_root = Path(laravel_root)

        # Standard Laravel route files
        self.route_files = {
            "web": self.laravel_root / "routes" / "web.php",
            "api": self.laravel_root / "routes" / "api.php",
            "channels": self.laravel_root / "routes" / "channels.php",
            "console": self.laravel_root / "routes" / "console.php"
        }

        # Custom API routes directory (routes/API/*.php)
        self.api_routes_dir = self.laravel_root / "routes" / "API"

    def find_route(self, route_path: str) -> Optional[Dict]:
        """Find route definition by path.

        Args:
            route_path: Route path to search for

        Returns:
            Route information dict or None
        """
        # Search standard route files
        for route_type, file_path in self.route_files.items():
            if not file_path.exists():
                continue

            route_info = self._search_route_file(file_path, route_path, route_type)
            if route_info:
                return route_info

        # Search custom API routes directory (routes/API/*.php)
        if self.api_routes_dir.exists():
            for api_file in self.api_routes_dir.glob("*.php"):
                route_info = self._search_route_file(api_file, route_path, "api")
                if route_info:
                    return route_info

        return None

    def list_all_routes(self, route_type: str = "all") -> List[Dict]:
        """List all routes in the application.

        Args:
            route_type: Type of routes (web, api, all)

        Returns:
            List of route information
        """
        all_routes = []

        # Search standard route files
        files_to_search = self.route_files.items()
        if route_type != "all" and route_type in self.route_files:
            files_to_search = [(route_type, self.route_files[route_type])]

        for rtype, file_path in files_to_search:
            if not file_path.exists():
                continue

            routes = self._parse_all_routes(file_path, rtype)
            all_routes.extend(routes)

        # Search custom API routes directory (routes/API/*.php)
        if route_type in ["all", "api"] and self.api_routes_dir.exists():
            for api_file in self.api_routes_dir.glob("*.php"):
                routes = self._parse_all_routes(api_file, "api")
                all_routes.extend(routes)

        return all_routes

    def _search_route_file(self, file_path: Path, route_path: str, route_type: str) -> Optional[Dict]:
        """Search for a specific route in a route file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Normalize route path for matching
        normalized_path = route_path.strip('/')

        # Try different route definition patterns
        patterns = [
            # Route::get('/path', [Controller::class, 'method'])
            rf'Route::(get|post|put|patch|delete|any)\s*\(\s*[\'"]/?{re.escape(normalized_path)}[\'"],?\s*\[([^\]]+)\]',

            # Route::get('/path', 'Controller@method')
            rf'Route::(get|post|put|patch|delete|any)\s*\(\s*[\'"]/?{re.escape(normalized_path)}[\'"],?\s*[\'"]([^\'@]+)@([^\']+)[\'"]',

            # Route::resource or apiResource
            rf'Route::(resource|apiResource)\s*\(\s*[\'"]/?{re.escape(normalized_path)}[\'"],?\s*([^,\)]+)',

            # Route groups with prefix
            rf'Route::group\s*\(\s*\[[^\]]*[\'"]prefix[\'"]?\s*=>\s*[\'"]/?{re.escape(normalized_path.split("/")[0])}[\'"]',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                http_method = match.group(1)

                # Parse controller and method based on pattern type
                if http_method in ['resource', 'apiResource']:
                    controller_info = self._parse_resource_controller(match.group(2))
                elif '@' in match.group(0):
                    # Old-style Controller@method
                    controller_info = {
                        'controller': match.group(2),
                        'method': match.group(3)
                    }
                else:
                    # New-style [Controller::class, 'method']
                    controller_info = self._parse_array_controller(match.group(2))

                if controller_info:
                    return {
                        'route': normalized_path,
                        'http_method': http_method,
                        'route_type': route_type,
                        'controller': controller_info['controller'],
                        'method': controller_info['method'],
                        'controller_file': self._controller_to_file(controller_info['controller']),
                        'route_file': str(file_path),
                        'middleware': self._extract_middleware(match.group(0))
                    }

        return None

    def _parse_all_routes(self, file_path: Path, route_type: str) -> List[Dict]:
        """Parse all routes from a route file with prefix tracking."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        routes = []

        # Extract controller use statements for namespace resolution
        controller_map = self._extract_controller_namespaces(content)

        # Extract route prefixes and their nesting
        prefix_stack = self._extract_route_prefixes(content)

        # Find all route definitions
        patterns = [
            r'Route::(get|post|put|patch|delete|any)\s*\(\s*[\'"]([^\'\"]+)[\'"],?\s*(\[[^\]]+\]|[\'"][^\'\"@]+@[^\'\"]+[\'"])',
            r'Route::(resource|apiResource)\s*\(\s*[\'"]([^\'\"]+)[\'"],?\s*([^,\)]+)'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                http_method = match.group(1)
                route_path = match.group(2).strip('/')
                controller_str = match.group(3)

                # Find which prefix group this route belongs to
                route_position = match.start()
                full_prefix = self._get_prefix_at_position(content, route_position, prefix_stack)

                # Combine prefix with route path
                if full_prefix:
                    route_path = f"{full_prefix}/{route_path}".strip('/')

                # Parse controller info
                if http_method in ['resource', 'apiResource']:
                    controller_info = self._parse_resource_controller(controller_str)
                    # Resolve full controller class with namespace
                    controller_class = controller_map.get(controller_info['controller'], controller_info['controller'])
                    # Resources have multiple methods
                    for method in self._get_resource_methods(http_method):
                        routes.append({
                            'route': f"{route_path}/{method['path']}" if method['path'] else route_path,
                            'http_method': method['http_method'],
                            'route_type': route_type,
                            'controller': controller_info['controller'],
                            'method': method['method'],
                            'controller_file': self._controller_to_file(controller_class),
                            'route_file': str(file_path),
                            'is_resource': True
                        })
                else:
                    if '@' in controller_str:
                        controller_info = self._parse_old_style_controller(controller_str)
                    else:
                        controller_info = self._parse_array_controller(controller_str)

                    if controller_info:
                        # Resolve full controller class with namespace
                        controller_class = controller_map.get(controller_info['controller'], controller_info['controller'])

                        routes.append({
                            'route': route_path,
                            'http_method': http_method,
                            'route_type': route_type,
                            'controller': controller_info['controller'],
                            'method': controller_info['method'],
                            'controller_file': self._controller_to_file(controller_class),
                            'route_file': str(file_path),
                            'is_resource': False
                        })

        return routes

    def _parse_array_controller(self, array_str: str) -> Optional[Dict]:
        """Parse [Controller::class, 'method'] format."""
        # Extract controller class
        controller_match = re.search(r'([A-Z]\w+(?:Controller)?)::', array_str)
        # Extract method
        method_match = re.search(r'[\'"](\w+)[\'"]', array_str)

        if controller_match and method_match:
            return {
                'controller': controller_match.group(1),
                'method': method_match.group(1)
            }

        return None

    def _parse_old_style_controller(self, controller_str: str) -> Optional[Dict]:
        """Parse 'Controller@method' format."""
        controller_str = controller_str.strip('\'"')
        if '@' in controller_str:
            parts = controller_str.split('@')
            return {
                'controller': parts[0],
                'method': parts[1]
            }
        return None

    def _parse_resource_controller(self, controller_str: str) -> Dict:
        """Parse resource controller definition."""
        # Could be Controller::class or 'Controller'
        controller_match = re.search(r'([A-Z]\w+(?:Controller)?)', controller_str)
        if controller_match:
            return {
                'controller': controller_match.group(1),
                'method': 'index'  # Default, will be overridden
            }
        return {'controller': 'Unknown', 'method': 'index'}

    def _get_resource_methods(self, resource_type: str) -> List[Dict]:
        """Get all methods for a resource route."""
        if resource_type == 'resource':
            return [
                {'http_method': 'GET', 'path': '', 'method': 'index'},
                {'http_method': 'GET', 'path': 'create', 'method': 'create'},
                {'http_method': 'POST', 'path': '', 'method': 'store'},
                {'http_method': 'GET', 'path': '{id}', 'method': 'show'},
                {'http_method': 'GET', 'path': '{id}/edit', 'method': 'edit'},
                {'http_method': 'PUT', 'path': '{id}', 'method': 'update'},
                {'http_method': 'DELETE', 'path': '{id}', 'method': 'destroy'},
            ]
        else:  # apiResource
            return [
                {'http_method': 'GET', 'path': '', 'method': 'index'},
                {'http_method': 'POST', 'path': '', 'method': 'store'},
                {'http_method': 'GET', 'path': '{id}', 'method': 'show'},
                {'http_method': 'PUT', 'path': '{id}', 'method': 'update'},
                {'http_method': 'DELETE', 'path': '{id}', 'method': 'destroy'},
            ]

    def _extract_middleware(self, route_definition: str) -> List[str]:
        """Extract middleware from route definition."""
        middleware = []

        # Look for ->middleware()
        middleware_matches = re.finditer(r'->middleware\s*\(\s*[\'"]([^\'\"]+)[\'"]', route_definition)
        for match in middleware_matches:
            middleware.append(match.group(1))

        # Look for middleware in route array
        array_middleware = re.search(r'[\'"]middleware[\'"]?\s*=>\s*\[([^\]]+)\]', route_definition)
        if array_middleware:
            mw_list = re.findall(r'[\'"]([^\'\"]+)[\'"]', array_middleware.group(1))
            middleware.extend(mw_list)

        return middleware

    def _controller_to_file(self, controller_name: str) -> str:
        """Convert controller class name to file path."""
        # Handle namespaced controllers
        if '\\' in controller_name:
            # Full namespace: App\Http\Controllers\Admin\UserController
            parts = controller_name.split('\\')
            # Remove App\Http\Controllers prefix
            if parts[0:3] == ['App', 'Http', 'Controllers']:
                parts = parts[3:]
            path = '/'.join(parts)
            return f"app/Http/Controllers/{path}.php"
        else:
            # Simple class name
            return f"app/Http/Controllers/{controller_name}.php"

    def get_route_groups(self) -> Dict[str, List[Dict]]:
        """Get routes organized by groups/prefixes."""
        all_routes = self.list_all_routes()

        groups = {}
        for route in all_routes:
            # Group by first path segment
            parts = route['route'].split('/')
            group = parts[0] if parts else 'root'

            if group not in groups:
                groups[group] = []

            groups[group].append(route)

        return groups

    def find_controller_routes(self, controller_name: str) -> List[Dict]:
        """Find all routes that use a specific controller.

        Args:
            controller_name: Name of the controller

        Returns:
            List of routes using this controller
        """
        all_routes = self.list_all_routes()
        return [r for r in all_routes if r['controller'] == controller_name]

    def _extract_controller_namespaces(self, content: str) -> Dict[str, str]:
        """Extract controller use statements and map class names to full namespaces.

        Returns dict: {ClassName: Full\\Namespaced\\ClassName}
        Example: {CycleCountController: App\\Http\\Controllers\\Api\\Warehouse\\CycleCountController}
        """
        controller_map = {}

        # Find all use statements for controllers
        use_pattern = r'use\s+(App\\Http\\Controllers\\[^;]+);'

        for match in re.finditer(use_pattern, content):
            full_namespace = match.group(1)
            # Extract just the class name
            class_name = full_namespace.split('\\')[-1]
            controller_map[class_name] = full_namespace

        return controller_map

    def _extract_route_prefixes(self, content: str) -> List[Dict]:
        """Extract all Route::prefix() groups and their positions.

        Returns list of dicts with: prefix, start_pos, end_pos, depth
        """
        prefixes = []

        # Find all Route::prefix() calls
        prefix_pattern = r'Route::prefix\s*\(\s*[\'"]([^\'\"]+)[\'"]\s*\)\s*->\s*group\s*\('

        for match in re.finditer(prefix_pattern, content):
            prefix = match.group(1).strip('/')
            start = match.end()

            # Find the matching closing parenthesis/brace
            # The group starts with function () {
            func_start = content.find('{', start)
            if func_start == -1:
                continue

            # Track brace depth
            depth = 1
            i = func_start + 1
            end = -1

            while i < len(content) and depth > 0:
                if content[i] == '{':
                    depth += 1
                elif content[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
                i += 1

            if end != -1:
                prefixes.append({
                    'prefix': prefix,
                    'start': func_start,
                    'end': end
                })

        return prefixes

    def _get_prefix_at_position(self, content: str, position: int,
                                 prefix_data: List[Dict]) -> str:
        """Get the full prefix path for a route at a given position.

        Handles nested prefixes like:
        Route::prefix('warehouse')->group(function() {
            Route::prefix('cycle-count')->group(function() {
                Route::post('/get-data', ...)  // Full path: warehouse/cycle-count/get-data
            });
        });
        """
        # Find all prefixes that contain this position
        active_prefixes = []

        for prefix_info in prefix_data:
            if prefix_info['start'] <= position <= prefix_info['end']:
                active_prefixes.append(prefix_info)

        if not active_prefixes:
            return ""

        # Sort by start position (outermost first)
        active_prefixes.sort(key=lambda x: x['start'])

        # Build full prefix path
        prefix_parts = [p['prefix'] for p in active_prefixes]
        return '/'.join(prefix_parts)

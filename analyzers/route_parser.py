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
        self.route_files = {
            "web": self.laravel_root / "routes" / "web.php",
            "api": self.laravel_root / "routes" / "api.php",
            "channels": self.laravel_root / "routes" / "channels.php",
            "console": self.laravel_root / "routes" / "console.php"
        }

    def find_route(self, route_path: str) -> Optional[Dict]:
        """Find route definition by path.

        Args:
            route_path: Route path to search for

        Returns:
            Route information dict or None
        """
        for route_type, file_path in self.route_files.items():
            if not file_path.exists():
                continue

            route_info = self._search_route_file(file_path, route_path, route_type)
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

        files_to_search = self.route_files.items()
        if route_type != "all":
            files_to_search = [(route_type, self.route_files[route_type])]

        for rtype, file_path in files_to_search:
            if not file_path.exists():
                continue

            routes = self._parse_all_routes(file_path, rtype)
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
        """Parse all routes from a route file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        routes = []

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

                # Parse controller info
                if http_method in ['resource', 'apiResource']:
                    controller_info = self._parse_resource_controller(controller_str)
                    # Resources have multiple methods
                    for method in self._get_resource_methods(http_method):
                        routes.append({
                            'route': f"{route_path}/{method['path']}" if method['path'] else route_path,
                            'http_method': method['http_method'],
                            'route_type': route_type,
                            'controller': controller_info['controller'],
                            'method': method['method'],
                            'controller_file': self._controller_to_file(controller_info['controller']),
                            'route_file': str(file_path),
                            'is_resource': True
                        })
                else:
                    if '@' in controller_str:
                        controller_info = self._parse_old_style_controller(controller_str)
                    else:
                        controller_info = self._parse_array_controller(controller_str)

                    if controller_info:
                        routes.append({
                            'route': route_path,
                            'http_method': http_method,
                            'route_type': route_type,
                            'controller': controller_info['controller'],
                            'method': controller_info['method'],
                            'controller_file': self._controller_to_file(controller_info['controller']),
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

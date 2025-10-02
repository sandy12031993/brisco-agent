"""
Vue.js and Laravel code parser for modern application analysis.
"""

import re
import json
import ast
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

@dataclass
class VueComponent:
    name: str
    template: str
    script: str
    style: str
    props: List[str]
    data: List[str]
    methods: List[str]
    computed: List[str]
    watchers: List[str]
    imports: List[str]
    file_path: str

@dataclass
class LaravelController:
    name: str
    methods: List[Dict[str, Any]]
    middleware: List[str]
    dependencies: List[str]
    routes: List[str]
    namespace: str
    file_path: str

@dataclass
class LaravelModel:
    name: str
    table: str
    fillable: List[str]
    relationships: List[Dict[str, Any]]
    scopes: List[str]
    mutators: List[str]
    accessors: List[str]
    file_path: str

class VueParser:
    """Parser for Vue.js components and Laravel code."""

    def __init__(self):
        self.vue_components = []
        self.controllers = []
        self.models = []

    def parse_vue_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a Vue.js Single File Component."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_vue_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_vue_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Vue SFC content."""
        # Extract template, script, and style sections
        template = self._extract_vue_section(content, 'template')
        script = self._extract_vue_section(content, 'script')
        style = self._extract_vue_section(content, 'style')

        # Parse script section for Vue component data
        component_data = self._parse_vue_script(script) if script else {}

        # Analyze template for component usage
        template_analysis = self._analyze_vue_template(template) if template else {}

        # Analyze style for CSS patterns
        style_analysis = self._analyze_vue_style(style) if style else {}

        component = VueComponent(
            name=self._extract_component_name(file_path, script),
            template=template or '',
            script=script or '',
            style=style or '',
            props=component_data.get('props', []),
            data=component_data.get('data', []),
            methods=component_data.get('methods', []),
            computed=component_data.get('computed', []),
            watchers=component_data.get('watchers', []),
            imports=component_data.get('imports', []),
            file_path=file_path
        )

        return {
            'file_path': file_path,
            'parsed': True,
            'type': 'vue_component',
            'component': self._component_to_dict(component),
            'template_analysis': template_analysis,
            'style_analysis': style_analysis,
            'dependencies': self._analyze_vue_dependencies(component),
            'patterns': self._analyze_vue_patterns(component),
            'metrics': self._calculate_vue_metrics(component)
        }

    def _extract_vue_section(self, content: str, section: str) -> Optional[str]:
        """Extract a section (template, script, style) from Vue SFC."""
        pattern = rf'<{section}[^>]*>(.*?)</{section}>'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _parse_vue_script(self, script: str) -> Dict[str, Any]:
        """Parse the script section of a Vue component."""
        data = {
            'props': [],
            'data': [],
            'methods': [],
            'computed': [],
            'watchers': [],
            'imports': []
        }

        # Extract imports
        import_matches = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', script)
        data['imports'] = import_matches

        # Extract props
        props_match = re.search(r'props\s*:\s*(\[.*?\]|\{.*?\})', script, re.DOTALL)
        if props_match:
            props_content = props_match.group(1)
            if props_content.startswith('['):
                # Array format: props: ['prop1', 'prop2']
                prop_matches = re.findall(r'[\'"](\w+)[\'"]', props_content)
                data['props'] = prop_matches
            else:
                # Object format: props: { prop1: {}, prop2: {} }
                prop_matches = re.findall(r'(\w+)\s*:', props_content)
                data['props'] = prop_matches

        # Extract data properties
        data_match = re.search(r'data\s*\(\s*\)\s*\{[^}]*return\s*\{(.*?)\}', script, re.DOTALL)
        if data_match:
            data_content = data_match.group(1)
            data_props = re.findall(r'(\w+)\s*:', data_content)
            data['data'] = data_props

        # Extract methods
        methods_match = re.search(r'methods\s*:\s*\{(.*?)\}(?=\s*,|\s*\}|\s*$)', script, re.DOTALL)
        if methods_match:
            methods_content = methods_match.group(1)
            method_matches = re.findall(r'(\w+)\s*\(', methods_content)
            data['methods'] = method_matches

        # Extract computed properties
        computed_match = re.search(r'computed\s*:\s*\{(.*?)\}(?=\s*,|\s*\}|\s*$)', script, re.DOTALL)
        if computed_match:
            computed_content = computed_match.group(1)
            computed_matches = re.findall(r'(\w+)\s*\(', computed_content)
            data['computed'] = computed_matches

        # Extract watchers
        watch_match = re.search(r'watch\s*:\s*\{(.*?)\}(?=\s*,|\s*\}|\s*$)', script, re.DOTALL)
        if watch_match:
            watch_content = watch_match.group(1)
            watcher_matches = re.findall(r'[\'"]?(\w+)[\'"]?\s*:', watch_content)
            data['watchers'] = watcher_matches

        return data

    def _extract_component_name(self, file_path: str, script: str) -> str:
        """Extract component name from file path or script."""
        # Try to get name from script first
        name_match = re.search(r'name\s*:\s*[\'"]([^\'"]+)[\'"]', script or '')
        if name_match:
            return name_match.group(1)

        # Fallback to file name
        return Path(file_path).stem

    def _analyze_vue_template(self, template: str) -> Dict[str, Any]:
        """Analyze Vue template for patterns and components."""
        analysis = {
            'components_used': [],
            'directives_used': [],
            'event_handlers': [],
            'computed_usage': [],
            'conditional_rendering': 0,
            'loops': 0
        }

        # Find custom components (components with PascalCase or kebab-case)
        component_matches = re.findall(r'<(\w+(?:-\w+)*)', template)
        html_tags = {'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img', 'input', 'button', 'form', 'table', 'tr', 'td', 'th', 'ul', 'li', 'ol'}
        analysis['components_used'] = [comp for comp in component_matches if comp not in html_tags]

        # Find Vue directives
        directive_matches = re.findall(r'v-(\w+)', template)
        analysis['directives_used'] = list(set(directive_matches))

        # Find event handlers
        event_matches = re.findall(r'@(\w+)', template)
        analysis['event_handlers'] = list(set(event_matches))

        # Count conditional rendering
        analysis['conditional_rendering'] = len(re.findall(r'v-if|v-else-if|v-else|v-show', template))

        # Count loops
        analysis['loops'] = len(re.findall(r'v-for', template))

        return analysis

    def _analyze_vue_style(self, style: str) -> Dict[str, Any]:
        """Analyze Vue style section."""
        analysis = {
            'scoped': 'scoped' in style,
            'preprocessor': None,
            'css_classes': [],
            'css_variables': []
        }

        # Detect CSS preprocessor
        if 'lang="scss"' in style or 'lang="sass"' in style:
            analysis['preprocessor'] = 'sass'
        elif 'lang="less"' in style:
            analysis['preprocessor'] = 'less'
        elif 'lang="stylus"' in style:
            analysis['preprocessor'] = 'stylus'

        # Extract CSS classes
        class_matches = re.findall(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', style)
        analysis['css_classes'] = list(set(class_matches))

        # Extract CSS variables
        var_matches = re.findall(r'--([a-zA-Z_-][a-zA-Z0-9_-]*)', style)
        analysis['css_variables'] = list(set(var_matches))

        return analysis

    def parse_laravel_controller(self, file_path: str) -> Dict[str, Any]:
        """Parse a Laravel controller file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_controller_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_controller_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Laravel controller content."""
        # Extract class name and namespace
        class_match = re.search(r'class\s+(\w+Controller)', content)
        class_name = class_match.group(1) if class_match else 'UnknownController'

        namespace_match = re.search(r'namespace\s+([\\\\\\w]+)', content)
        namespace = namespace_match.group(1) if namespace_match else None

        # Extract methods
        methods = self._parse_controller_methods(content)

        # Extract middleware
        middleware = self._parse_middleware(content)

        # Extract dependencies (use statements)
        dependencies = self._parse_use_statements(content)

        # Extract route patterns (this would need route file analysis for completeness)
        routes = self._infer_routes_from_methods(methods, class_name)

        controller = LaravelController(
            name=class_name,
            methods=methods,
            middleware=middleware,
            dependencies=dependencies,
            routes=routes,
            namespace=namespace,
            file_path=file_path
        )

        return {
            'file_path': file_path,
            'parsed': True,
            'type': 'laravel_controller',
            'controller': self._controller_to_dict(controller),
            'patterns': self._analyze_controller_patterns(controller),
            'metrics': self._calculate_controller_metrics(controller)
        }

    def _parse_controller_methods(self, content: str) -> List[Dict[str, Any]]:
        """Parse controller methods."""
        methods = []

        # Pattern for method definition
        method_pattern = r'(public|private|protected)\s+function\s+(\w+)\s*\(([^)]*)\)'

        for match in re.finditer(method_pattern, content):
            visibility = match.group(1)
            method_name = match.group(2)
            parameters = match.group(3)

            # Skip constructor and common non-action methods
            if method_name in ['__construct', '__destruct']:
                continue

            # Parse parameters
            param_list = []
            if parameters.strip():
                for param in parameters.split(','):
                    param = param.strip()
                    if param:
                        # Extract parameter name
                        param_match = re.search(r'\$(\w+)', param)
                        if param_match:
                            param_list.append(param_match.group(1))

            methods.append({
                'name': method_name,
                'visibility': visibility,
                'parameters': param_list,
                'line': content[:match.start()].count('\n') + 1,
                'is_action': self._is_controller_action(method_name, visibility)
            })

        return methods

    def _is_controller_action(self, method_name: str, visibility: str) -> bool:
        """Determine if a method is a controller action."""
        if visibility != 'public':
            return False

        # Common action patterns
        action_patterns = ['index', 'show', 'create', 'store', 'edit', 'update', 'destroy']
        return any(pattern in method_name.lower() for pattern in action_patterns)

    def _parse_middleware(self, content: str) -> List[str]:
        """Parse middleware declarations."""
        middleware = []

        # Look for middleware in constructor
        constructor_match = re.search(r'__construct.*?\{(.*?)\}', content, re.DOTALL)
        if constructor_match:
            constructor_content = constructor_match.group(1)
            middleware_matches = re.findall(r'middleware\([\'"]([^\'"]+)[\'"]', constructor_content)
            middleware.extend(middleware_matches)

        # Look for route middleware
        route_middleware_matches = re.findall(r'Route::.*?middleware\([\'"]([^\'"]+)[\'"]', content)
        middleware.extend(route_middleware_matches)

        return list(set(middleware))

    def _parse_use_statements(self, content: str) -> List[str]:
        """Parse use statements for dependencies."""
        use_matches = re.findall(r'use\s+([\\\\\\w]+)', content)
        return use_matches

    def _infer_routes_from_methods(self, methods: List[Dict[str, Any]], controller_name: str) -> List[str]:
        """Infer likely routes from controller methods."""
        routes = []
        resource_name = controller_name.replace('Controller', '').lower()

        for method in methods:
            if method['is_action']:
                method_name = method['name']
                if method_name == 'index':
                    routes.append(f"GET /{resource_name}")
                elif method_name == 'show':
                    routes.append(f"GET /{resource_name}/{{id}}")
                elif method_name == 'create':
                    routes.append(f"GET /{resource_name}/create")
                elif method_name == 'store':
                    routes.append(f"POST /{resource_name}")
                elif method_name == 'edit':
                    routes.append(f"GET /{resource_name}/{{id}}/edit")
                elif method_name == 'update':
                    routes.append(f"PUT /{resource_name}/{{id}}")
                elif method_name == 'destroy':
                    routes.append(f"DELETE /{resource_name}/{{id}}")

        return routes

    def parse_laravel_model(self, file_path: str) -> Dict[str, Any]:
        """Parse a Laravel Eloquent model file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_model_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_model_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse Laravel model content."""
        # Extract class name
        class_match = re.search(r'class\s+(\w+)\s+extends', content)
        class_name = class_match.group(1) if class_match else 'UnknownModel'

        # Extract table name
        table = self._extract_table_name(content, class_name)

        # Extract fillable fields
        fillable = self._extract_array_property(content, 'fillable')

        # Extract relationships
        relationships = self._parse_model_relationships(content)

        # Extract scopes
        scopes = self._parse_model_scopes(content)

        # Extract mutators and accessors
        mutators = self._parse_mutators(content)
        accessors = self._parse_accessors(content)

        model = LaravelModel(
            name=class_name,
            table=table,
            fillable=fillable,
            relationships=relationships,
            scopes=scopes,
            mutators=mutators,
            accessors=accessors,
            file_path=file_path
        )

        return {
            'file_path': file_path,
            'parsed': True,
            'type': 'laravel_model',
            'model': self._model_to_dict(model),
            'patterns': self._analyze_model_patterns(model),
            'metrics': self._calculate_model_metrics(model)
        }

    def _extract_table_name(self, content: str, class_name: str) -> str:
        """Extract table name from model."""
        # Look for explicit table declaration
        table_match = re.search(r'protected\s+\$table\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if table_match:
            return table_match.group(1)

        # Default Laravel convention: pluralized snake_case
        import re
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
        return f"{snake_case}s"  # Simple pluralization

    def _extract_array_property(self, content: str, property_name: str) -> List[str]:
        """Extract array property values."""
        pattern = rf'protected\s+\${property_name}\s*=\s*\[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)

        if match:
            array_content = match.group(1)
            items = re.findall(r'[\'"]([^\'"]+)[\'"]', array_content)
            return items

        return []

    def _parse_model_relationships(self, content: str) -> List[Dict[str, Any]]:
        """Parse Eloquent relationships."""
        relationships = []

        # Common relationship methods
        relationship_types = ['hasOne', 'hasMany', 'belongsTo', 'belongsToMany', 'morphOne', 'morphMany', 'morphTo']

        for rel_type in relationship_types:
            pattern = rf'public\s+function\s+(\w+)\s*\([^)]*\)\s*\{{[^}}]*return\s+\$this->{rel_type}\s*\([^)]*\)'
            matches = re.findall(pattern, content, re.DOTALL)

            for match in matches:
                relationships.append({
                    'name': match,
                    'type': rel_type,
                    'method': match
                })

        return relationships

    def _parse_model_scopes(self, content: str) -> List[str]:
        """Parse query scopes."""
        # Look for scope methods (scopeMethodName)
        scope_matches = re.findall(r'public\s+function\s+scope(\w+)', content)
        return scope_matches

    def _parse_mutators(self, content: str) -> List[str]:
        """Parse attribute mutators."""
        # Look for mutator methods (setAttributeNameAttribute)
        mutator_matches = re.findall(r'public\s+function\s+set(\w+)Attribute', content)
        return mutator_matches

    def _parse_accessors(self, content: str) -> List[str]:
        """Parse attribute accessors."""
        # Look for accessor methods (getAttributeNameAttribute)
        accessor_matches = re.findall(r'public\s+function\s+get(\w+)Attribute', content)
        return accessor_matches

    def _analyze_vue_dependencies(self, component: VueComponent) -> Dict[str, Any]:
        """Analyze Vue component dependencies."""
        child_components = self._extract_child_components(component.script, component.file_path)

        # Get direct API calls from component
        api_calls = self._detect_api_calls(component.script)

        # Get API calls from Vuex store actions
        store_api_calls = self._get_store_api_calls(component.script, component.file_path)
        api_calls.extend(store_api_calls)

        return {
            'vue_components': component.imports,
            'child_components': child_components,
            'external_libraries': self._detect_external_libraries(component.script),
            'api_calls': api_calls
        }

    def _extract_child_components(self, script: str, file_path: str) -> List[Dict[str, str]]:
        """Extract child Vue component imports.

        Returns:
            List of dicts with 'name' and 'path' keys
        """
        child_components = []

        # Match: import ComponentName from '@/path/to/Component'
        import_patterns = [
            r'import\s+(\w+)\s+from\s+[\'"](@/[^\'"]+)[\'"]',
            r'import\s+(\w+)\s+from\s+[\'"](\./[^\'"]+)[\'"]',
            r'import\s+(\w+)\s+from\s+[\'"](\.\./[^\'"]+)[\'"]',
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, script)
            for match in matches:
                comp_name = match.group(1)
                import_path = match.group(2)

                # Skip non-component imports
                if not self._is_vue_component_import(comp_name, import_path):
                    continue

                # Resolve path
                resolved_path = self._resolve_import_path(import_path, file_path)

                child_components.append({
                    'name': comp_name,
                    'import_path': import_path,
                    'resolved_path': resolved_path
                })

        return child_components

    def _is_vue_component_import(self, name: str, import_path: str) -> bool:
        """Determine if import is a Vue component."""
        # Component names usually start with uppercase
        if not name[0].isupper():
            return False

        # Exclude common libraries
        exclude_libs = ['Vue', 'Router', 'Vuex', 'Axios', 'Lodash', 'Moment']
        if name in exclude_libs:
            return False

        # Check if path looks like a component
        component_indicators = ['/components/', '/views/', '/pages/', '.vue']
        return any(indicator in import_path.lower() for indicator in component_indicators)

    def _resolve_import_path(self, import_path: str, current_file: str) -> Optional[str]:
        """Resolve import path to absolute file path."""
        try:
            current_dir = Path(current_file).parent

            if import_path.startswith('@/'):
                # @ alias usually points to src directory
                src_path = import_path[2:]
                # Try to find src directory
                # Assuming structure: laravel/resources/app/src/
                parts = Path(current_file).parts
                if 'src' in parts:
                    src_index = parts.index('src')
                    src_dir = Path(*parts[:src_index + 1])
                    resolved = src_dir / src_path
                else:
                    return None
            elif import_path.startswith('./'):
                # Relative to current file
                resolved = current_dir / import_path[2:]
            elif import_path.startswith('../'):
                # Parent directory
                resolved = current_dir / import_path
            else:
                return None

            # Try different patterns (order matters!)
            # 1. Directory with index.vue (most common pattern)
            # 2. File with .vue extension
            # 3. Directory with index.js
            # 4. File with .js extension
            for pattern in ['/index.vue', '.vue', '/index.js', '.js', '']:
                full_path = Path(str(resolved) + pattern)
                if full_path.exists():
                    return str(full_path)

            # Return expected path even if not found (prefer index.vue pattern)
            return str(resolved) + '/index.vue'

        except Exception:
            return None

    def _detect_external_libraries(self, script: str) -> List[str]:
        """Detect external library imports."""
        libraries = []

        # Common Vue ecosystem libraries
        library_patterns = {
            'axios': r'axios',
            'lodash': r'lodash|_',
            'moment': r'moment',
            'vue-router': r'vue-router',
            'vuex': r'vuex',
            'bootstrap': r'bootstrap'
        }

        for lib, pattern in library_patterns.items():
            if re.search(pattern, script, re.IGNORECASE):
                libraries.append(lib)

        return libraries

    def _detect_api_calls(self, script: str) -> List[Dict[str, str]]:
        """Detect API calls in Vue component.

        Handles:
        - Direct axios/fetch calls
        - Vuex store.dispatch() calls (finds store actions and extracts API calls)

        Returns:
            List of dicts with 'url', 'method', and 'type' keys
        """
        api_calls = []

        # Look for axios calls with different methods
        # axios.get('/api/endpoint')
        # axios.post('/api/endpoint', data)
        axios_patterns = [
            (r'axios\.(get|post|put|patch|delete|head|options)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', 'axios'),
            (r'axios\s*\(\s*\{\s*url\s*:\s*[\'"`]([^\'"` ]+)[\'"`].*?method\s*:\s*[\'"`](\w+)[\'"`]', 'axios_config'),
            (r'axios\s*\(\s*\{\s*method\s*:\s*[\'"`](\w+)[\'"`].*?url\s*:\s*[\'"`]([^\'"` ]+)[\'"`]', 'axios_config_reverse'),
        ]

        for pattern, ptype in axios_patterns:
            matches = re.finditer(pattern, script, re.DOTALL)
            for match in matches:
                if ptype == 'axios':
                    method = match.group(1).upper()
                    url = match.group(2)
                elif ptype == 'axios_config':
                    method = match.group(2).upper()
                    url = match.group(1)
                elif ptype == 'axios_config_reverse':
                    method = match.group(1).upper()
                    url = match.group(2)

                api_calls.append({
                    'url': url,
                    'method': method,
                    'type': 'axios'
                })

        # Look for fetch calls
        # fetch('/api/endpoint', { method: 'POST' })
        fetch_patterns = [
            (r'fetch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]\s*,\s*\{[^}]*method\s*:\s*[\'"`](\w+)[\'"`]', 'fetch_with_method'),
            (r'fetch\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]\s*\)', 'fetch_simple'),
        ]

        for pattern, ptype in fetch_patterns:
            matches = re.finditer(pattern, script, re.DOTALL)
            for match in matches:
                if ptype == 'fetch_with_method':
                    url = match.group(1)
                    method = match.group(2).upper()
                elif ptype == 'fetch_simple':
                    url = match.group(1)
                    method = 'GET'

                api_calls.append({
                    'url': url,
                    'method': method,
                    'type': 'fetch'
                })

        # Look for $http calls (if using older Vue patterns)
        http_calls = re.finditer(r'\$http\.(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', script)
        for match in http_calls:
            api_calls.append({
                'url': match.group(2),
                'method': match.group(1).upper(),
                'type': '$http'
            })

        # Look for $api calls (custom API wrapper)
        # this.$api.post('warehouse/cycle-count/...')
        api_calls_match = re.finditer(r'\$api\.(get|post|put|patch|delete|head)\s*\(\s*[\'"`]([^\'"` ]+)[\'"`]', script)
        for match in api_calls_match:
            api_calls.append({
                'url': match.group(2),
                'method': match.group(1).upper(),
                'type': '$api'
            })

        return api_calls

    def _get_store_api_calls(self, script: str, component_file_path: str) -> List[Dict[str, str]]:
        """Extract API calls from Vuex store actions that are actually dispatched.

        Process:
        1. Find store.dispatch() calls in component
        2. Extract module name and action name
        3. Find the store actions file
        4. Parse ONLY the specific action that is dispatched
        5. Extract API calls from that action only
        """
        api_calls = []
        dispatched_actions = set()  # Track which actions are actually dispatched

        try:
            # Find store.dispatch() calls
            # Pattern: store.dispatch('moduleName/actionName', payload)
            # Pattern: store.dispatch(`${props.module}/actionName`, payload)
            dispatch_patterns = [
                r'store\.dispatch\s*\(\s*[\'"`]([^\'"`]+)/([^\'"`]+)[\'"`]',  # store.dispatch('module/action')
                r'store\.dispatch\s*\(\s*`\$\{[^}]+\}/([^`]+)`',  # store.dispatch(`${module}/action`)
            ]

            for pattern in dispatch_patterns:
                matches = re.finditer(pattern, script)
                for match in matches:
                    if len(match.groups()) == 2:
                        module_name = match.group(1)
                        action_name = match.group(2)
                    else:
                        # Dynamic module name - try to infer from props
                        action_name = match.group(1)
                        module_name = self._infer_store_module(script, component_file_path)

                    if not module_name or not action_name:
                        continue

                    # Create unique key for this action
                    action_key = f"{module_name}/{action_name}"

                    # Only parse each action once per component
                    if action_key in dispatched_actions:
                        continue
                    dispatched_actions.add(action_key)

                    # Find and parse this specific store action
                    store_api_calls = self._parse_store_action(module_name, action_name, component_file_path)
                    api_calls.extend(store_api_calls)

        except Exception as e:
            # Silently fail - store parsing is optional
            pass

        return api_calls

    def _infer_store_module(self, script: str, component_file_path: str) -> Optional[str]:
        """Infer store module name from component file path or props."""
        # Try to extract from file path
        # e.g., views/pages/Warehouse/cycleCount/... -> Warehouse/cycleCount
        path_parts = Path(component_file_path).parts

        if 'Warehouse' in path_parts:
            warehouse_index = path_parts.index('Warehouse')
            # Get the next part after Warehouse
            if warehouse_index + 1 < len(path_parts):
                next_part = path_parts[warehouse_index + 1]
                # Remove file extension
                module_part = next_part.replace('.vue', '').replace('index', '')
                if module_part:
                    return f"Warehouse/{module_part}"

        # Try to find module prop
        # props: { module: { ... } }
        # Then look for module: 'Warehouse/cycleCount'
        module_match = re.search(r'module:\s*[\'"]([^\'"`]+)[\'"]', script)
        if module_match:
            return module_match.group(1)

        return None

    def _parse_store_action(self, module_name: str, action_name: str, component_file_path: str) -> List[Dict[str, str]]:
        """Parse a Vuex store action file and extract API calls."""
        api_calls = []

        try:
            # Find store directory from component path
            # Component: .../resources/app/src/views/pages/Warehouse/...
            # Store: .../resources/app/src/store/Warehouse/cycleCount/actions.js
            parts = Path(component_file_path).parts
            if 'src' in parts:
                src_index = parts.index('src')
                src_dir = Path(*parts[:src_index + 1])

                # Build store actions path
                # module_name could be 'Warehouse/cycleCount'
                store_path = src_dir / 'store' / module_name / 'actions.js'

                if not store_path.exists():
                    return api_calls

                # Read and parse actions file
                with open(store_path, 'r', encoding='utf-8') as f:
                    actions_content = f.read()

                # Find the specific action function
                # Pattern: async actionName({ commit }, payload) {
                # Or: actionName(context, payload) {
                action_pattern = rf'(?:async\s+)?{re.escape(action_name)}\s*\([^)]*\)\s*{{'
                action_match = re.search(action_pattern, actions_content)

                if not action_match:
                    return api_calls

                # The match includes the opening brace, so start after it
                # Find where the opening { is in the match
                opening_brace_pos = action_match.group().rfind('{')
                start_pos = action_match.start() + opening_brace_pos + 1

                # Find the closing brace for this action
                brace_depth = 1
                end_pos = start_pos

                for i in range(start_pos, len(actions_content)):
                    if actions_content[i] == '{':
                        brace_depth += 1
                    elif actions_content[i] == '}':
                        brace_depth -= 1
                        if brace_depth == 0:
                            end_pos = i
                            break

                # Extract action body
                action_body = actions_content[start_pos:end_pos]

                # Extract API calls from action body
                action_api_calls = self._detect_api_calls(action_body)
                api_calls.extend(action_api_calls)

        except Exception as e:
            # Silently fail - store parsing is optional
            pass

        return api_calls

    def _analyze_vue_patterns(self, component: VueComponent) -> Dict[str, Any]:
        """Analyze Vue component patterns."""
        patterns = {
            'composition_api': 'setup' in component.script,
            'typescript': 'lang="ts"' in component.script,
            'state_management': self._detect_state_management(component.script),
            'component_communication': self._analyze_component_communication(component),
            'performance_patterns': self._analyze_performance_patterns(component)
        }

        return patterns

    def _detect_state_management(self, script: str) -> List[str]:
        """Detect state management patterns."""
        patterns = []

        if 'mapState' in script or 'mapGetters' in script:
            patterns.append('vuex')
        if 'useState' in script or 'reactive' in script:
            patterns.append('composition_api_state')
        if '$emit' in script:
            patterns.append('event_emitting')

        return patterns

    def _analyze_component_communication(self, component: VueComponent) -> Dict[str, Any]:
        """Analyze component communication patterns."""
        return {
            'props_count': len(component.props),
            'events_emitted': len(re.findall(r'\$emit', component.script)),
            'parent_child_communication': len(component.props) > 0,
            'event_bus_usage': '$eventBus' in component.script or 'eventBus' in component.script
        }

    def _analyze_performance_patterns(self, component: VueComponent) -> List[str]:
        """Analyze performance-related patterns."""
        patterns = []

        if 'v-once' in component.template:
            patterns.append('v-once_optimization')
        if 'keep-alive' in component.template:
            patterns.append('keep_alive')
        if 'lazy' in component.script or 'Lazy' in component.script:
            patterns.append('lazy_loading')

        return patterns

    def _analyze_controller_patterns(self, controller: LaravelController) -> Dict[str, Any]:
        """Analyze Laravel controller patterns."""
        patterns = {
            'restful': self._is_restful_controller(controller),
            'api_controller': 'Api' in controller.namespace,
            'resource_controller': self._has_resource_methods(controller),
            'middleware_usage': len(controller.middleware) > 0,
            'dependency_injection': self._uses_dependency_injection(controller)
        }

        return patterns

    def _is_restful_controller(self, controller: LaravelController) -> bool:
        """Check if controller follows RESTful conventions."""
        restful_methods = {'index', 'show', 'create', 'store', 'edit', 'update', 'destroy'}
        controller_methods = {method['name'] for method in controller.methods}
        return len(restful_methods.intersection(controller_methods)) >= 3

    def _has_resource_methods(self, controller: LaravelController) -> bool:
        """Check if controller has resource methods."""
        resource_methods = {'index', 'store', 'show', 'update', 'destroy'}
        controller_methods = {method['name'] for method in controller.methods}
        return len(resource_methods.intersection(controller_methods)) >= 2

    def _uses_dependency_injection(self, controller: LaravelController) -> bool:
        """Check if controller uses dependency injection."""
        # Look for type-hinted constructor parameters or method parameters
        return any('Request' in dep or 'Service' in dep for dep in controller.dependencies)

    def _analyze_model_patterns(self, model: LaravelModel) -> Dict[str, Any]:
        """Analyze Laravel model patterns."""
        patterns = {
            'has_relationships': len(model.relationships) > 0,
            'uses_scopes': len(model.scopes) > 0,
            'has_mutators': len(model.mutators) > 0,
            'has_accessors': len(model.accessors) > 0,
            'mass_assignment_protection': len(model.fillable) > 0,
            'relationship_types': list(set(rel['type'] for rel in model.relationships))
        }

        return patterns

    def _calculate_vue_metrics(self, component: VueComponent) -> Dict[str, Any]:
        """Calculate metrics for Vue component."""
        return {
            'template_lines': component.template.count('\n') + 1 if component.template else 0,
            'script_lines': component.script.count('\n') + 1 if component.script else 0,
            'style_lines': component.style.count('\n') + 1 if component.style else 0,
            'props_count': len(component.props),
            'methods_count': len(component.methods),
            'computed_count': len(component.computed),
            'watchers_count': len(component.watchers)
        }

    def _calculate_controller_metrics(self, controller: LaravelController) -> Dict[str, Any]:
        """Calculate metrics for Laravel controller."""
        return {
            'methods_count': len(controller.methods),
            'public_methods': len([m for m in controller.methods if m['visibility'] == 'public']),
            'action_methods': len([m for m in controller.methods if m['is_action']]),
            'middleware_count': len(controller.middleware),
            'dependencies_count': len(controller.dependencies)
        }

    def _calculate_model_metrics(self, model: LaravelModel) -> Dict[str, Any]:
        """Calculate metrics for Laravel model."""
        return {
            'fillable_count': len(model.fillable),
            'relationships_count': len(model.relationships),
            'scopes_count': len(model.scopes),
            'mutators_count': len(model.mutators),
            'accessors_count': len(model.accessors)
        }

    def _component_to_dict(self, component: VueComponent) -> Dict[str, Any]:
        """Convert VueComponent to dictionary."""
        return {
            'name': component.name,
            'props': component.props,
            'data': component.data,
            'methods': component.methods,
            'computed': component.computed,
            'watchers': component.watchers,
            'imports': component.imports,
            'file_path': component.file_path
        }

    def _controller_to_dict(self, controller: LaravelController) -> Dict[str, Any]:
        """Convert LaravelController to dictionary."""
        return {
            'name': controller.name,
            'methods': controller.methods,
            'middleware': controller.middleware,
            'dependencies': controller.dependencies,
            'routes': controller.routes,
            'namespace': controller.namespace,
            'file_path': controller.file_path
        }

    def _model_to_dict(self, model: LaravelModel) -> Dict[str, Any]:
        """Convert LaravelModel to dictionary."""
        return {
            'name': model.name,
            'table': model.table,
            'fillable': model.fillable,
            'relationships': model.relationships,
            'scopes': model.scopes,
            'mutators': model.mutators,
            'accessors': model.accessors,
            'file_path': model.file_path
        }
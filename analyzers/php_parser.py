"""
PHP code parser for legacy PHP 5.6 analysis.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass

@dataclass
class PHPFunction:
    name: str
    parameters: List[str]
    return_type: Optional[str]
    visibility: str
    is_static: bool
    line_start: int
    line_end: int
    docstring: Optional[str]

@dataclass
class PHPClass:
    name: str
    extends: Optional[str]
    implements: List[str]
    methods: List[PHPFunction]
    properties: List[Dict[str, Any]]
    constants: List[Dict[str, Any]]
    line_start: int
    line_end: int
    namespace: Optional[str]

@dataclass
class PHPInclude:
    type: str  # include, require, include_once, require_once
    path: str
    line: int
    is_dynamic: bool

class PHPParser:
    """Parser for PHP 5.6 legacy code analysis."""

    def __init__(self):
        self.classes = []
        self.functions = []
        self.includes = []
        self.globals = []
        self.constants = []
        self.current_namespace = None

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a PHP file and extract structure information."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()

            return self._parse_content(content, file_path)

        except Exception as e:
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _parse_content(self, content: str, file_path: str) -> Dict[str, Any]:
        """Parse PHP content and extract all relevant information."""
        lines = content.split('\n')

        # Reset state for new file
        self.classes = []
        self.functions = []
        self.includes = []
        self.globals = []
        self.constants = []
        self.current_namespace = None

        # Parse different elements
        self._parse_namespace(content)
        self._parse_includes(lines)
        self._parse_classes(content, lines)
        self._parse_functions(content, lines)
        self._parse_globals(lines)
        self._parse_constants(lines)

        # Analyze patterns
        patterns = self._analyze_patterns(content, lines)

        return {
            'file_path': file_path,
            'parsed': True,
            'namespace': self.current_namespace,
            'classes': [self._class_to_dict(cls) for cls in self.classes],
            'functions': [self._function_to_dict(func) for func in self.functions],
            'includes': [self._include_to_dict(inc) for inc in self.includes],
            'globals': self.globals,
            'constants': self.constants,
            'patterns': patterns,
            'metrics': self._calculate_metrics(content, lines)
        }

    def _parse_namespace(self, content: str):
        """Parse namespace declaration."""
        namespace_match = re.search(r'namespace\s+([\\\\\\w]+)\s*;', content)
        if namespace_match:
            self.current_namespace = namespace_match.group(1)

    def _parse_includes(self, lines: List[str]):
        """Parse include/require statements."""
        include_pattern = r'(include|require|include_once|require_once)\s*\(?\s*[\'"]([^\'"]+)[\'"]'

        for i, line in enumerate(lines):
            matches = re.findall(include_pattern, line, re.IGNORECASE)
            for match in matches:
                include_type, path = match
                is_dynamic = '$' in path or '{' in path

                self.includes.append(PHPInclude(
                    type=include_type.lower(),
                    path=path,
                    line=i + 1,
                    is_dynamic=is_dynamic
                ))

    def _parse_classes(self, content: str, lines: List[str]):
        """Parse class definitions."""
        # Pattern for class definition
        class_pattern = r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{'

        for match in re.finditer(class_pattern, content, re.IGNORECASE):
            class_name = match.group(1)
            extends = match.group(2)
            implements = [impl.strip() for impl in match.group(3).split(',')] if match.group(3) else []

            # Find class boundaries
            start_line = content[:match.start()].count('\n') + 1
            class_content = self._extract_class_content(content, match.start())
            end_line = start_line + class_content.count('\n')

            # Parse methods and properties
            methods = self._parse_class_methods(class_content, start_line)
            properties = self._parse_class_properties(class_content, start_line)
            constants = self._parse_class_constants(class_content, start_line)

            php_class = PHPClass(
                name=class_name,
                extends=extends,
                implements=implements,
                methods=methods,
                properties=properties,
                constants=constants,
                line_start=start_line,
                line_end=end_line,
                namespace=self.current_namespace
            )

            self.classes.append(php_class)

    def _extract_class_content(self, content: str, start_pos: int) -> str:
        """Extract the content of a class between braces."""
        brace_count = 0
        i = start_pos

        # Find opening brace
        while i < len(content) and content[i] != '{':
            i += 1

        if i >= len(content):
            return ""

        start = i
        brace_count = 1
        i += 1

        # Find matching closing brace
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1

        return content[start:i]

    def _parse_class_methods(self, class_content: str, class_start_line: int) -> List[PHPFunction]:
        """Parse methods within a class."""
        methods = []

        # Pattern for method definition
        method_pattern = r'(public|private|protected|static)?\s*(static)?\s*function\s+(\w+)\s*\(([^)]*)\)'

        for match in re.finditer(method_pattern, class_content, re.IGNORECASE):
            visibility = match.group(1) or 'public'
            is_static = bool(match.group(2)) or 'static' in (match.group(1) or '')
            method_name = match.group(3)
            params_str = match.group(4)

            # Parse parameters
            parameters = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        # Extract parameter name (remove type hints and default values)
                        param_match = re.search(r'\$(\w+)', param)
                        if param_match:
                            parameters.append(param_match.group(1))

            line_num = class_start_line + class_content[:match.start()].count('\n')

            method = PHPFunction(
                name=method_name,
                parameters=parameters,
                return_type=None,  # PHP 5.6 doesn't have return type hints
                visibility=visibility,
                is_static=is_static,
                line_start=line_num,
                line_end=line_num,  # Simplified for now
                docstring=None
            )

            methods.append(method)

        return methods

    def _parse_class_properties(self, class_content: str, class_start_line: int) -> List[Dict[str, Any]]:
        """Parse class properties."""
        properties = []

        # Pattern for property definition
        property_pattern = r'(public|private|protected)?\s*(static)?\s*\$(\w+)(?:\s*=\s*([^;]+))?;'

        for match in re.finditer(property_pattern, class_content, re.IGNORECASE):
            visibility = match.group(1) or 'public'
            is_static = bool(match.group(2))
            prop_name = match.group(3)
            default_value = match.group(4)

            line_num = class_start_line + class_content[:match.start()].count('\n')

            properties.append({
                'name': prop_name,
                'visibility': visibility,
                'is_static': is_static,
                'default_value': default_value.strip() if default_value else None,
                'line': line_num
            })

        return properties

    def _parse_class_constants(self, class_content: str, class_start_line: int) -> List[Dict[str, Any]]:
        """Parse class constants."""
        constants = []

        # Pattern for constant definition
        const_pattern = r'const\s+(\w+)\s*=\s*([^;]+);'

        for match in re.finditer(const_pattern, class_content, re.IGNORECASE):
            const_name = match.group(1)
            const_value = match.group(2).strip()

            line_num = class_start_line + class_content[:match.start()].count('\n')

            constants.append({
                'name': const_name,
                'value': const_value,
                'line': line_num
            })

        return constants

    def _parse_functions(self, content: str, lines: List[str]):
        """Parse standalone functions (not in classes)."""
        # Find functions that are not inside classes
        function_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'

        # Get class boundaries to exclude methods
        class_boundaries = []
        for cls in self.classes:
            class_boundaries.append((cls.line_start, cls.line_end))

        for match in re.finditer(function_pattern, content, re.IGNORECASE):
            func_name = match.group(1)
            params_str = match.group(2)

            line_num = content[:match.start()].count('\n') + 1

            # Check if this function is inside a class
            inside_class = any(start <= line_num <= end for start, end in class_boundaries)

            if not inside_class:
                # Parse parameters
                parameters = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if param:
                            param_match = re.search(r'\$(\w+)', param)
                            if param_match:
                                parameters.append(param_match.group(1))

                function = PHPFunction(
                    name=func_name,
                    parameters=parameters,
                    return_type=None,
                    visibility='public',
                    is_static=False,
                    line_start=line_num,
                    line_end=line_num,
                    docstring=None
                )

                self.functions.append(function)

    def _parse_globals(self, lines: List[str]):
        """Parse global variable declarations."""
        for i, line in enumerate(lines):
            # Look for global declarations
            global_matches = re.findall(r'global\s+(\$\w+(?:\s*,\s*\$\w+)*)', line, re.IGNORECASE)
            for match in global_matches:
                vars = [var.strip() for var in match.split(',')]
                for var in vars:
                    if var not in self.globals:
                        self.globals.append({
                            'name': var,
                            'line': i + 1
                        })

    def _parse_constants(self, lines: List[str]):
        """Parse define() statements for constants."""
        for i, line in enumerate(lines):
            # Look for define statements
            define_matches = re.findall(r'define\s*\(\s*[\'"](\w+)[\'"]\s*,\s*([^)]+)\)', line, re.IGNORECASE)
            for match in define_matches:
                const_name, const_value = match
                self.constants.append({
                    'name': const_name,
                    'value': const_value.strip(),
                    'line': i + 1
                })

    def _analyze_patterns(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Analyze code patterns and anti-patterns."""
        patterns = {
            'database_usage': self._detect_database_patterns(content),
            'security_issues': self._detect_security_patterns(content),
            'deprecated_features': self._detect_deprecated_features(content),
            'architectural_patterns': self._detect_architectural_patterns(content),
            'api_integrations': self._detect_api_patterns(content)
        }

        return patterns

    def _detect_database_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect database access patterns."""
        patterns = []

        # MySQL direct usage
        if re.search(r'mysql_', content, re.IGNORECASE):
            patterns.append({
                'type': 'mysql_direct',
                'description': 'Direct MySQL function usage (deprecated)',
                'severity': 'high'
            })

        # PDO usage
        if re.search(r'new\s+PDO', content, re.IGNORECASE):
            patterns.append({
                'type': 'pdo_usage',
                'description': 'PDO database access',
                'severity': 'low'
            })

        # SQL injection risks
        sql_concat = re.findall(r'\$\w+\s*\.\s*[\'"][^\'\"]*[\'\"]\s*\.\s*\$\w+', content)
        if sql_concat:
            patterns.append({
                'type': 'sql_concatenation',
                'description': 'Potential SQL injection through string concatenation',
                'severity': 'high',
                'occurrences': len(sql_concat)
            })

        return patterns

    def _detect_security_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect security-related patterns."""
        patterns = []

        # Direct $_GET/$_POST usage without sanitization
        if re.search(r'\$_(GET|POST|REQUEST)\[', content):
            patterns.append({
                'type': 'unsanitized_input',
                'description': 'Direct superglobal usage without apparent sanitization',
                'severity': 'medium'
            })

        # eval() usage
        if re.search(r'eval\s*\(', content, re.IGNORECASE):
            patterns.append({
                'type': 'eval_usage',
                'description': 'eval() function usage (security risk)',
                'severity': 'critical'
            })

        # Include with variables
        if re.search(r'(include|require).*\$', content, re.IGNORECASE):
            patterns.append({
                'type': 'dynamic_include',
                'description': 'Dynamic include/require (potential LFI)',
                'severity': 'high'
            })

        return patterns

    def _detect_deprecated_features(self, content: str) -> List[Dict[str, Any]]:
        """Detect deprecated PHP features."""
        patterns = []

        # PHP 4 style constructors
        php4_constructors = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*{[^}]*\$this', content, re.IGNORECASE)
        if php4_constructors:
            patterns.append({
                'type': 'php4_constructor',
                'description': 'PHP 4 style constructor',
                'severity': 'medium'
            })

        # Short tags
        if '<?=' in content or re.search(r'<\?\s(?!php)', content):
            patterns.append({
                'type': 'short_tags',
                'description': 'Short PHP tags usage',
                'severity': 'low'
            })

        return patterns

    def _detect_architectural_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect architectural patterns."""
        patterns = []

        # Singleton pattern
        if re.search(r'private\s+static\s+\$instance', content, re.IGNORECASE):
            patterns.append({
                'type': 'singleton',
                'description': 'Singleton pattern detected',
                'severity': 'info'
            })

        # Factory pattern
        if re.search(r'function\s+create\w*\(', content, re.IGNORECASE):
            patterns.append({
                'type': 'factory_method',
                'description': 'Factory method pattern detected',
                'severity': 'info'
            })

        return patterns

    def _detect_api_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Detect API integration patterns."""
        patterns = []

        # Common API patterns
        api_services = {
            'amazon': r'amazon|aws|s3',
            'shopify': r'shopify',
            'ups': r'ups.*shipping|ups.*api',
            'paypal': r'paypal',
            'stripe': r'stripe'
        }

        for service, pattern in api_services.items():
            if re.search(pattern, content, re.IGNORECASE):
                patterns.append({
                    'type': 'api_integration',
                    'service': service,
                    'description': f'{service.title()} API integration detected',
                    'severity': 'info'
                })

        # CURL usage
        if re.search(r'curl_', content, re.IGNORECASE):
            patterns.append({
                'type': 'curl_usage',
                'description': 'CURL library usage for HTTP requests',
                'severity': 'info'
            })

        return patterns

    def _calculate_metrics(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Calculate code metrics."""
        return {
            'lines_of_code': len(lines),
            'classes_count': len(self.classes),
            'functions_count': len(self.functions),
            'includes_count': len(self.includes),
            'complexity_score': self._calculate_complexity(content),
            'maintainability_score': self._calculate_maintainability(content, lines)
        }

    def _calculate_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity."""
        complexity_keywords = ['if', 'else', 'elseif', 'for', 'foreach', 'while', 'do', 'switch', 'case', 'catch']

        complexity = 1  # Base complexity
        for keyword in complexity_keywords:
            complexity += len(re.findall(rf'\\b{keyword}\\b', content, re.IGNORECASE))

        return complexity

    def _calculate_maintainability(self, content: str, lines: List[str]) -> float:
        """Calculate maintainability score (0-100)."""
        score = 100.0

        # Deduct for length
        if len(lines) > 500:
            score -= min(20, (len(lines) - 500) / 50)

        # Deduct for complexity
        complexity = self._calculate_complexity(content)
        if complexity > 50:
            score -= min(30, (complexity - 50) / 10)

        # Deduct for security issues
        security_patterns = self._detect_security_patterns(content)
        critical_issues = sum(1 for p in security_patterns if p['severity'] == 'critical')
        high_issues = sum(1 for p in security_patterns if p['severity'] == 'high')

        score -= critical_issues * 15
        score -= high_issues * 5

        return max(0, score)

    def _class_to_dict(self, cls: PHPClass) -> Dict[str, Any]:
        """Convert PHPClass to dictionary."""
        return {
            'name': cls.name,
            'extends': cls.extends,
            'implements': cls.implements,
            'methods': [self._function_to_dict(method) for method in cls.methods],
            'properties': cls.properties,
            'constants': cls.constants,
            'line_start': cls.line_start,
            'line_end': cls.line_end,
            'namespace': cls.namespace
        }

    def _function_to_dict(self, func: PHPFunction) -> Dict[str, Any]:
        """Convert PHPFunction to dictionary."""
        return {
            'name': func.name,
            'parameters': func.parameters,
            'return_type': func.return_type,
            'visibility': func.visibility,
            'is_static': func.is_static,
            'line_start': func.line_start,
            'line_end': func.line_end,
            'docstring': func.docstring
        }

    def _include_to_dict(self, inc: PHPInclude) -> Dict[str, Any]:
        """Convert PHPInclude to dictionary."""
        return {
            'type': inc.type,
            'path': inc.path,
            'line': inc.line,
            'is_dynamic': inc.is_dynamic
        }
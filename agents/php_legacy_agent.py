"""
PHP Legacy Agent for analyzing PHP 5.6 codebase.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import networkx as nx
from .base_agent import BaseAgent
from analyzers.php_parser import PHPParser

class PHPLegacyAgent(BaseAgent):
    """Agent specialized in analyzing legacy PHP 5.6 codebase."""

    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.php_parser = PHPParser()
        self.dependency_graph = nx.DiGraph()
        self.core_analysis_cache = None
        self._load_core_analysis()

    def _load_core_analysis(self):
        """Load the existing core project analysis."""
        try:
            analysis_path = self.config['analysis_files']['core_analysis']
            if os.path.exists(analysis_path):
                with open(analysis_path, 'r') as file:
                    self.core_analysis_cache = json.load(file)
                    self.logger.info(f"Loaded core analysis: {len(self.core_analysis_cache.get('files', []))} files")
        except Exception as e:
            self.logger.error(f"Failed to load core analysis: {e}")

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a specific PHP file."""
        self.logger.info(f"Analyzing PHP file: {file_path}")

        try:
            # Parse the file
            parsed_result = self.php_parser.parse_file(file_path)

            if not parsed_result['parsed']:
                return parsed_result

            # Enhance with additional analysis
            analysis = self._enhance_file_analysis(parsed_result)

            # Save insights
            self._save_file_insights(file_path, analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def _enhance_file_analysis(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance parsed result with additional analysis."""
        file_path = parsed_result['file_path']

        # Add migration recommendations
        migration_recommendations = self._analyze_migration_needs(parsed_result)

        # Add dependency analysis
        dependencies = self._analyze_dependencies(parsed_result)

        # Add modernization suggestions
        modernization = self._analyze_modernization_opportunities(parsed_result)

        # Add Laravel equivalents
        laravel_equivalents = self._find_laravel_equivalents(parsed_result)

        enhanced = parsed_result.copy()
        enhanced.update({
            'migration_recommendations': migration_recommendations,
            'dependencies': dependencies,
            'modernization': modernization,
            'laravel_equivalents': laravel_equivalents,
            'analysis_timestamp': self._get_timestamp()
        })

        return enhanced

    def _analyze_migration_needs(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what needs to be migrated from this file."""
        recommendations = {
            'priority': 'medium',
            'complexity': 'medium',
            'issues': [],
            'required_changes': [],
            'estimated_effort': 'medium'
        }

        patterns = parsed_result.get('patterns', {})

        # Check for high-priority migration issues
        if patterns.get('security_issues'):
            for issue in patterns['security_issues']:
                if issue['severity'] in ['critical', 'high']:
                    recommendations['priority'] = 'high'
                    recommendations['issues'].append(f"Security issue: {issue['description']}")

        # Check for deprecated features
        if patterns.get('deprecated_features'):
            recommendations['issues'].extend([
                f"Deprecated: {feature['description']}"
                for feature in patterns['deprecated_features']
            ])

        # Check database patterns
        if patterns.get('database_usage'):
            for db_pattern in patterns['database_usage']:
                if db_pattern['type'] == 'mysql_direct':
                    recommendations['required_changes'].append(
                        "Convert MySQL direct functions to Eloquent ORM"
                    )
                    recommendations['complexity'] = 'high'

        # Check for API integrations
        api_patterns = [p for p in patterns.get('api_integrations', []) if p['type'] == 'api_integration']
        if api_patterns:
            recommendations['required_changes'].append(
                f"Migrate API integrations: {', '.join([p['service'] for p in api_patterns])}"
            )

        # Calculate estimated effort
        effort_factors = len(recommendations['issues']) + len(recommendations['required_changes'])
        if effort_factors > 5:
            recommendations['estimated_effort'] = 'high'
        elif effort_factors < 2:
            recommendations['estimated_effort'] = 'low'

        return recommendations

    def _analyze_dependencies(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file dependencies."""
        dependencies = {
            'includes': [],
            'class_dependencies': [],
            'function_calls': [],
            'global_dependencies': []
        }

        # Process includes
        for include in parsed_result.get('includes', []):
            dependencies['includes'].append({
                'path': include['path'],
                'type': include['type'],
                'is_dynamic': include['is_dynamic'],
                'migration_status': self._check_migration_status(include['path'])
            })

        # Analyze class extensions and implementations
        for cls in parsed_result.get('classes', []):
            if cls['extends']:
                dependencies['class_dependencies'].append({
                    'type': 'extends',
                    'class': cls['extends'],
                    'source_class': cls['name']
                })

            for interface in cls['implements']:
                dependencies['class_dependencies'].append({
                    'type': 'implements',
                    'interface': interface,
                    'source_class': cls['name']
                })

        return dependencies

    def _analyze_modernization_opportunities(self, parsed_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze opportunities for code modernization."""
        opportunities = []

        # Check for PHP 4 style constructors
        for cls in parsed_result.get('classes', []):
            for method in cls['methods']:
                if method['name'] == cls['name']:  # PHP 4 style constructor
                    opportunities.append({
                        'type': 'constructor_modernization',
                        'description': f"Convert PHP 4 constructor in class {cls['name']} to __construct()",
                        'class': cls['name'],
                        'priority': 'medium'
                    })

        # Check for global variables that could be dependency injected
        if parsed_result.get('globals'):
            opportunities.append({
                'type': 'dependency_injection',
                'description': "Consider converting global variables to dependency injection",
                'globals': [g['name'] for g in parsed_result['globals']],
                'priority': 'low'
            })

        # Check for direct database access
        patterns = parsed_result.get('patterns', {})
        db_patterns = patterns.get('database_usage', [])
        if any(p['type'] == 'mysql_direct' for p in db_patterns):
            opportunities.append({
                'type': 'orm_migration',
                'description': "Migrate direct MySQL functions to Laravel Eloquent ORM",
                'priority': 'high'
            })

        return opportunities

    def _find_laravel_equivalents(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Find Laravel equivalents for PHP constructs."""
        equivalents = {
            'classes': [],
            'functions': [],
            'patterns': []
        }

        # Map common patterns to Laravel equivalents
        pattern_mappings = {
            'database_access': {
                'mysql_direct': 'Eloquent ORM / Query Builder',
                'pdo_usage': 'Eloquent ORM / Query Builder'
            },
            'authentication': {
                'session_management': 'Laravel Auth facade',
                'password_hashing': 'Hash facade'
            },
            'routing': {
                'manual_routing': 'Laravel Route facade',
                'url_parsing': 'Laravel Request class'
            },
            'templating': {
                'php_templates': 'Blade templating engine'
            }
        }

        # Analyze classes for Laravel equivalents
        for cls in parsed_result.get('classes', []):
            laravel_equivalent = self._find_class_equivalent(cls)
            if laravel_equivalent:
                equivalents['classes'].append({
                    'original_class': cls['name'],
                    'laravel_equivalent': laravel_equivalent,
                    'migration_notes': self._get_migration_notes(cls, laravel_equivalent)
                })

        return equivalents

    def _find_class_equivalent(self, cls: Dict[str, Any]) -> Optional[str]:
        """Find Laravel equivalent for a PHP class."""
        class_name = cls['name'].lower()

        # Common mapping patterns
        if 'database' in class_name or 'db' in class_name:
            return 'Eloquent Model'
        elif 'auth' in class_name or 'login' in class_name:
            return 'Laravel Auth'
        elif 'mail' in class_name or 'email' in class_name:
            return 'Laravel Mail'
        elif 'cache' in class_name:
            return 'Laravel Cache'
        elif 'session' in class_name:
            return 'Laravel Session'
        elif 'file' in class_name or 'upload' in class_name:
            return 'Laravel Storage'

        return None

    def _get_migration_notes(self, cls: Dict[str, Any], laravel_equivalent: str) -> str:
        """Get migration notes for a class."""
        if laravel_equivalent == 'Eloquent Model':
            return "Convert to Eloquent model with proper relationships and mutators"
        elif laravel_equivalent == 'Laravel Auth':
            return "Use Laravel's built-in authentication system"
        elif laravel_equivalent == 'Laravel Mail':
            return "Use Laravel's Mail facade and Mailable classes"

        return f"Consider migrating to {laravel_equivalent}"

    def analyze_module(self, module_path: str) -> Dict[str, Any]:
        """Analyze a module/directory of PHP files."""
        self.logger.info(f"Analyzing PHP module: {module_path}")

        module_analysis = {
            'module_path': module_path,
            'files': [],
            'summary': {},
            'migration_plan': {},
            'dependencies': {}
        }

        # Get all PHP files in the module
        php_files = self._get_php_files(module_path)

        # Analyze each file
        for file_path in php_files:
            file_analysis = self.analyze_file(file_path)
            module_analysis['files'].append(file_analysis)

        # Generate module summary
        module_analysis['summary'] = self._generate_module_summary(module_analysis['files'])

        # Generate migration plan
        module_analysis['migration_plan'] = self._generate_migration_plan(module_analysis['files'])

        # Analyze module dependencies
        module_analysis['dependencies'] = self._analyze_module_dependencies(module_analysis['files'])

        # Save module insights
        self._save_module_insights(module_path, module_analysis)

        return module_analysis

    def _get_php_files(self, module_path: str) -> List[str]:
        """Get all PHP files in a module."""
        php_files = []
        extensions = self.config['agents']['php_legacy']['extensions']
        ignore_patterns = self.config['agents']['php_legacy']['ignore_patterns']

        for root, dirs, files in os.walk(module_path):
            # Remove ignored directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in ignore_patterns)]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    php_files.append(file_path)

        return php_files

    def _generate_module_summary(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary for a module."""
        summary = {
            'total_files': len(file_analyses),
            'total_classes': 0,
            'total_functions': 0,
            'migration_priorities': {'high': 0, 'medium': 0, 'low': 0},
            'common_patterns': {},
            'security_issues': 0,
            'api_integrations': []
        }

        for analysis in file_analyses:
            if not analysis.get('parsed', False):
                continue

            # Count classes and functions
            summary['total_classes'] += len(analysis.get('classes', []))
            summary['total_functions'] += len(analysis.get('functions', []))

            # Count migration priorities
            migration = analysis.get('migration_recommendations', {})
            priority = migration.get('priority', 'medium')
            summary['migration_priorities'][priority] += 1

            # Count security issues
            patterns = analysis.get('patterns', {})
            security_issues = patterns.get('security_issues', [])
            summary['security_issues'] += len([
                issue for issue in security_issues
                if issue['severity'] in ['critical', 'high']
            ])

            # Collect API integrations
            api_patterns = patterns.get('api_integrations', [])
            for pattern in api_patterns:
                if pattern['type'] == 'api_integration':
                    service = pattern['service']
                    if service not in summary['api_integrations']:
                        summary['api_integrations'].append(service)

        return summary

    def _generate_migration_plan(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate migration plan for a module."""
        plan = {
            'phases': [],
            'estimated_effort': 'medium',
            'prerequisites': [],
            'risks': []
        }

        # Phase 1: Security and critical issues
        critical_files = [
            analysis for analysis in file_analyses
            if analysis.get('migration_recommendations', {}).get('priority') == 'high'
        ]

        if critical_files:
            plan['phases'].append({
                'phase': 1,
                'name': 'Critical Security and Database Migration',
                'files': [f['file_path'] for f in critical_files],
                'description': 'Address security vulnerabilities and database access patterns',
                'estimated_days': len(critical_files) * 2
            })

        # Phase 2: Core functionality migration
        medium_files = [
            analysis for analysis in file_analyses
            if analysis.get('migration_recommendations', {}).get('priority') == 'medium'
        ]

        if medium_files:
            plan['phases'].append({
                'phase': 2,
                'name': 'Core Functionality Migration',
                'files': [f['file_path'] for f in medium_files],
                'description': 'Migrate core business logic and functionality',
                'estimated_days': len(medium_files) * 1.5
            })

        # Phase 3: Remaining files and cleanup
        low_files = [
            analysis for analysis in file_analyses
            if analysis.get('migration_recommendations', {}).get('priority') == 'low'
        ]

        if low_files:
            plan['phases'].append({
                'phase': 3,
                'name': 'Cleanup and Optimization',
                'files': [f['file_path'] for f in low_files],
                'description': 'Migrate remaining files and optimize code',
                'estimated_days': len(low_files) * 1
            })

        # Calculate total effort
        total_days = sum(phase.get('estimated_days', 0) for phase in plan['phases'])
        if total_days > 30:
            plan['estimated_effort'] = 'high'
        elif total_days < 10:
            plan['estimated_effort'] = 'low'

        return plan

    def _analyze_module_dependencies(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dependencies within a module."""
        dependencies = {
            'internal_dependencies': [],
            'external_dependencies': [],
            'circular_dependencies': [],
            'dependency_graph': {}
        }

        # Build dependency graph
        for analysis in file_analyses:
            file_path = analysis['file_path']
            file_deps = analysis.get('dependencies', {})

            for include in file_deps.get('includes', []):
                include_path = include['path']
                dependencies['dependency_graph'][file_path] = dependencies['dependency_graph'].get(file_path, [])
                dependencies['dependency_graph'][file_path].append(include_path)

        # Detect circular dependencies
        # This is a simplified check - could be enhanced with proper graph analysis
        for file_path, deps in dependencies['dependency_graph'].items():
            for dep in deps:
                if dep in dependencies['dependency_graph']:
                    dep_deps = dependencies['dependency_graph'][dep]
                    if file_path in dep_deps:
                        dependencies['circular_dependencies'].append({
                            'file1': file_path,
                            'file2': dep
                        })

        return dependencies

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a specific file."""
        analysis = self.analyze_file(file_path)
        dependencies = []

        if analysis.get('parsed', False):
            file_deps = analysis.get('dependencies', {})
            for include in file_deps.get('includes', []):
                dependencies.append(include['path'])

        return dependencies

    def get_migration_status(self, file_path: str) -> Dict[str, Any]:
        """Get migration status for a file."""
        # Check if there's a corresponding Laravel file
        laravel_equivalent = self._find_laravel_file_equivalent(file_path)

        return {
            'file_path': file_path,
            'laravel_equivalent': laravel_equivalent,
            'migration_completed': laravel_equivalent is not None,
            'last_analyzed': self._get_timestamp()
        }

    def _find_laravel_file_equivalent(self, php_file_path: str) -> Optional[str]:
        """Find Laravel equivalent file if it exists."""
        # This would check the Laravel codebase for equivalent functionality
        # Implementation would depend on your Laravel project structure
        return None

    def _check_migration_status(self, include_path: str) -> str:
        """Check if an included file has been migrated."""
        # Simplified check - could be enhanced with actual migration tracking
        return "pending"

    def _save_file_insights(self, file_path: str, analysis: Dict[str, Any]):
        """Save insights from file analysis."""
        # Save migration recommendations
        migration = analysis.get('migration_recommendations', {})
        if migration.get('issues'):
            self.save_insight(
                file_path,
                'migration_issues',
                json.dumps(migration['issues']),
                0.9
            )

        # Save security issues
        patterns = analysis.get('patterns', {})
        security_issues = patterns.get('security_issues', [])
        if security_issues:
            critical_issues = [issue for issue in security_issues if issue['severity'] == 'critical']
            if critical_issues:
                self.save_insight(
                    file_path,
                    'security_critical',
                    json.dumps(critical_issues),
                    1.0
                )

    def _save_module_insights(self, module_path: str, analysis: Dict[str, Any]):
        """Save insights from module analysis."""
        summary = analysis.get('summary', {})

        # Save module summary
        self.save_insight(
            module_path,
            'module_summary',
            json.dumps(summary),
            0.8
        )

        # Save migration plan
        migration_plan = analysis.get('migration_plan', {})
        if migration_plan.get('phases'):
            self.save_insight(
                module_path,
                'migration_plan',
                json.dumps(migration_plan),
                0.9
            )

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_unmigrated_functions(self) -> List[Dict[str, Any]]:
        """Get list of functions that haven't been migrated yet."""
        # This would cross-reference with Laravel analysis
        # For now, return a placeholder
        return []

    def find_api_integrations(self) -> List[Dict[str, Any]]:
        """Find all API integrations in the codebase."""
        integrations = []

        if self.core_analysis_cache:
            # Search through cached analysis for API patterns
            files = self.core_analysis_cache.get('files', [])
            for file_info in files:
                file_path = file_info.get('path', '')
                # Re-analyze file for API patterns if needed
                analysis = self.analyze_file(file_path)
                patterns = analysis.get('patterns', {})
                api_patterns = patterns.get('api_integrations', [])

                for pattern in api_patterns:
                    if pattern['type'] == 'api_integration':
                        integrations.append({
                            'file': file_path,
                            'service': pattern['service'],
                            'description': pattern['description']
                        })

        return integrations
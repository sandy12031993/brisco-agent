"""
Coordinator Agent for orchestrating multi-agent analysis and providing unified interface.
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional AI provider imports
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base_agent import BaseAgent
from .php_legacy_agent import PHPLegacyAgent
from .laravel_agent import LaravelAgent
from .database_agent import DatabaseAgent

class CoordinatorAgent(BaseAgent):
    """Coordinator agent that orchestrates multiple specialized agents."""

    def __init__(self, config_path: str):
        super().__init__(config_path)

        # Initialize specialized agents
        self.php_agent = PHPLegacyAgent(config_path)
        self.laravel_agent = LaravelAgent(config_path)
        self.database_agent = DatabaseAgent(config_path)

        # Initialize Claude client if API key is available
        self.claude_client = None
        self._init_claude_client()

        # Track ongoing analyses
        self.active_analyses = {}

    def _init_claude_client(self):
        """Initialize Claude API client if available."""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.claude_client = anthropic.Anthropic(api_key=api_key)
                self.logger.info("Claude client initialized successfully")
            else:
                self.logger.warning("ANTHROPIC_API_KEY not set - complex reasoning will be limited")
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude client: {e}")

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file using the appropriate specialized agent."""
        self.logger.info(f"Coordinating analysis of file: {file_path}")

        try:
            # Determine which agent should handle this file
            agent = self._select_agent_for_file(file_path)

            if not agent:
                return {
                    'error': 'No suitable agent found for file type',
                    'file_path': file_path,
                    'parsed': False
                }

            # Perform analysis with selected agent
            analysis = agent.analyze_file(file_path)

            # Enhance with cross-agent insights
            enhanced_analysis = self._enhance_with_cross_agent_insights(analysis, file_path)

            # Save coordination insights
            self._save_coordination_insights(file_path, enhanced_analysis)

            return enhanced_analysis

        except Exception as e:
            self.logger.error(f"Error in coordinated analysis of {file_path}: {e}")
            return {
                'error': str(e),
                'file_path': file_path,
                'parsed': False
            }

    def analyze_module(self, module_path: str) -> Dict[str, Any]:
        """Analyze a module using multiple agents in coordination."""
        self.logger.info(f"Coordinating module analysis: {module_path}")

        try:
            # Get all relevant files in the module
            files = self._get_all_files_in_module(module_path)

            # Group files by agent type
            file_groups = self._group_files_by_agent(files)

            # Perform parallel analysis with each agent
            agent_results = self._perform_parallel_agent_analysis(file_groups)

            # Synthesize results across agents
            module_analysis = self._synthesize_module_analysis(module_path, agent_results)

            # Generate cross-agent insights
            module_analysis['cross_agent_insights'] = self._generate_cross_agent_insights(agent_results)

            # Generate migration recommendations
            module_analysis['migration_recommendations'] = self._generate_migration_recommendations(agent_results)

            return module_analysis

        except Exception as e:
            self.logger.error(f"Error in coordinated module analysis of {module_path}: {e}")
            return {
                'error': str(e),
                'module_path': module_path,
                'analyzed': False
            }

    def _select_agent_for_file(self, file_path: str) -> Optional[BaseAgent]:
        """Select the appropriate agent for a file based on its characteristics."""
        file_path_lower = file_path.lower()
        file_extension = Path(file_path).suffix.lower()

        # Database files
        if file_extension == '.sql' or 'migration' in file_path_lower:
            return self.database_agent

        # Laravel/Vue files
        if (file_extension in ['.vue', '.js', '.ts'] or
            'laravel/' in file_path_lower or
            '/app/' in file_path_lower or
            'Controller' in file_path or
            'Model' in file_path):
            return self.laravel_agent

        # PHP Legacy files (default for .php files)
        if file_extension == '.php':
            # Check if it's in core directory or legacy patterns
            if 'core/' in file_path_lower or not ('laravel/' in file_path_lower):
                return self.php_agent
            else:
                return self.laravel_agent

        return None

    def _enhance_with_cross_agent_insights(self, analysis: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Enhance analysis with insights from other agents."""
        enhanced = analysis.copy()

        # Add cross-references
        cross_references = self._find_cross_references(file_path, analysis)
        enhanced['cross_references'] = cross_references

        # Add migration context
        migration_context = self._get_migration_context(file_path, analysis)
        enhanced['migration_context'] = migration_context

        # Add dependency map
        dependency_map = self._build_dependency_map(file_path, analysis)
        enhanced['dependency_map'] = dependency_map

        return enhanced

    def _find_cross_references(self, file_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Find cross-references between different parts of the system."""
        references = {
            'related_core_files': [],
            'related_laravel_files': [],
            'related_database_elements': [],
            'api_connections': []
        }

        # Extract entities from the analysis
        entities = self._extract_entities_from_analysis(analysis)

        # Search for related files in other parts of the system
        for entity in entities:
            # Find related core files
            core_files = self._find_related_files_by_entity(entity, 'core')
            references['related_core_files'].extend(core_files)

            # Find related Laravel files
            laravel_files = self._find_related_files_by_entity(entity, 'laravel')
            references['related_laravel_files'].extend(laravel_files)

            # Find related database elements
            db_elements = self._find_related_database_elements(entity)
            references['related_database_elements'].extend(db_elements)

        return references

    def _extract_entities_from_analysis(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract entity names from analysis results."""
        entities = []

        # Extract class names
        if 'classes' in analysis:
            entities.extend([cls['name'] for cls in analysis['classes']])

        # Extract function names
        if 'functions' in analysis:
            entities.extend([func['name'] for func in analysis['functions']])

        # Extract table names
        if 'tables' in analysis:
            entities.extend(list(analysis['tables'].keys()))

        # Extract component names
        if 'component' in analysis:
            entities.append(analysis['component']['name'])

        # Extract controller/model names
        if 'controller' in analysis:
            entities.append(analysis['controller']['name'])

        if 'model' in analysis:
            entities.append(analysis['model']['name'])

        return entities

    def _find_related_files_by_entity(self, entity: str, system_type: str) -> List[str]:
        """Find files related to an entity in a specific system."""
        related_files = []

        # This would search through cached analyses for entity references
        # For now, return placeholder structure

        return related_files

    def _find_related_database_elements(self, entity: str) -> List[str]:
        """Find database elements related to an entity."""
        related_elements = []

        # This would search through database schema for related tables/columns
        # For now, return placeholder structure

        return related_elements

    def _get_migration_context(self, file_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get migration context for a file."""
        context = {
            'migration_status': 'unknown',
            'equivalent_files': [],
            'migration_priority': 'medium',
            'blocking_dependencies': [],
            'migration_complexity': 'medium'
        }

        # Determine migration status based on file location and analysis
        if 'core/' in file_path.lower():
            # This is a core file - check if it has Laravel equivalent
            context['migration_status'] = 'needs_migration'
            context['equivalent_files'] = self._find_laravel_equivalents(file_path, analysis)
        elif 'laravel/' in file_path.lower():
            # This is a Laravel file - check if it's complete
            context['migration_status'] = 'migrated'
            context['equivalent_files'] = self._find_core_equivalents(file_path, analysis)

        # Determine migration priority based on analysis results
        if analysis.get('patterns', {}).get('security_issues'):
            critical_issues = [
                issue for issue in analysis['patterns']['security_issues']
                if issue.get('severity') == 'critical'
            ]
            if critical_issues:
                context['migration_priority'] = 'high'

        return context

    def _find_laravel_equivalents(self, core_file_path: str, analysis: Dict[str, Any]) -> List[str]:
        """Find Laravel equivalents for a core file."""
        # This would search through Laravel analysis for equivalent functionality
        return []

    def _find_core_equivalents(self, laravel_file_path: str, analysis: Dict[str, Any]) -> List[str]:
        """Find core equivalents for a Laravel file."""
        # This would search through core analysis for equivalent functionality
        return []

    def _build_dependency_map(self, file_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build a dependency map for the file."""
        dependency_map = {
            'direct_dependencies': [],
            'indirect_dependencies': [],
            'dependents': [],
            'circular_dependencies': []
        }

        # Extract direct dependencies from analysis
        if 'dependencies' in analysis:
            dependency_map['direct_dependencies'] = analysis['dependencies']

        # This would build a more comprehensive dependency graph
        # For now, return the basic structure

        return dependency_map

    def _get_all_files_in_module(self, module_path: str) -> List[str]:
        """Get all relevant files in a module."""
        files = []

        # Get all file extensions we can handle
        php_extensions = self.config['agents']['php_legacy']['extensions']
        laravel_extensions = self.config['agents']['laravel']['extensions']
        db_extensions = ['.sql', '.php']  # PHP for migrations

        all_extensions = set(php_extensions + laravel_extensions + db_extensions)

        for root, dirs, filenames in os.walk(module_path):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in all_extensions):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)

        return files

    def _group_files_by_agent(self, files: List[str]) -> Dict[str, List[str]]:
        """Group files by the agent that should handle them."""
        groups = {
            'php_legacy': [],
            'laravel': [],
            'database': []
        }

        for file_path in files:
            agent = self._select_agent_for_file(file_path)

            if agent == self.php_agent:
                groups['php_legacy'].append(file_path)
            elif agent == self.laravel_agent:
                groups['laravel'].append(file_path)
            elif agent == self.database_agent:
                groups['database'].append(file_path)

        return groups

    def _perform_parallel_agent_analysis(self, file_groups: Dict[str, List[str]]) -> Dict[str, Any]:
        """Perform parallel analysis using multiple agents."""
        results = {
            'php_legacy': [],
            'laravel': [],
            'database': []
        }

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            # Submit analysis tasks for each agent
            if file_groups['php_legacy']:
                future = executor.submit(self._analyze_files_with_agent, self.php_agent, file_groups['php_legacy'])
                futures['php_legacy'] = future

            if file_groups['laravel']:
                future = executor.submit(self._analyze_files_with_agent, self.laravel_agent, file_groups['laravel'])
                futures['laravel'] = future

            if file_groups['database']:
                future = executor.submit(self._analyze_files_with_agent, self.database_agent, file_groups['database'])
                futures['database'] = future

            # Collect results
            for agent_type, future in futures.items():
                try:
                    results[agent_type] = future.result(timeout=300)  # 5 minute timeout
                except Exception as e:
                    self.logger.error(f"Error in {agent_type} agent analysis: {e}")
                    results[agent_type] = []

        return results

    def _analyze_files_with_agent(self, agent: BaseAgent, files: List[str]) -> List[Dict[str, Any]]:
        """Analyze a list of files with a specific agent."""
        results = []

        for file_path in files:
            try:
                analysis = agent.analyze_file(file_path)
                results.append(analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path} with {agent.__class__.__name__}: {e}")
                results.append({
                    'error': str(e),
                    'file_path': file_path,
                    'parsed': False
                })

        return results

    def _synthesize_module_analysis(self, module_path: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from multiple agents into a unified module analysis."""
        synthesis = {
            'module_path': module_path,
            'analyzed': True,
            'summary': {},
            'agent_results': agent_results,
            'analysis_timestamp': self._get_timestamp()
        }

        # Calculate summary statistics
        total_files = sum(len(results) for results in agent_results.values())
        parsed_files = sum(
            len([r for r in results if r.get('parsed', False)])
            for results in agent_results.values()
        )

        synthesis['summary'] = {
            'total_files_analyzed': total_files,
            'successfully_parsed': parsed_files,
            'parse_success_rate': (parsed_files / total_files * 100) if total_files > 0 else 0,
            'php_legacy_files': len(agent_results.get('php_legacy', [])),
            'laravel_files': len(agent_results.get('laravel', [])),
            'database_files': len(agent_results.get('database', []))
        }

        return synthesis

    def _generate_cross_agent_insights(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights that span across multiple agents."""
        insights = {
            'migration_completeness': self._analyze_migration_completeness(agent_results),
            'architectural_patterns': self._identify_architectural_patterns(agent_results),
            'integration_gaps': self._find_integration_gaps(agent_results),
            'data_flow_analysis': self._analyze_data_flow(agent_results),
            'security_assessment': self._assess_security_across_agents(agent_results)
        }

        return insights

    def _analyze_migration_completeness(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze migration completeness across all agents."""
        completeness = {
            'overall_score': 0,
            'core_to_laravel_mapping': {},
            'unmigrated_functionality': [],
            'incomplete_migrations': []
        }

        php_results = agent_results.get('php_legacy', [])
        laravel_results = agent_results.get('laravel', [])

        # Count core files vs Laravel equivalents
        core_classes = []
        laravel_classes = []

        for result in php_results:
            if result.get('parsed') and 'classes' in result:
                core_classes.extend([cls['name'] for cls in result['classes']])

        for result in laravel_results:
            if result.get('parsed'):
                if 'controller' in result:
                    laravel_classes.append(result['controller']['name'])
                if 'model' in result:
                    laravel_classes.append(result['model']['name'])

        # Calculate migration score
        if core_classes:
            migrated_count = len(set(core_classes) & set(laravel_classes))
            completeness['overall_score'] = (migrated_count / len(core_classes)) * 100

        return completeness

    def _identify_architectural_patterns(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Identify architectural patterns across the system."""
        patterns = {
            'mvc_adherence': 'unknown',
            'design_patterns': [],
            'anti_patterns': [],
            'consistency_score': 0
        }

        # Analyze patterns from Laravel results
        laravel_results = agent_results.get('laravel', [])

        has_controllers = any('controller' in result for result in laravel_results if result.get('parsed'))
        has_models = any('model' in result for result in laravel_results if result.get('parsed'))
        has_views = any('vue_component' in result.get('type', '') for result in laravel_results if result.get('parsed'))

        if has_controllers and has_models and has_views:
            patterns['mvc_adherence'] = 'good'
        elif has_controllers and has_models:
            patterns['mvc_adherence'] = 'partial'
        else:
            patterns['mvc_adherence'] = 'poor'

        return patterns

    def _find_integration_gaps(self, agent_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find integration gaps between different parts of the system."""
        gaps = []

        # Check for API endpoint mismatches
        laravel_results = agent_results.get('laravel', [])
        vue_components = [r for r in laravel_results if r.get('type') == 'vue_component']
        controllers = [r for r in laravel_results if r.get('type') == 'laravel_controller']

        # Find Vue components with API calls that don't have corresponding controllers
        for component_result in vue_components:
            if component_result.get('parsed'):
                api_analysis = component_result.get('api_analysis', {})
                api_calls = api_analysis.get('api_calls', [])

                for api_call in api_calls:
                    # Check if there's a corresponding controller endpoint
                    has_controller = any(
                        api_call in str(ctrl_result.get('controller', {}).get('routes', []))
                        for ctrl_result in controllers
                        if ctrl_result.get('parsed')
                    )

                    if not has_controller:
                        gaps.append({
                            'type': 'missing_api_endpoint',
                            'component_file': component_result['file_path'],
                            'api_call': api_call,
                            'description': f'Vue component calls {api_call} but no corresponding controller found'
                        })

        return gaps

    def _analyze_data_flow(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data flow across the system."""
        data_flow = {
            'frontend_to_backend': [],
            'backend_to_database': [],
            'data_consistency_issues': [],
            'flow_completeness': 'unknown'
        }

        # This would analyze the complete data flow from Vue components
        # through Laravel controllers to database models
        # For now, return basic structure

        return data_flow

    def _assess_security_across_agents(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess security across all agents."""
        security = {
            'overall_risk_level': 'low',
            'critical_issues': [],
            'security_gaps': [],
            'recommendations': []
        }

        all_results = []
        for agent_type, results in agent_results.items():
            all_results.extend(results)

        # Collect security issues from all analyses
        for result in all_results:
            if result.get('parsed'):
                patterns = result.get('patterns', {})
                security_issues = patterns.get('security_issues', [])

                for issue in security_issues:
                    if issue.get('severity') == 'critical':
                        security['critical_issues'].append({
                            'file': result['file_path'],
                            'issue': issue
                        })

        # Determine overall risk level
        if security['critical_issues']:
            security['overall_risk_level'] = 'critical'
        elif len(security['critical_issues']) > 5:
            security['overall_risk_level'] = 'high'

        return security

    def _generate_migration_recommendations(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate migration recommendations based on all agent analyses."""
        recommendations = {
            'immediate_actions': [],
            'short_term_plan': [],
            'long_term_plan': [],
            'risk_mitigation': []
        }

        # Analyze results to generate recommendations
        php_results = agent_results.get('php_legacy', [])

        # Find high-priority migration items
        for result in php_results:
            if result.get('parsed'):
                migration_rec = result.get('migration_recommendations', {})
                if migration_rec.get('priority') == 'high':
                    recommendations['immediate_actions'].append({
                        'file': result['file_path'],
                        'action': 'Migrate high-priority file',
                        'reason': 'Contains security issues or critical functionality'
                    })

        return recommendations

    def generate_comprehensive_report(self, scope: str = 'all') -> Dict[str, Any]:
        """Generate a comprehensive migration analysis report."""
        self.logger.info(f"Generating comprehensive report for scope: {scope}")

        report = {
            'report_type': 'comprehensive_migration_analysis',
            'scope': scope,
            'generated_at': self._get_timestamp(),
            'executive_summary': {},
            'detailed_analysis': {},
            'recommendations': {},
            'next_steps': []
        }

        try:
            # Perform comprehensive analysis based on scope
            if scope == 'all':
                # Analyze entire project
                core_path = self.config['project']['core_path']
                laravel_path = self.config['project']['laravel_path']

                core_analysis = self.analyze_module(core_path)
                laravel_analysis = self.analyze_module(laravel_path)

                report['detailed_analysis']['core'] = core_analysis
                report['detailed_analysis']['laravel'] = laravel_analysis

            # Generate executive summary
            report['executive_summary'] = self._generate_executive_summary(report['detailed_analysis'])

            # Generate recommendations
            report['recommendations'] = self._generate_comprehensive_recommendations(report['detailed_analysis'])

            # Generate next steps
            report['next_steps'] = self._generate_next_steps(report['recommendations'])

            # Use Claude for enhanced analysis if available
            if self.claude_client:
                report['ai_insights'] = self._get_claude_insights(report)

        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            report['error'] = str(e)

        return report

    def _generate_executive_summary(self, detailed_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from detailed analysis."""
        summary = {
            'migration_status': 'in_progress',
            'overall_health': 'good',
            'critical_issues': 0,
            'completion_percentage': 0,
            'key_achievements': [],
            'major_concerns': []
        }

        # Analyze detailed results to generate summary
        # This would be more comprehensive in a real implementation

        return summary

    def _generate_comprehensive_recommendations(self, detailed_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive recommendations."""
        recommendations = {
            'technical': [],
            'architectural': [],
            'security': [],
            'performance': [],
            'process': []
        }

        # Generate recommendations based on analysis
        # This would be more detailed in a real implementation

        return recommendations

    def _generate_next_steps(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized next steps."""
        next_steps = []

        # Convert recommendations into actionable steps
        # This would be more detailed in a real implementation

        return next_steps

    def _get_claude_insights(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Get enhanced insights using Claude API."""
        insights = {
            'strategic_analysis': '',
            'risk_assessment': '',
            'optimization_opportunities': '',
            'architectural_recommendations': ''
        }

        try:
            # Prepare context for Claude
            context = {
                'project_type': 'PHP to Laravel migration',
                'summary': report.get('executive_summary', {}),
                'key_issues': report.get('recommendations', {})
            }

            # Use Claude for strategic analysis
            response = self.claude_client.messages.create(
                model=self.config['anthropic']['model'],
                max_tokens=self.config['anthropic']['max_tokens'],
                messages=[{
                    "role": "user",
                    "content": f"""Analyze this PHP to Laravel migration project and provide strategic insights:

                    Context: {json.dumps(context, indent=2)}

                    Please provide:
                    1. Strategic analysis of the migration progress
                    2. Risk assessment and mitigation strategies
                    3. Optimization opportunities
                    4. Architectural recommendations

                    Focus on actionable insights for technical leadership."""
                }]
            )

            insights['strategic_analysis'] = response.content[0].text

        except Exception as e:
            self.logger.error(f"Error getting Claude insights: {e}")
            insights['error'] = str(e)

        return insights

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a file using the appropriate agent."""
        agent = self._select_agent_for_file(file_path)
        if agent:
            return agent.get_dependencies(file_path)
        return []

    def _save_coordination_insights(self, file_path: str, analysis: Dict[str, Any]):
        """Save coordination-specific insights."""
        # Save cross-references
        cross_refs = analysis.get('cross_references', {})
        if cross_refs.get('related_core_files') or cross_refs.get('related_laravel_files'):
            self.save_insight(
                file_path,
                'cross_references',
                json.dumps(cross_refs),
                0.8
            )

        # Save migration context
        migration_context = analysis.get('migration_context', {})
        if migration_context.get('migration_status') != 'unknown':
            self.save_insight(
                file_path,
                'migration_context',
                json.dumps(migration_context),
                0.9
            )

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    # Placeholder methods for interface compatibility
    def analyze_module(self, module_path: str) -> Dict[str, Any]:
        """Implemented above - this maintains interface compatibility."""
        pass
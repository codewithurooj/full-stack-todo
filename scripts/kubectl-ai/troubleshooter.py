"""Kubernetes troubleshooting analyzer using AI.

Analyzes problems and suggests diagnostic commands and solutions.
"""

from typing import Dict, Any, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ai_provider import get_ai_provider
from shared.k8s_client import K8sClient
from shared.error_handler import ErrorHandler
import logging

logger = logging.getLogger(__name__)


class KubectlTroubleshooter:
    """AI-powered Kubernetes troubleshooting."""

    def __init__(self, config: Any):
        """Initialize troubleshooter.

        Args:
            config: Configuration object
        """
        self.config = config
        self.ai_provider = get_ai_provider(config)

        try:
            self.k8s_client = K8sClient()
        except Exception as e:
            logger.warning(f"Could not initialize K8s client: {e}")
            self.k8s_client = None

    def analyze(self, problem: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a Kubernetes problem.

        Args:
            problem: Description of the problem
            context: Additional context (namespace, resource info, etc.)

        Returns:
            Dictionary with analysis results
        """
        # Gather cluster information if available
        cluster_info = self._gather_cluster_info(context)

        # Generate AI analysis
        analysis = self._ai_analyze(problem, cluster_info)

        return analysis

    def _gather_cluster_info(self, context: Dict[str, Any] = None) -> str:
        """Gather relevant cluster information.

        Args:
            context: Context dictionary with namespace, resource hints

        Returns:
            Formatted cluster info string
        """
        if not self.k8s_client:
            return "Cluster information unavailable (kubectl not configured)"

        info_parts = []

        try:
            # Get cluster summary
            cluster_info = self.k8s_client.get_cluster_info()
            info_parts.append(f"Cluster: {cluster_info['nodes']} nodes, {cluster_info['pods']} pods")

            # Get namespace info if specified
            if context and context.get('namespace'):
                namespace = context['namespace']
                pods = self.k8s_client.get_pods(namespace=namespace)
                info_parts.append(f"Namespace '{namespace}': {len(pods)} pods")

                # Check for unhealthy pods
                unhealthy = [
                    p for p in pods
                    if p.status.phase != 'Running'
                ]
                if unhealthy:
                    info_parts.append(f"  {len(unhealthy)} pods not running")

        except Exception as e:
            logger.warning(f"Error gathering cluster info: {e}")
            info_parts.append(f"Error gathering cluster info: {e}")

        return '\n'.join(info_parts)

    def _ai_analyze(self, problem: str, cluster_info: str) -> Dict[str, Any]:
        """Use AI to analyze the problem.

        Args:
            problem: Problem description
            cluster_info: Cluster information context

        Returns:
            Analysis dictionary
        """
        system_prompt = """You are a Kubernetes expert troubleshooter.
Analyze problems and provide:
1. Clear explanation of likely causes
2. Specific diagnostic commands to run
3. Actionable solutions

Be concise and practical. Focus on the most common issues first."""

        user_prompt = f"""Problem: {problem}

Cluster Context:
{cluster_info}

Provide:
1. Explanation: What is likely causing this?
2. Diagnostic Commands: kubectl commands to investigate (list 3-5 commands)
3. Solutions: Step-by-step fixes (3-5 specific actions)

Format as:
EXPLANATION:
[your explanation]

COMMANDS:
- kubectl command 1
- kubectl command 2
...

SOLUTIONS:
1. First solution step
2. Second solution step
..."""

        try:
            response = self.ai_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=1000,
                temperature=0.5
            )

            # Parse response
            analysis = self._parse_analysis(response)
            analysis['raw_response'] = response

            return analysis

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return {
                'explanation': f"Unable to perform AI analysis: {e}",
                'commands': self._get_generic_diagnostic_commands(problem),
                'suggestions': self._get_generic_suggestions(problem),
                'error': str(e)
            }

    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format.

        Args:
            response: AI response text

        Returns:
            Structured analysis dictionary
        """
        sections = {
            'explanation': '',
            'commands': [],
            'suggestions': []
        }

        current_section = None
        lines = response.split('\n')

        for line in lines:
            line = line.strip()

            if 'EXPLANATION:' in line.upper():
                current_section = 'explanation'
                continue
            elif 'COMMANDS:' in line.upper() or 'DIAGNOSTIC' in line.upper():
                current_section = 'commands'
                continue
            elif 'SOLUTIONS:' in line.upper() or 'FIXES:' in line.upper():
                current_section = 'suggestions'
                continue

            if current_section == 'explanation' and line:
                sections['explanation'] += line + ' '
            elif current_section == 'commands' and line:
                # Extract kubectl commands
                if line.startswith('-') or line.startswith('•'):
                    cmd = line.lstrip('-•').strip()
                    if cmd:
                        sections['commands'].append(cmd)
            elif current_section == 'suggestions' and line:
                # Extract suggestions
                if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                    suggestion = line.lstrip('0123456789.-•').strip()
                    if suggestion:
                        sections['suggestions'].append(suggestion)

        sections['explanation'] = sections['explanation'].strip()

        return sections

    def _get_generic_diagnostic_commands(self, problem: str) -> List[str]:
        """Get generic diagnostic commands based on problem keywords.

        Args:
            problem: Problem description

        Returns:
            List of diagnostic kubectl commands
        """
        commands = []
        problem_lower = problem.lower()

        # Always useful
        commands.append("kubectl get pods --all-namespaces")
        commands.append("kubectl get nodes")

        if 'pod' in problem_lower:
            commands.append("kubectl describe pod <pod-name>")
            commands.append("kubectl logs <pod-name>")

        if 'crash' in problem_lower or 'fail' in problem_lower:
            commands.append("kubectl get events --sort-by=.metadata.creationTimestamp")
            commands.append("kubectl logs <pod-name> --previous")

        if 'deploy' in problem_lower:
            commands.append("kubectl describe deployment <deployment-name>")
            commands.append("kubectl rollout status deployment <deployment-name>")

        if 'service' in problem_lower or 'connect' in problem_lower:
            commands.append("kubectl get svc")
            commands.append("kubectl get endpoints")

        if 'resource' in problem_lower or 'memory' in problem_lower or 'cpu' in problem_lower:
            commands.append("kubectl top nodes")
            commands.append("kubectl top pods")

        return commands[:5]  # Return top 5

    def _get_generic_suggestions(self, problem: str) -> List[str]:
        """Get generic troubleshooting suggestions.

        Args:
            problem: Problem description

        Returns:
            List of suggestions
        """
        suggestions = []
        problem_lower = problem.lower()

        if 'crash' in problem_lower or 'restart' in problem_lower:
            suggestions.append("Check pod logs for error messages")
            suggestions.append("Verify resource limits are not too restrictive")
            suggestions.append("Check liveness and readiness probes configuration")

        if 'connect' in problem_lower or 'access' in problem_lower:
            suggestions.append("Verify service selector matches pod labels")
            suggestions.append("Check network policies")
            suggestions.append("Ensure service port matches container port")

        if 'pending' in problem_lower:
            suggestions.append("Check if there are sufficient node resources")
            suggestions.append("Verify PersistentVolume availability if using storage")
            suggestions.append("Check for taints on nodes")

        if not suggestions:
            suggestions.append("Check pod status and logs")
            suggestions.append("Review recent events")
            suggestions.append("Verify configuration and resource availability")

        return suggestions

    def quick_diagnose(self, resource_type: str, resource_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Perform quick diagnosis of a specific resource.

        Args:
            resource_type: Type of resource (pod, deployment, etc.)
            resource_name: Name of resource
            namespace: Kubernetes namespace

        Returns:
            Diagnosis results
        """
        if not self.k8s_client:
            return {
                'error': 'Kubernetes client not available',
                'suggestions': ['Configure kubectl and try again']
            }

        diagnosis = {
            'resource': f"{resource_type}/{resource_name}",
            'namespace': namespace,
            'issues': [],
            'suggestions': []
        }

        try:
            if resource_type == 'pod':
                pods = self.k8s_client.get_pods(namespace=namespace)
                pod = next((p for p in pods if p.metadata.name == resource_name), None)

                if not pod:
                    diagnosis['issues'].append("Pod not found")
                    diagnosis['suggestions'].append("Verify pod name and namespace")
                    return diagnosis

                # Check pod status
                if pod.status.phase != 'Running':
                    diagnosis['issues'].append(f"Pod is in {pod.status.phase} state")

                # Check container statuses
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if not container.ready:
                            diagnosis['issues'].append(f"Container {container.name} not ready")

                            if container.state.waiting:
                                reason = container.state.waiting.reason
                                diagnosis['issues'].append(f"Waiting: {reason}")
                                if reason == 'CrashLoopBackOff':
                                    diagnosis['suggestions'].append("Check logs for crash cause")
                                elif reason == 'ImagePullBackOff':
                                    diagnosis['suggestions'].append("Verify image name and registry access")

        except Exception as e:
            diagnosis['error'] = str(e)

        return diagnosis

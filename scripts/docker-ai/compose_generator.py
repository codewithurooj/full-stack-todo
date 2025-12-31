"""Docker Compose generator for docker-ai.

Generates docker-compose.yml files for multi-service applications.
"""

from typing import Dict, Any, List
import yaml
import logging

logger = logging.getLogger(__name__)


class ComposeGenerator:
    """Generates docker-compose.yml files."""

    # Default service configurations
    SERVICE_CONFIGS = {
        'postgresql': {
            'image': 'postgres:16-alpine',
            'environment': {
                'POSTGRES_USER': 'user',
                'POSTGRES_PASSWORD': 'password',
                'POSTGRES_DB': 'database'
            },
            'volumes': ['postgres_data:/var/lib/postgresql/data'],
            'ports': ['5432:5432']
        },
        'mysql': {
            'image': 'mysql:8-oracle',
            'environment': {
                'MYSQL_ROOT_PASSWORD': 'rootpass',
                'MYSQL_DATABASE': 'database',
                'MYSQL_USER': 'user',
                'MYSQL_PASSWORD': 'password'
            },
            'volumes': ['mysql_data:/var/lib/mysql'],
            'ports': ['3306:3306']
        },
        'mongodb': {
            'image': 'mongo:7',
            'environment': {
                'MONGO_INITDB_ROOT_USERNAME': 'root',
                'MONGO_INITDB_ROOT_PASSWORD': 'password'
            },
            'volumes': ['mongo_data:/data/db'],
            'ports': ['27017:27017']
        },
        'redis': {
            'image': 'redis:7-alpine',
            'volumes': ['redis_data:/data'],
            'ports': ['6379:6379']
        },
        'rabbitmq': {
            'image': 'rabbitmq:3-management-alpine',
            'environment': {
                'RABBITMQ_DEFAULT_USER': 'user',
                'RABBITMQ_DEFAULT_PASS': 'password'
            },
            'ports': ['5672:5672', '15672:15672']
        },
        'elasticsearch': {
            'image': 'elasticsearch:8.11.0',
            'environment': {
                'discovery.type': 'single-node',
                'ES_JAVA_OPTS': '-Xms512m -Xmx512m'
            },
            'volumes': ['elastic_data:/usr/share/elasticsearch/data'],
            'ports': ['9200:9200']
        },
        'nginx': {
            'image': 'nginx:alpine',
            'ports': ['80:80'],
            'volumes': ['./nginx.conf:/etc/nginx/nginx.conf:ro']
        }
    }

    def __init__(self, config: Any):
        """Initialize compose generator.

        Args:
            config: Configuration object
        """
        self.config = config

    def generate(self, spec: Dict[str, Any]) -> str:
        """Generate docker-compose.yml.

        Args:
            spec: Application specification

        Returns:
            docker-compose.yml content as YAML string
        """
        language = spec.get('language', 'python')
        framework = spec.get('framework')
        services = spec.get('services', [])
        ports = spec.get('ports', [8000])

        # Build compose structure
        compose = {
            'version': '3.8',
            'services': {},
            'volumes': {}
        }

        # Add main application service
        app_service = self._create_app_service(language, framework, ports, services)
        compose['services']['app'] = app_service

        # Add dependent services
        for service in services:
            if service in self.SERVICE_CONFIGS:
                compose['services'][service] = self.SERVICE_CONFIGS[service].copy()

                # Add volume definition
                for volume in self.SERVICE_CONFIGS[service].get('volumes', []):
                    volume_name = volume.split(':')[0]
                    if not volume_name.startswith('.'):
                        compose['volumes'][volume_name] = {}

        # Convert to YAML
        return yaml.dump(compose, default_flow_style=False, sort_keys=False)

    def _create_app_service(
        self,
        language: str,
        framework: str,
        ports: List[int],
        dependencies: List[str]
    ) -> Dict[str, Any]:
        """Create application service configuration.

        Args:
            language: Programming language
            framework: Framework
            ports: Port numbers
            dependencies: Service dependencies

        Returns:
            Service configuration dict
        """
        service = {
            'build': '.',
            'ports': [f"{p}:{p}" for p in ports],
            'environment': {}
        }

        # Add environment variables for services
        if 'postgresql' in dependencies:
            service['environment'].update({
                'DATABASE_URL': 'postgresql://user:password@postgresql:5432/database',
                'DB_HOST': 'postgresql',
                'DB_PORT': '5432',
                'DB_USER': 'user',
                'DB_PASSWORD': 'password',
                'DB_NAME': 'database'
            })
            service['depends_on'] = service.get('depends_on', []) + ['postgresql']

        if 'mysql' in dependencies:
            service['environment'].update({
                'DATABASE_URL': 'mysql://user:password@mysql:3306/database',
                'DB_HOST': 'mysql',
                'DB_PORT': '3306'
            })
            service['depends_on'] = service.get('depends_on', []) + ['mysql']

        if 'mongodb' in dependencies:
            service['environment'].update({
                'MONGO_URL': 'mongodb://root:password@mongodb:27017',
                'MONGO_HOST': 'mongodb',
                'MONGO_PORT': '27017'
            })
            service['depends_on'] = service.get('depends_on', []) + ['mongodb']

        if 'redis' in dependencies:
            service['environment'].update({
                'REDIS_URL': 'redis://redis:6379',
                'REDIS_HOST': 'redis',
                'REDIS_PORT': '6379'
            })
            service['depends_on'] = service.get('depends_on', []) + ['redis']

        # Add restart policy
        service['restart'] = 'unless-stopped'

        # Add volumes for development
        service['volumes'] = ['.:/app']

        return service

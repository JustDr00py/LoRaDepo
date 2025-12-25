"""Global configuration for LoRaDB Instance Manager."""

from pathlib import Path
import os


class Config:
    """Global application configuration."""

    # Paths
    INSTANCES_ROOT = Path.home() / ".loradb-instances"
    LORADB_TEMPLATE = Path("/home/sysadmin/Documents/LoRaDepo/LoRaDB")
    UI_TEMPLATE = Path("/home/sysadmin/Documents/LoRaDepo/LoRaDB-UI")

    # Port allocation
    PORT_RANGE_MIN = 8000
    PORT_RANGE_MAX = 9999

    # Default ports
    DEFAULT_LORADB_PORT = 8443
    DEFAULT_UI_BACKEND_PORT = 3001
    DEFAULT_UI_FRONTEND_PORT = 3000

    # Docker
    DOCKER_COMPOSE_TIMEOUT = 120  # seconds
    CONTAINER_HEALTH_CHECK_TIMEOUT = 60  # seconds

    # UI
    LOG_TAIL_LINES = 100
    STATUS_REFRESH_INTERVAL = 5  # seconds

    @classmethod
    def validate(cls):
        """
        Validate configuration on startup.

        Raises:
            RuntimeError: If configuration is invalid
        """
        # Check templates exist
        if not cls.LORADB_TEMPLATE.exists():
            raise RuntimeError(
                f"LoRaDB template not found at {cls.LORADB_TEMPLATE}. "
                "Please ensure LoRaDB directory exists."
            )

        if not cls.UI_TEMPLATE.exists():
            raise RuntimeError(
                f"LoRaDB-UI template not found at {cls.UI_TEMPLATE}. "
                "Please ensure LoRaDB-UI directory exists."
            )

        # Test Docker connection
        try:
            import docker
            client = docker.from_env()
            client.ping()
        except Exception as e:
            raise RuntimeError(
                f"Docker is not available: {e}\n"
                "Please ensure Docker is installed and running."
            )

        # Create instances root if it doesn't exist
        cls.INSTANCES_ROOT.mkdir(parents=True, exist_ok=True)

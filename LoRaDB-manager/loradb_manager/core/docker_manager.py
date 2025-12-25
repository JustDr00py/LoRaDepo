"""Docker management for LoRaDB instances."""

import docker
from docker.errors import DockerException, NotFound
import subprocess
import time
from pathlib import Path
from typing import Generator, Optional
from .instance import InstanceMetadata, InstanceStatus
from ..config import Config


class DockerManager:
    """Manages Docker operations for instances using Docker Python SDK."""

    def __init__(self):
        """
        Initialize Docker manager and test connection.

        Raises:
            RuntimeError: If Docker daemon is not available
        """
        try:
            self.client = docker.from_env()
            self.client.ping()
        except DockerException as e:
            raise RuntimeError(f"Docker daemon not available: {e}")

    def start_instance(self, metadata: InstanceMetadata):
        """
        Start instance using docker-compose up -d.

        Starts LoRaDB first, waits for health check, then starts UI.

        Args:
            metadata: Instance metadata

        Raises:
            RuntimeError: If docker-compose command fails
        """
        loradb_compose = Path(metadata.loradb_dir) / "docker-compose.yml"
        ui_compose = Path(metadata.ui_dir) / "docker-compose.yml"

        # Start LoRaDB first with unique project name
        self._compose_up(loradb_compose, f"loradb-{metadata.instance_id}")

        # Wait for LoRaDB to be healthy
        try:
            self._wait_for_container_healthy(
                f"loradb-{metadata.instance_id}",
                timeout=Config.CONTAINER_HEALTH_CHECK_TIMEOUT
            )
        except TimeoutError:
            # If health check times out, just wait for container to be running
            self._wait_for_container_running(
                f"loradb-{metadata.instance_id}",
                timeout=30
            )

        # Start UI services with unique project name
        self._compose_up(ui_compose, f"loradb-ui-{metadata.instance_id}")

        # Update container IDs
        self._update_container_ids(metadata)

    def stop_instance(self, metadata: InstanceMetadata):
        """
        Stop instance using docker-compose down.

        Stops UI first, then LoRaDB.

        Args:
            metadata: Instance metadata

        Raises:
            RuntimeError: If docker-compose command fails
        """
        ui_compose = Path(metadata.ui_dir) / "docker-compose.yml"
        loradb_compose = Path(metadata.loradb_dir) / "docker-compose.yml"

        # Stop UI first with unique project name
        self._compose_down(ui_compose, f"loradb-ui-{metadata.instance_id}")

        # Then stop LoRaDB with unique project name
        self._compose_down(loradb_compose, f"loradb-{metadata.instance_id}")

    def restart_instance(self, metadata: InstanceMetadata):
        """
        Restart instance.

        Args:
            metadata: Instance metadata
        """
        self.stop_instance(metadata)
        time.sleep(2)  # Brief pause between stop and start
        self.start_instance(metadata)

    def rebuild_instance(self, metadata: InstanceMetadata):
        """
        Rebuild instance (stops, rebuilds Docker images, starts).

        This rebuilds the Docker images from the templates, which is useful when
        the LoRaDB or UI code has been updated.

        Args:
            metadata: Instance metadata

        Raises:
            RuntimeError: If docker-compose command fails
        """
        loradb_compose = Path(metadata.loradb_dir) / "docker-compose.yml"
        ui_compose = Path(metadata.ui_dir) / "docker-compose.yml"

        # Stop containers first
        self.stop_instance(metadata)
        time.sleep(2)

        # Rebuild LoRaDB image
        self._compose_build(loradb_compose, f"loradb-{metadata.instance_id}")

        # Rebuild UI images
        self._compose_build(ui_compose, f"loradb-ui-{metadata.instance_id}")

        # Start with new images
        self.start_instance(metadata)

    def get_instance_status(self, metadata: InstanceMetadata) -> InstanceStatus:
        """
        Get aggregated status of all containers for an instance.

        Args:
            metadata: Instance metadata

        Returns:
            InstanceStatus enum value
        """
        try:
            container_names = [
                f"loradb-{metadata.instance_id}",
                f"loradb-ui-backend-{metadata.instance_id}",
                f"loradb-ui-frontend-{metadata.instance_id}"
            ]

            statuses = []
            for name in container_names:
                try:
                    container = self.client.containers.get(name)
                    statuses.append(container.status)
                except NotFound:
                    statuses.append("not_found")

            # If all containers not found, instance is stopped
            if all(s == "not_found" for s in statuses):
                return InstanceStatus.STOPPED

            # If all running, instance is running
            if all(s == "running" for s in statuses if s != "not_found"):
                return InstanceStatus.RUNNING

            # If any running, instance is starting/partially started
            if any(s == "running" for s in statuses):
                return InstanceStatus.STARTING

            # If any exited or dead
            if any(s in ["exited", "dead"] for s in statuses):
                return InstanceStatus.ERROR

            return InstanceStatus.UNKNOWN

        except Exception:
            return InstanceStatus.ERROR

    def stream_logs(self, container_name: str, tail: int = 100) -> Generator[str, None, None]:
        """
        Stream logs from a container.

        Args:
            container_name: Name of container to stream logs from
            tail: Number of initial lines to retrieve

        Yields:
            Log lines as strings
        """
        try:
            container = self.client.containers.get(container_name)

            # Stream logs
            for line in container.logs(stream=True, follow=True, tail=tail):
                yield line.decode('utf-8', errors='replace')

        except NotFound:
            yield f"Container {container_name} not found\n"
        except Exception as e:
            yield f"Error streaming logs: {e}\n"

    def remove_containers(self, metadata: InstanceMetadata):
        """
        Remove containers for an instance (if they exist).

        Args:
            metadata: Instance metadata
        """
        container_names = [
            f"loradb-{metadata.instance_id}",
            f"loradb-ui-backend-{metadata.instance_id}",
            f"loradb-ui-frontend-{metadata.instance_id}"
        ]

        for name in container_names:
            try:
                container = self.client.containers.get(name)
                container.remove(force=True)
            except NotFound:
                pass

    def remove_network(self, network_name: str):
        """
        Remove Docker network.

        Args:
            network_name: Name of network to remove
        """
        try:
            network = self.client.networks.get(network_name)
            network.remove()
        except NotFound:
            pass

    def remove_volume(self, volume_name: str):
        """
        Remove Docker volume.

        Args:
            volume_name: Name of volume to remove
        """
        try:
            volume = self.client.volumes.get(volume_name)
            volume.remove()
        except NotFound:
            pass

    def _compose_up(self, compose_file: Path, project_name: str):
        """
        Execute docker compose up -d.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Unique project name for this compose stack

        Raises:
            RuntimeError: If command fails
        """
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_file), "up", "-d"],
            cwd=compose_file.parent,
            capture_output=True,
            text=True,
            timeout=Config.DOCKER_COMPOSE_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker compose up failed: {result.stderr}")

    def _compose_down(self, compose_file: Path, project_name: str):
        """
        Execute docker compose down.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Unique project name for this compose stack

        Raises:
            RuntimeError: If command fails
        """
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_file), "down"],
            cwd=compose_file.parent,
            capture_output=True,
            text=True,
            timeout=Config.DOCKER_COMPOSE_TIMEOUT
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker compose down failed: {result.stderr}")

    def _compose_build(self, compose_file: Path, project_name: str):
        """
        Execute docker compose build.

        Args:
            compose_file: Path to docker-compose.yml
            project_name: Unique project name for this compose stack

        Raises:
            RuntimeError: If command fails
        """
        result = subprocess.run(
            ["docker", "compose", "-p", project_name, "-f", str(compose_file), "build", "--no-cache"],
            cwd=compose_file.parent,
            capture_output=True,
            text=True,
            timeout=Config.DOCKER_COMPOSE_TIMEOUT * 3  # Building takes longer
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker compose build failed: {result.stderr}")

    def _wait_for_container_healthy(self, container_name: str, timeout: int = 60):
        """
        Wait for container to be healthy.

        Args:
            container_name: Name of container
            timeout: Maximum time to wait in seconds

        Raises:
            TimeoutError: If container doesn't become healthy within timeout
            RuntimeError: If container stops running
        """
        start = time.time()

        while time.time() - start < timeout:
            try:
                container = self.client.containers.get(container_name)
                health = container.attrs.get("State", {}).get("Health", {}).get("Status")

                if health == "healthy":
                    return
                elif container.status != "running":
                    raise RuntimeError(f"Container {container_name} not running (status: {container.status})")

            except NotFound:
                pass

            time.sleep(1)

        raise TimeoutError(f"Container {container_name} did not become healthy within {timeout} seconds")

    def _wait_for_container_running(self, container_name: str, timeout: int = 30):
        """
        Wait for container to be running.

        Args:
            container_name: Name of container
            timeout: Maximum time to wait in seconds

        Raises:
            TimeoutError: If container doesn't start within timeout
        """
        start = time.time()

        while time.time() - start < timeout:
            try:
                container = self.client.containers.get(container_name)
                if container.status == "running":
                    return
            except NotFound:
                pass

            time.sleep(1)

        raise TimeoutError(f"Container {container_name} did not start within {timeout} seconds")

    def _update_container_ids(self, metadata: InstanceMetadata):
        """
        Update metadata with current container IDs.

        Args:
            metadata: Instance metadata to update
        """
        try:
            loradb = self.client.containers.get(f"loradb-{metadata.instance_id}")
            backend = self.client.containers.get(f"loradb-ui-backend-{metadata.instance_id}")
            frontend = self.client.containers.get(f"loradb-ui-frontend-{metadata.instance_id}")

            metadata.loradb_container_id = loradb.id
            metadata.ui_backend_container_id = backend.id
            metadata.ui_frontend_container_id = frontend.id
        except NotFound:
            pass

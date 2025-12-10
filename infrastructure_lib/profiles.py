"""
Platform Profiles (Golden Paths) for different environments.

Profiles define sensible defaults for Dev, Staging, and Production environments.
Each profile can be customized via override parameters.
"""

from typing import Any

from .config import ClusterConfig, NetworkConfig


class PlatformProfile:
    """
    Base class for Platform Profiles (Golden Paths).

    Enforces naming conventions and provides common configuration patterns.

    Args:
        project_id: GCP project ID
        region: GCP region (e.g., europe-west1)
        env: Environment name (dev, staging, prod)
        prefix: Resource naming prefix (e.g., myapp)
    """

    def __init__(self, project_id: str, region: str, env: str, prefix: str):
        self.project_id = project_id
        self.region = region
        self.env = env
        self.prefix = prefix

    @property
    def common_labels(self) -> dict:
        """Standard labels applied to all resources."""
        return {"environment": self.env, "managed-by": "cdktf", "project": self.project_id}

    def get_network_config(self, **overrides: Any) -> NetworkConfig:
        """
        Get network configuration with optional overrides.

        Args:
            **overrides: Override any NetworkConfig parameter
                        (e.g., cidr="10.1.0.0/16")

        Returns:
            NetworkConfig instance
        """
        defaults = {
            "project_id": self.project_id,
            "region": self.region,
            "env": self.env,
            "prefix": self.prefix,
        }
        return NetworkConfig(**{**defaults, **overrides})

    def get_cluster_config(self, **overrides: Any) -> ClusterConfig:
        """
        Get cluster configuration with optional overrides.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_cluster_config")


class DevProfile(PlatformProfile):
    """
    Development Profile: Cost-optimized, relaxed availability.

    Features:
    - Single zone deployment
    - Spot/Preemptible instances enabled
    - Smaller machine types
    - Lower node count limits
    """

    def get_cluster_config(self, **overrides: Any) -> ClusterConfig:
        """
        Get dev-optimized cluster configuration.

        Default settings:
        - machine_type: e2-medium (cost-effective)
        - max_nodes: 3 (limited scaling)
        - spot_instances: True (cost savings)
        - disk_size: 50GB
        """
        defaults = {
            "project_id": self.project_id,
            "region": self.region,
            "env": self.env,
            "prefix": self.prefix,
            "machine_type": "e2-medium",
            "node_count": 1,
            "min_nodes": 1,
            "max_nodes": 3,
            "spot_instances": True,
            "disk_size": 50,
        }
        return ClusterConfig(**{**defaults, **overrides})


class ProdProfile(PlatformProfile):
    """
    Production Profile: High Availability, Performance, Stability.

    Features:
    - Higher node counts for HA
    - No spot instances (stability)
    - Larger machine types
    - Higher disk sizes
    """

    def get_cluster_config(self, **overrides: Any) -> ClusterConfig:
        """
        Get production-optimized cluster configuration.

        Default settings:
        - machine_type: n2-standard-4 (balanced performance)
        - min_nodes: 3 (HA guarantee)
        - max_nodes: 10 (scaling headroom)
        - spot_instances: False (stability)
        - disk_size: 100GB
        """
        defaults = {
            "project_id": self.project_id,
            "region": self.region,
            "env": self.env,
            "prefix": self.prefix,
            "machine_type": "n2-standard-4",
            "node_count": 3,
            "min_nodes": 3,
            "max_nodes": 10,
            "spot_instances": False,
            "disk_size": 100,
        }
        return ClusterConfig(**{**defaults, **overrides})


class StagingProfile(PlatformProfile):
    """
    Staging Profile: Production-like but cost-conscious.

    Features:
    - Similar to prod for testing
    - Slightly smaller resources
    - Spot instances allowed
    """

    def get_cluster_config(self, **overrides: Any) -> ClusterConfig:
        """
        Get staging cluster configuration.

        Default settings:
        - machine_type: n2-standard-2 (smaller than prod)
        - min_nodes: 2
        - max_nodes: 5
        - spot_instances: True (cost savings)
        - disk_size: 75GB
        """
        defaults = {
            "project_id": self.project_id,
            "region": self.region,
            "env": self.env,
            "prefix": self.prefix,
            "machine_type": "n2-standard-2",
            "node_count": 2,
            "min_nodes": 2,
            "max_nodes": 5,
            "spot_instances": True,
            "disk_size": 75,
        }
        return ClusterConfig(**{**defaults, **overrides})

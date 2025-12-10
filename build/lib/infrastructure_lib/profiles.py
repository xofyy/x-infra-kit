from typing import List, Optional
from .config import ClusterConfig, NetworkConfig

class PlatformProfile:
    """
    Base class for Platform Profiles (Golden Paths).
    Enforces naming conventions and sizing policies.
    """
    def __init__(self, project_id: str, region: str, env: str, prefix: str = "app"):
        self.project_id = project_id
        self.region = region
        self.env = env
        self.prefix = prefix

    @property
    def common_labels(self):
        return {
            "environment": self.env,
            "managed-by": "cdktf",
            "project": self.project_id
        }

    def _get_name(self, resource: str) -> str:
        """Standard naming convention: {prefix}-{env}-{resource}"""
        return f"{self.prefix}-{self.env}-{resource}"

    def get_network_config(self, cidr: str = "10.0.0.0/16") -> NetworkConfig:
        return NetworkConfig(
            project_id=self.project_id,
            region=self.region,
            env=self.env,
            vpc_name=self._get_name("vpc"),
            subnet_name=self._get_name("subnet"),
            cidr=cidr,
            pod_range_name="pod-ranges",
            service_range_name="service-ranges"
        )

    def get_cluster_config(self) -> ClusterConfig:
        raise NotImplementedError("Subclasses must implement get_cluster_config")


class DevProfile(PlatformProfile):
    """
    Development Profile: Cost-optimized, relaxed availability.
    """
    def get_cluster_config(self) -> ClusterConfig:
        return ClusterConfig(
            project_id=self.project_id,
            region=self.region,
            zone=f"{self.region}-a", # Single zone for cost
            env=self.env,
            cluster_name=self._get_name("cluster"),
            workload_pool=f"{self.project_id}.svc.id.goog",
            
            # Smart Default: Low cost machine
            machine_type="e2-medium",
            node_count=1,
            min_nodes=1,
            max_nodes=3,
            spot_instances=True, # Use Spot for Dev
            disk_size=50
        )


class ProdProfile(PlatformProfile):
    """
    Production Profile: High Availability, Performance, Stability.
    """
    def get_cluster_config(self) -> ClusterConfig:
        return ClusterConfig(
            project_id=self.project_id,
            region=self.region,
            zone=f"{self.region}-a", # In real prod, might use regional cluster (no single zone)
            env=self.env,
            cluster_name=self._get_name("cluster"),
            workload_pool=f"{self.project_id}.svc.id.goog",
            
            # Smart Default: Production grade machine
            machine_type="n2-standard-4",
            node_count=3, # Start with HA
            min_nodes=3, # Never go below 3
            max_nodes=10,
            spot_instances=False, # No Spot for Master/Critical pools
            disk_size=100
        )

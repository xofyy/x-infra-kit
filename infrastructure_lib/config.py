from dataclasses import dataclass
from typing import Optional


@dataclass
class NetworkConfig:
    """
    Network configuration for VPC and Subnet.

    Required:
        project_id: GCP project ID
        region: GCP region
        env: Environment (dev, staging, prod)
        prefix: Resource naming prefix

    Optional:
        cidr: Primary subnet CIDR (default: 10.0.0.0/16)
        pod_cidr: Secondary range for pods (default: 10.11.0.0/21)
        service_cidr: Secondary range for services (default: 10.12.0.0/21)
        pod_range_name: Name for pod secondary range (default: pod-ranges)
        service_range_name: Name for service secondary range (default: service-ranges)
    """

    # REQUIRED
    project_id: str
    region: str
    env: str
    prefix: str

    # OPTIONAL (with smart defaults)
    cidr: str = "10.0.0.0/16"
    pod_cidr: str = "10.11.0.0/21"
    service_cidr: str = "10.12.0.0/21"
    pod_range_name: str = "pod-ranges"
    service_range_name: str = "service-ranges"

    # AUTO-GENERATED (computed properties)
    @property
    def vpc_name(self) -> str:
        """Standard naming: {prefix}-{env}-vpc"""
        return f"{self.prefix}-{self.env}-vpc"

    @property
    def subnet_name(self) -> str:
        """Standard naming: {prefix}-{env}-subnet"""
        return f"{self.prefix}-{self.env}-subnet"


@dataclass
class ClusterConfig:
    """
    GKE Cluster configuration.

    Required:
        project_id: GCP project ID
        region: GCP region
        env: Environment (dev, staging, prod)
        prefix: Resource naming prefix

    Optional:
        zone: GCP zone (default: {region}-a)
        machine_type: Node machine type (default: e2-medium)
        node_count: Initial node count (default: 1)
        min_nodes: Autoscaler minimum (default: 1)
        max_nodes: Autoscaler maximum (default: 3)
        disk_size: Node disk size in GB (default: 50)
        spot_instances: Use spot/preemptible VMs (default: True)
        master_cidr: Private cluster master CIDR (default: 172.16.0.0/28)
    """

    # REQUIRED
    project_id: str
    region: str
    env: str
    prefix: str

    # OPTIONAL (with smart defaults)
    zone: Optional[str] = None  # None = auto-calculated as {region}-a
    machine_type: str = "e2-medium"
    node_count: int = 1
    min_nodes: int = 1
    max_nodes: int = 3
    disk_size: int = 50
    spot_instances: bool = True
    master_cidr: str = "172.16.0.0/28"

    # Secondary range names (to pass to GKE)
    pod_range_name: str = "pod-ranges"
    service_range_name: str = "service-ranges"

    # AUTO-GENERATED (computed properties)
    @property
    def cluster_name(self) -> str:
        """Standard naming: {prefix}-{env}-cluster"""
        return f"{self.prefix}-{self.env}-cluster"

    @property
    def workload_pool(self) -> str:
        """Workload Identity pool: {project_id}.svc.id.goog"""
        return f"{self.project_id}.svc.id.goog"

    @property
    def effective_zone(self) -> str:
        """Returns zone if set, otherwise {region}-a"""
        return self.zone if self.zone else f"{self.region}-a"

    def __post_init__(self):
        """Validate configuration."""
        if self.min_nodes > self.max_nodes:
            raise ValueError(
                f"min_nodes ({self.min_nodes}) cannot be greater than max_nodes ({self.max_nodes})"
            )

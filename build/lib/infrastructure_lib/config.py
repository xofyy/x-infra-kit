from dataclasses import dataclass, field
from typing import List
@dataclass
class NetworkConfig:
    project_id: str
    region: str
    env: str
    # Generic naming fields
    vpc_name: str
    subnet_name: str
    cidr: str = "10.0.0.0/16"
    # Secondary ranges now have default names but can be overridden if needed
    pod_cidr: str = "10.11.0.0/21"
    service_cidr: str = "10.12.0.0/21"
    pod_range_name: str = "pod-ranges"
    service_range_name: str = "service-ranges"

@dataclass
class ClusterConfig:
    project_id: str
    region: str
    zone: str
    env: str
    cluster_name: str
    workload_pool: str
    
    # Defaults
    machine_type: str = "e2-medium"
    node_count: int = 1
    min_nodes: int = 1
    max_nodes: int = 3
    disk_size: int = 50
    spot_instances: bool = True
    master_cidr: str = "172.16.0.0/28"
    
    def __post_init__(self):
        # Validation allows overriding via a "strict_validation" flag if we wanted, 
        # but for now we just make it a soft check or remove purely project-specific logic.
        
        # Example: validation remains useful but should be generic
        if self.min_nodes > self.max_nodes:
             raise ValueError(f"min_nodes ({self.min_nodes}) cannot be greater than max_nodes ({self.max_nodes})")


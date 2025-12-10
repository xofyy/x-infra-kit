"""
Standard VPC networking construct with best practices.

Creates:
- Custom VPC (no auto-subnets)
- Subnet with secondary ranges for GKE pods/services
- Cloud Router + NAT for private node internet access
"""
from typing import Optional
from constructs import Construct
from cdktf_cdktf_provider_google.compute_network import ComputeNetwork
from cdktf_cdktf_provider_google.compute_subnetwork import (
    ComputeSubnetwork, 
    ComputeSubnetworkSecondaryIpRange
)
from cdktf_cdktf_provider_google.compute_router import ComputeRouter
from cdktf_cdktf_provider_google.compute_router_nat import ComputeRouterNat
from .config import NetworkConfig


class StandardVPC(Construct):
    """
    Standard VPC with production-ready networking.
    
    Creates a custom VPC with:
    - Single subnet with configurable CIDR
    - Secondary IP ranges for GKE pods and services
    - Cloud Router and NAT for private node egress
    
    Args:
        scope: CDK scope
        id: Construct ID
        config: NetworkConfig instance with all network settings
        labels: Optional resource labels for cost tracking
    
    Attributes:
        network: The ComputeNetwork resource
        subnet: The ComputeSubnetwork resource
        router: The ComputeRouter resource
        nat: The ComputeRouterNat resource
    
    Example:
        from infrastructure_lib import NetworkConfig, StandardVPC
        
        config = NetworkConfig(
            project_id="my-project",
            region="europe-west1",
            env="prod",
            prefix="myapp"
        )
        vpc = StandardVPC(self, "networking", config=config)
        
        # Access resources
        print(vpc.network.id)
        print(vpc.subnet.id)
    """
    
    def __init__(
        self, 
        scope: Construct, 
        id: str, 
        config: NetworkConfig,
        labels: Optional[dict[str, str]] = None
    ):
        super().__init__(scope, id)
        
        # Default labels
        resource_labels = {
            "environment": config.env,
            "managed-by": "cdktf",
        }
        if labels:
            resource_labels.update(labels)
        
        # VPC Network
        self.network = ComputeNetwork(self, "vpc",
            name=config.vpc_name,
            auto_create_subnetworks=False,
            description=f"Standard VPC for {config.prefix}-{config.env}"
        )

        # Subnet with secondary ranges for GKE
        self.subnet = ComputeSubnetwork(self, "subnet",
            name=config.subnet_name,
            region=config.region,
            network=self.network.id,
            ip_cidr_range=config.cidr,
            private_ip_google_access=True,  # Best practice: access Google APIs without public IP
            secondary_ip_range=[
                ComputeSubnetworkSecondaryIpRange(
                    range_name=config.pod_range_name, 
                    ip_cidr_range=config.pod_cidr
                ),
                ComputeSubnetworkSecondaryIpRange(
                    range_name=config.service_range_name, 
                    ip_cidr_range=config.service_cidr
                )
            ]
        )

        # Cloud Router (required for NAT)
        self.router = ComputeRouter(self, "router",
            name=f"{config.vpc_name}-router",
            region=config.region,
            network=self.network.id
        )

        # Cloud NAT (allows private nodes to access internet)
        self.nat = ComputeRouterNat(self, "nat",
            name=f"{config.vpc_name}-nat",
            router=self.router.name,
            region=config.region,
            nat_ip_allocate_option="AUTO_ONLY",
            source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES"
        )
    
    @property
    def network_id(self) -> str:
        """Get the VPC network ID."""
        return self.network.id
    
    @property
    def subnet_id(self) -> str:
        """Get the subnet ID."""
        return self.subnet.id

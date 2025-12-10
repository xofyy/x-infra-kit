from constructs import Construct
from cdktf_cdktf_provider_google.compute_network import ComputeNetwork
from cdktf_cdktf_provider_google.compute_subnetwork import ComputeSubnetwork, ComputeSubnetworkSecondaryIpRange
from cdktf_cdktf_provider_google.compute_router import ComputeRouter
from cdktf_cdktf_provider_google.compute_router_nat import ComputeRouterNat
from .config import NetworkConfig

class StandardVPC(Construct):
    def __init__(self, scope: Construct, id: str, config: NetworkConfig):
        super().__init__(scope, id)
        
        self.network = ComputeNetwork(self, "vpc",
            name=config.vpc_name,
            auto_create_subnetworks=False,
            description="Standard VPC"
        )

        self.subnet = ComputeSubnetwork(self, "subnet",
            name=config.subnet_name,
            region=config.region,
            network=self.network.id,
            ip_cidr_range=config.cidr,
            secondary_ip_range=[
                ComputeSubnetworkSecondaryIpRange(range_name=config.pod_range_name, ip_cidr_range=config.pod_cidr),
                ComputeSubnetworkSecondaryIpRange(range_name=config.service_range_name, ip_cidr_range=config.service_cidr)
            ]
        )

        # Cloud NAT (Standard Pattern: Private Nodes need Internet)
        router = ComputeRouter(self, "router",
            name=f"{config.vpc_name}-router",
            region=config.region,
            network=self.network.id
        )

        ComputeRouterNat(self, "nat",
            name=f"{config.vpc_name}-nat",
            router=router.name,
            region=config.region,
            nat_ip_allocate_option="AUTO_ONLY",
            source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES"
        )

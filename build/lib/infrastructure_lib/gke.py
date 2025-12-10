from constructs import Construct
from cdktf_cdktf_provider_google.container_cluster import (
    ContainerCluster,
    ContainerClusterIpAllocationPolicy,
    ContainerClusterPrivateClusterConfig,
    ContainerClusterWorkloadIdentityConfig
)
from cdktf_cdktf_provider_google.container_node_pool import (
    ContainerNodePool,
    ContainerNodePoolAutoscaling,
    ContainerNodePoolNodeConfig
)
from .config import ClusterConfig

class StandardCluster(Construct):
    def __init__(self, scope: Construct, id: str, config: ClusterConfig, network_id: str, subnet_id: str):
        super().__init__(scope, id)

        self.cluster = ContainerCluster(self, "cluster",
            name=config.cluster_name,
            location=config.zone,
            network=network_id,
            subnetwork=subnet_id,
            remove_default_node_pool=True,
            initial_node_count=1,
            deletion_protection=True if config.env == "prod" else False,
            
            # Standard: VPC-Native
            ip_allocation_policy=ContainerClusterIpAllocationPolicy(
                cluster_secondary_range_name="pod-ranges",
                services_secondary_range_name="service-ranges"
            ),

            # Standard: Private Cluster
            private_cluster_config=ContainerClusterPrivateClusterConfig(
                enable_private_nodes=True,
                enable_private_endpoint=False,
                master_ipv4_cidr_block=config.master_cidr
            ),

            # Standard: Workload Identity
            workload_identity_config=ContainerClusterWorkloadIdentityConfig(
                workload_pool=config.workload_pool
            )
        )

        # Default Node Pool
        ContainerNodePool(self, "default_pool",
            name=f"{config.cluster_name}-pool",
            location=config.zone,
            cluster=self.cluster.name,
            initial_node_count=config.node_count,
            
            autoscaling=ContainerNodePoolAutoscaling(
                min_node_count=config.min_nodes,
                max_node_count=config.max_nodes,
                location_policy="ANY"
            ),

            node_config=ContainerNodePoolNodeConfig(
                machine_type=config.machine_type,
                disk_size_gb=config.disk_size,
                disk_type="pd-standard",
                spot=config.spot_instances,
                tags=["gke-node", f"{config.cluster_name}-gke"],
                oauth_scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
        )

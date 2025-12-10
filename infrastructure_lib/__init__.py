"""
x-infra-kit: Reusable CDKTF Infrastructure Library for GCP

This library provides production-ready infrastructure constructs for Google Cloud Platform.

Quick Start:
    from x_infra_kit import StandardPlatform
    
    platform = StandardPlatform(stack, "platform",
        project_id="my-project",
        region="europe-west1",
        env="prod",
        prefix="myapp"
    )

Building Blocks (for advanced usage):
    from x_infra_kit import StandardVPC, StandardCluster, DevProfile
    
    profile = DevProfile(project_id, region, env, prefix)
    vpc = StandardVPC(self, "vpc", config=profile.get_network_config())
    cluster = StandardCluster(self, "gke", config=profile.get_cluster_config(), ...)
"""

# Composite (Recommended for most users)
from .composites import StandardPlatform

# Building Blocks
from .networking import StandardVPC
from .gke import StandardCluster
from .security import StandardSecrets, StandardIdentity

# Configuration
from .config import NetworkConfig, ClusterConfig

# Profiles (Golden Paths)
from .profiles import PlatformProfile, DevProfile, StagingProfile, ProdProfile

__all__ = [
    # Composite
    "StandardPlatform",
    # Building Blocks
    "StandardVPC",
    "StandardCluster", 
    "StandardSecrets",
    "StandardIdentity",
    # Config
    "NetworkConfig",
    "ClusterConfig",
    # Profiles
    "PlatformProfile",
    "DevProfile",
    "StagingProfile",
    "ProdProfile",
]

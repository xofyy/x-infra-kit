#!/usr/bin/env python
"""
Example usage of x-infra-kit library.

This file demonstrates how to use the infrastructure library in a real project.
It can be used as a template for new projects.
"""
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, GcsBackend
from cdktf_cdktf_provider_google.provider import GoogleProvider

# Option 1: Use StandardPlatform for quick setup
from infrastructure_lib import StandardPlatform

# Option 2: Use building blocks for more control
# from infrastructure_lib import (
#     StandardVPC, StandardCluster, StandardSecrets, StandardIdentity,
#     DevProfile, ProdProfile
# )


class DeliveryStack(TerraformStack):
    """Example stack using x-infra-kit."""
    
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # --- Load Configuration from Environment ---
        import os
        from dotenv import load_dotenv
        load_dotenv()

        project_id = os.getenv("GCP_PROJECT_ID", "my-gcp-project")
        region = os.getenv("GCP_REGION", "us-central1")
        env = os.getenv("ENV", "dev")
        prefix = os.getenv("PREFIX", "delivery")
        
        # --- Provider ---
        GoogleProvider(self, "Google",
            project=project_id,
            region=region
        )

        # --- Remote Backend (Optional) ---
        state_bucket = os.getenv("STATE_BUCKET")
        if state_bucket:
            GcsBackend(self,
                bucket=state_bucket,
                prefix=f"cdktf/{env}"
            )

        # --- Option 1: Quick Setup with StandardPlatform ---
        platform = StandardPlatform(self, "platform",
            project_id=project_id,
            region=region,
            env=env,
            prefix=prefix,
            # Optional: Secrets
            secret_ids=[
                "postgres-password",
                "rabbitmq-password",
                "jwt-secret"
            ],
            # Optional: Workload Identity
            workload_identity={
                "sa_id": "external-secrets-sa",
                "k8s_namespace": "external-secrets",
                "k8s_sa_name": "external-secrets",
                "roles": ["roles/secretmanager.secretAccessor"]
            }
        )

        # --- Outputs ---
        TerraformOutput(self, "cluster_name", 
            value=platform.cluster.cluster.name
        )
        TerraformOutput(self, "cluster_endpoint", 
            value=platform.cluster.cluster.endpoint
        )
        TerraformOutput(self, "vpc_name",
            value=platform.vpc.network.name
        )


# --- Alternative: Building Blocks Approach ---
# class CustomStack(TerraformStack):
#     def __init__(self, scope, id):
#         super().__init__(scope, id)
#         
#         from infrastructure_lib import DevProfile, StandardVPC, StandardCluster
#         
#         profile = DevProfile("my-project", "us-central1", "dev", "myapp")
#         
#         vpc = StandardVPC(self, "vpc", 
#             config=profile.get_network_config(cidr="10.1.0.0/16")  # Custom CIDR
#         )
#         
#         cluster = StandardCluster(self, "gke",
#             config=profile.get_cluster_config(max_nodes=10),  # Override max_nodes
#             network_id=vpc.network.id,
#             subnet_id=vpc.subnet.id
#         )


app = App()
DeliveryStack(app, "x-infra-kit")
app.synth()

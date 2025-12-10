"""
Composite constructs for single-line platform creation.

These constructs bundle multiple resources together for simplified usage,
following the "Golden Path" pattern.
"""

from typing import Optional

from constructs import Construct

from .gke import StandardCluster
from .networking import StandardVPC
from .profiles import DevProfile, ProdProfile, StagingProfile
from .security import StandardIdentity, StandardSecrets


class StandardPlatform(Construct):
    """
    Complete platform infrastructure in a single construct.

    Creates: VPC + Subnet + NAT + GKE Cluster + (optional) Secrets + (optional) Workload Identity

    This is the recommended way to use x-infra-kit for most use cases.

    Args:
        scope: CDK scope
        id: Construct ID
        project_id: GCP project ID (required)
        region: GCP region (required)
        env: Environment - dev, staging, or prod (required)
        prefix: Resource naming prefix (required)
        secret_ids: List of secret IDs to create in Secret Manager
        workload_identity: Dict with {sa_id, k8s_namespace, k8s_sa_name, roles}
        **cluster_overrides: Override any ClusterConfig parameter

    Attributes:
        vpc: StandardVPC instance
        cluster: StandardCluster instance
        secrets: StandardSecrets instance (if secret_ids provided)
        identity: StandardIdentity instance (if workload_identity provided)

    Example:
        # Minimal usage
        platform = StandardPlatform(stack, "platform",
            project_id="my-project",
            region="europe-west1",
            env="dev",
            prefix="myapp"
        )

        # Full usage with all options
        platform = StandardPlatform(stack, "platform",
            project_id="my-project",
            region="europe-west1",
            env="prod",
            prefix="myapp",
            secret_ids=["db-password", "api-key"],
            workload_identity={
                "sa_id": "workload-sa",
                "k8s_namespace": "default",
                "k8s_sa_name": "app-sa",
                "roles": ["roles/secretmanager.secretAccessor"]
            },
            max_nodes=20,
            machine_type="n2-standard-8"
        )
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        # REQUIRED
        project_id: str,
        region: str,
        env: str,
        prefix: str,
        # OPTIONAL
        secret_ids: Optional[list[str]] = None,
        workload_identity: Optional[dict] = None,
        **cluster_overrides,
    ):
        super().__init__(scope, id)

        # Store for reference
        self.project_id = project_id
        self.region = region
        self.env = env
        self.prefix = prefix

        # 1. Select profile based on environment
        if env == "prod":
            profile = ProdProfile(project_id, region, env, prefix)
        elif env == "staging":
            profile = StagingProfile(project_id, region, env, prefix)
        else:
            profile = DevProfile(project_id, region, env, prefix)

        # 2. Create VPC and Networking
        network_config = profile.get_network_config()
        self.vpc = StandardVPC(self, "networking", config=network_config)

        # 3. Create GKE Cluster (with optional overrides)
        cluster_config = profile.get_cluster_config(
            pod_range_name=network_config.pod_range_name,
            service_range_name=network_config.service_range_name,
            **cluster_overrides,
        )
        self.cluster = StandardCluster(
            self,
            "compute",
            config=cluster_config,
            network_id=self.vpc.network.id,
            subnet_id=self.vpc.subnet.id,
        )

        # 4. Create Secrets (optional)
        self._secrets = None
        if secret_ids:
            self._secrets = StandardSecrets(self, "secrets", secret_ids=secret_ids)

        # 5. Create Workload Identity (optional)
        self._identity = None
        if workload_identity:
            self._identity = StandardIdentity(
                self,
                "identity",
                project_id=project_id,
                sa_id=workload_identity.get("sa_id"),
                k8s_namespace=workload_identity.get("k8s_namespace"),
                k8s_sa_name=workload_identity.get("k8s_sa_name"),
                roles=workload_identity.get("roles", []),
            )

    # --- Safe Access Properties ---

    @property
    def has_secrets(self) -> bool:
        """Check if secrets were configured."""
        return self._secrets is not None

    @property
    def has_identity(self) -> bool:
        """Check if workload identity was configured."""
        return self._identity is not None

    @property
    def secrets(self) -> StandardSecrets:
        """
        Get the StandardSecrets instance.

        Raises:
            ValueError: If secrets were not configured (secret_ids not provided)
        """
        if self._secrets is None:
            raise ValueError(
                "Secrets not configured. Provide 'secret_ids' parameter to StandardPlatform."
            )
        return self._secrets

    @property
    def identity(self) -> StandardIdentity:
        """
        Get the StandardIdentity instance.

        Raises:
            ValueError: If workload identity was not configured
        """
        if self._identity is None:
            raise ValueError(
                "Workload Identity not configured. Provide 'workload_identity' parameter to StandardPlatform."
            )
        return self._identity

    # --- Convenience Properties ---

    @property
    def cluster_name(self) -> str:
        """Get the GKE cluster name."""
        return self.cluster.cluster.name

    @property
    def cluster_endpoint(self) -> str:
        """Get the GKE cluster endpoint (API server URL)."""
        return self.cluster.cluster.endpoint

    @property
    def network_id(self) -> str:
        """Get the VPC network ID."""
        return self.vpc.network.id

    @property
    def subnet_id(self) -> str:
        """Get the subnet ID."""
        return self.vpc.subnet.id

    @property
    def identity_email(self) -> str:
        """
        Get the workload identity service account email.

        Raises:
            ValueError: If workload identity was not configured
        """
        return self.identity.email

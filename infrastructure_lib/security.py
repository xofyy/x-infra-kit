"""
Security constructs for Secret Manager and Workload Identity.

Provides:
- StandardSecrets: Creates Secret Manager secrets with auto-replication
- StandardIdentity: Sets up Workload Identity (GCP SA + K8s SA binding)
"""
from typing import Optional
from constructs import Construct
from cdktf_cdktf_provider_google.secret_manager_secret import (
    SecretManagerSecret,
    SecretManagerSecretReplication,
    SecretManagerSecretReplicationAuto
)
from cdktf_cdktf_provider_google.service_account import ServiceAccount
from cdktf_cdktf_provider_google.project_iam_member import ProjectIamMember
from cdktf_cdktf_provider_google.service_account_iam_binding import ServiceAccountIamBinding


class StandardSecrets(Construct):
    """
    Creates Secret Manager secrets with automatic replication.
    
    Note: This creates the secret containers only, not the secret values.
    Secret values should be added manually or via CI/CD.
    
    Args:
        scope: CDK scope
        id: Construct ID
        secret_ids: List of secret IDs to create
    
    Attributes:
        secret_ids: List of created secret IDs
    
    Example:
        secrets = StandardSecrets(self, "secrets",
            secret_ids=["db-password", "api-key", "jwt-secret"]
        )
    """
    
    def __init__(self, scope: Construct, id: str, secret_ids: list[str]):
        super().__init__(scope, id)
        
        if not secret_ids:
            raise ValueError("secret_ids cannot be empty")
        
        self.secret_ids = secret_ids
        self._secrets: dict[str, SecretManagerSecret] = {}
        
        for secret_id in secret_ids:
            if not secret_id or not secret_id.strip():
                raise ValueError("secret_id cannot be empty or whitespace")
            
            secret = SecretManagerSecret(self, f"secret-{secret_id}",
                secret_id=secret_id,
                replication=SecretManagerSecretReplication(
                    auto=SecretManagerSecretReplicationAuto()
                )
            )
            self._secrets[secret_id] = secret
    
    def get_secret(self, secret_id: str) -> SecretManagerSecret:
        """Get a specific secret by ID."""
        if secret_id not in self._secrets:
            raise KeyError(f"Secret '{secret_id}' not found. Available: {list(self._secrets.keys())}")
        return self._secrets[secret_id]


class StandardIdentity(Construct):
    """
    Sets up Workload Identity for Kubernetes-to-GCP authentication.
    
    Creates:
    1. Google Service Account (GSA)
    2. IAM role bindings for the GSA
    3. Workload Identity binding (K8s SA → GSA)
    
    Args:
        scope: CDK scope
        id: Construct ID
        project_id: GCP project ID
        sa_id: Service account ID (6-30 chars, lowercase, hyphens allowed)
        k8s_namespace: Kubernetes namespace where the SA exists
        k8s_sa_name: Kubernetes ServiceAccount name
        roles: Optional list of IAM roles to grant (e.g., ["roles/secretmanager.secretAccessor"])
    
    Attributes:
        gsa: The created Google Service Account
        email: The service account email address
    
    Example:
        identity = StandardIdentity(self, "workload-identity",
            project_id="my-project",
            sa_id="external-secrets-sa",
            k8s_namespace="external-secrets",
            k8s_sa_name="external-secrets",
            roles=["roles/secretmanager.secretAccessor"]
        )
        print(identity.email)  # external-secrets-sa@my-project.iam.gserviceaccount.com
    """
    
    def __init__(
        self, 
        scope: Construct, 
        id: str, 
        project_id: str, 
        sa_id: str, 
        k8s_namespace: str, 
        k8s_sa_name: str, 
        roles: Optional[list[str]] = None
    ):
        super().__init__(scope, id)
        
        # Validation
        if not project_id:
            raise ValueError("project_id is required")
        if not sa_id or len(sa_id) < 6 or len(sa_id) > 30:
            raise ValueError("sa_id must be 6-30 characters")
        if not k8s_namespace:
            raise ValueError("k8s_namespace is required")
        if not k8s_sa_name:
            raise ValueError("k8s_sa_name is required")
        
        # 1. Create Google Service Account (GSA)
        self.gsa = ServiceAccount(self, "sa",
            account_id=sa_id,
            display_name=f"Workload Identity SA for {sa_id}"
        )

        # 2. Grant GSA Access to specified roles
        self._role_bindings: list[ProjectIamMember] = []
        if roles:
            for idx, role in enumerate(roles):
                binding = ProjectIamMember(self, f"role_binding_{idx}",
                    project=project_id,
                    role=role,
                    member=f"serviceAccount:{self.gsa.email}"
                )
                self._role_bindings.append(binding)

        # 3. Bind K8s SA to GSA (Workload Identity)
        self.workload_identity_binding = ServiceAccountIamBinding(self, "workload_identity_user",
            service_account_id=self.gsa.name,
            role="roles/iam.workloadIdentityUser",
            members=[
                f"serviceAccount:{project_id}.svc.id.goog[{k8s_namespace}/{k8s_sa_name}]"
            ]
        )
    
    @property
    def email(self) -> str:
        """Get the service account email address."""
        return self.gsa.email

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
    def __init__(self, scope: Construct, id: str, secret_ids: list[str]):
        super().__init__(scope, id)
        
        for secret_id in secret_ids:
            SecretManagerSecret(self, f"secret-{secret_id}",
                secret_id=secret_id,
                replication=SecretManagerSecretReplication(
                    auto=SecretManagerSecretReplicationAuto()
                )
            )

class StandardIdentity(Construct):
    def __init__(self, scope: Construct, id: str, project_id: str, sa_id: str, k8s_namespace: str, k8s_sa_name: str, roles: list[str] = None):
        super().__init__(scope, id)
        
        # 1. Create Google Service Account (GSA)
        self.gsa = ServiceAccount(self, "sa",
            account_id=sa_id,
            display_name=f"Workload Identity SA for {sa_id}"
        )

        # 2. Grant GSA Access to Secrets (or any other roles passed in)
        if roles:
            for idx, role in enumerate(roles):
                ProjectIamMember(self, f"role_binding_{idx}",
                    project=project_id,
                    role=role,
                    member=f"serviceAccount:{self.gsa.email}"
                )

        # 3. Bind K8s SA to GSA (Workload Identity)
        ServiceAccountIamBinding(self, "workload_identity_user",
            service_account_id=self.gsa.name,
            role="roles/iam.workloadIdentityUser",
            members=[
                f"serviceAccount:{project_id}.svc.id.goog[{k8s_namespace}/{k8s_sa_name}]"
            ]
        )

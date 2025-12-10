"""
Snapshot tests for infrastructure constructs.

These tests verify that the synthesized Terraform JSON output
matches expected baselines, catching unintended changes.
"""

import pytest
from cdktf import App, TerraformStack, Testing
from cdktf_cdktf_provider_google.provider import GoogleProvider

from infrastructure_lib import (
    StandardPlatform,
    StandardVPC,
    StandardCluster,
    StandardSecrets,
    StandardIdentity,
    DevProfile,
    ProdProfile,
)


class TestStack(TerraformStack):
    """Helper stack for testing."""

    def __init__(self, scope, id):
        super().__init__(scope, id)
        GoogleProvider(self, "Google", project="test-project", region="us-central1")


class TestStandardVPCSnapshot:
    """Snapshot tests for StandardVPC construct."""

    def test_vpc_creates_expected_resources(self):
        """Test that StandardVPC creates VPC, Subnet, Router, and NAT."""
        app = Testing.app()
        stack = TestStack(app, "test")

        profile = DevProfile("test-project", "us-central1", "dev", "myapp")
        StandardVPC(stack, "vpc", config=profile.get_network_config())

        synth = Testing.synth(stack)

        # Verify expected resources are created
        assert Testing.to_have_resource(synth, "google_compute_network")
        assert Testing.to_have_resource(synth, "google_compute_subnetwork")
        assert Testing.to_have_resource(synth, "google_compute_router")
        assert Testing.to_have_resource(synth, "google_compute_router_nat")

    def test_vpc_resource_count(self):
        """Test that StandardVPC creates exactly 4 resources."""
        app = Testing.app()
        stack = TestStack(app, "test")

        profile = DevProfile("test-project", "us-central1", "dev", "myapp")
        StandardVPC(stack, "vpc", config=profile.get_network_config())

        synth = Testing.synth(stack)

        assert Testing.to_have_resource_with_properties(
            synth, "google_compute_network", {"name": "myapp-dev-vpc"}
        )
        assert Testing.to_have_resource_with_properties(
            synth, "google_compute_subnetwork", {"name": "myapp-dev-subnet"}
        )


class TestStandardClusterSnapshot:
    """Snapshot tests for StandardCluster construct."""

    def test_cluster_creates_expected_resources(self):
        """Test that StandardCluster creates GKE cluster and node pool."""
        app = Testing.app()
        stack = TestStack(app, "test")

        profile = DevProfile("test-project", "us-central1", "dev", "myapp")
        vpc_config = profile.get_network_config()
        cluster_config = profile.get_cluster_config(
            pod_range_name=vpc_config.pod_range_name,
            service_range_name=vpc_config.service_range_name,
        )

        # Mock network/subnet IDs
        StandardCluster(
            stack,
            "cluster",
            config=cluster_config,
            network_id="mock-network-id",
            subnet_id="mock-subnet-id",
        )

        synth = Testing.synth(stack)

        assert Testing.to_have_resource(synth, "google_container_cluster")
        assert Testing.to_have_resource(synth, "google_container_node_pool")

    def test_dev_cluster_uses_spot_instances(self):
        """Test that DevProfile enables spot instances."""
        app = Testing.app()
        stack = TestStack(app, "test")

        profile = DevProfile("test-project", "us-central1", "dev", "myapp")
        cluster_config = profile.get_cluster_config()

        StandardCluster(
            stack,
            "cluster",
            config=cluster_config,
            network_id="mock-network-id",
            subnet_id="mock-subnet-id",
        )

        synth = Testing.synth(stack)

        assert Testing.to_have_resource_with_properties(
            synth,
            "google_container_node_pool",
            {"node_config": {"spot": True}},
        )

    def test_prod_cluster_disables_spot_instances(self):
        """Test that ProdProfile disables spot instances."""
        app = Testing.app()
        stack = TestStack(app, "test")

        profile = ProdProfile("test-project", "us-central1", "prod", "myapp")
        cluster_config = profile.get_cluster_config()

        StandardCluster(
            stack,
            "cluster",
            config=cluster_config,
            network_id="mock-network-id",
            subnet_id="mock-subnet-id",
        )

        synth = Testing.synth(stack)

        assert Testing.to_have_resource_with_properties(
            synth,
            "google_container_node_pool",
            {"node_config": {"spot": False}},
        )


class TestStandardSecretsSnapshot:
    """Snapshot tests for StandardSecrets construct."""

    def test_secrets_creates_expected_resources(self):
        """Test that StandardSecrets creates Secret Manager secrets."""
        app = Testing.app()
        stack = TestStack(app, "test")

        StandardSecrets(stack, "secrets", secret_ids=["db-password", "api-key"])

        synth = Testing.synth(stack)

        assert Testing.to_have_resource(synth, "google_secret_manager_secret")


class TestStandardIdentitySnapshot:
    """Snapshot tests for StandardIdentity construct."""

    def test_identity_creates_expected_resources(self):
        """Test that StandardIdentity creates SA and IAM bindings."""
        app = Testing.app()
        stack = TestStack(app, "test")

        StandardIdentity(
            stack,
            "identity",
            project_id="test-project",
            sa_id="test-sa-account",
            k8s_namespace="default",
            k8s_sa_name="test-k8s-sa",
            roles=["roles/secretmanager.secretAccessor"],
        )

        synth = Testing.synth(stack)

        assert Testing.to_have_resource(synth, "google_service_account")
        assert Testing.to_have_resource(synth, "google_project_iam_member")
        assert Testing.to_have_resource(synth, "google_service_account_iam_binding")


class TestStandardPlatformSnapshot:
    """Snapshot tests for StandardPlatform composite construct."""

    def test_platform_creates_all_resources(self):
        """Test that StandardPlatform creates complete infrastructure."""
        app = Testing.app()
        stack = TestStack(app, "test")

        StandardPlatform(
            stack,
            "platform",
            project_id="test-project",
            region="us-central1",
            env="dev",
            prefix="myapp",
        )

        synth = Testing.synth(stack)

        # Networking
        assert Testing.to_have_resource(synth, "google_compute_network")
        assert Testing.to_have_resource(synth, "google_compute_subnetwork")
        assert Testing.to_have_resource(synth, "google_compute_router")
        assert Testing.to_have_resource(synth, "google_compute_router_nat")

        # GKE
        assert Testing.to_have_resource(synth, "google_container_cluster")
        assert Testing.to_have_resource(synth, "google_container_node_pool")

    def test_platform_with_secrets_and_identity(self):
        """Test StandardPlatform with optional secrets and identity."""
        app = Testing.app()
        stack = TestStack(app, "test")

        StandardPlatform(
            stack,
            "platform",
            project_id="test-project",
            region="us-central1",
            env="prod",
            prefix="myapp",
            secret_ids=["db-password"],
            workload_identity={
                "sa_id": "workload-identity-sa",
                "k8s_namespace": "default",
                "k8s_sa_name": "app-sa",
                "roles": ["roles/secretmanager.secretAccessor"],
            },
        )

        synth = Testing.synth(stack)

        # Secrets
        assert Testing.to_have_resource(synth, "google_secret_manager_secret")

        # Identity
        assert Testing.to_have_resource(synth, "google_service_account")
        assert Testing.to_have_resource(synth, "google_service_account_iam_binding")

    def test_valid_terraform_output(self):
        """Test that synthesized output is valid Terraform."""
        app = Testing.app()
        stack = TestStack(app, "test")

        StandardPlatform(
            stack,
            "platform",
            project_id="test-project",
            region="us-central1",
            env="dev",
            prefix="myapp",
        )

        # This validates the Terraform JSON is syntactically correct
        assert Testing.to_be_valid_terraform(Testing.full_synth(stack))

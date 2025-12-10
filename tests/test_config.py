"""
Tests for configuration validation and property generation.
"""

import pytest
from infrastructure_lib.config import ClusterConfig, NetworkConfig


class TestNetworkConfig:
    """Tests for NetworkConfig dataclass."""

    def test_required_fields(self):
        """Test that required fields must be provided."""
        with pytest.raises(TypeError):
            NetworkConfig()  # Missing required fields

    def test_auto_generated_names(self):
        """Test that vpc_name and subnet_name are auto-generated."""
        config = NetworkConfig(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        assert config.vpc_name == "myapp-dev-vpc"
        assert config.subnet_name == "myapp-dev-subnet"

    def test_default_values(self):
        """Test that optional fields have sensible defaults."""
        config = NetworkConfig(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        assert config.cidr == "10.0.0.0/16"
        assert config.pod_cidr == "10.11.0.0/21"
        assert config.service_cidr == "10.12.0.0/21"
        assert config.pod_range_name == "pod-ranges"
        assert config.service_range_name == "service-ranges"

    def test_override_defaults(self):
        """Test that defaults can be overridden."""
        config = NetworkConfig(
            project_id="test-project",
            region="us-central1",
            env="dev",
            prefix="myapp",
            cidr="10.1.0.0/16",
        )
        assert config.cidr == "10.1.0.0/16"


class TestClusterConfig:
    """Tests for ClusterConfig dataclass."""

    def test_required_fields(self):
        """Test that required fields must be provided."""
        with pytest.raises(TypeError):
            ClusterConfig()  # Missing required fields

    def test_auto_generated_properties(self):
        """Test that cluster_name and workload_pool are auto-generated."""
        config = ClusterConfig(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        assert config.cluster_name == "myapp-dev-cluster"
        assert config.workload_pool == "test-project.svc.id.goog"

    def test_effective_zone_default(self):
        """Test that zone defaults to {region}-a."""
        config = ClusterConfig(
            project_id="test-project", region="europe-west1", env="dev", prefix="myapp"
        )
        assert config.effective_zone == "europe-west1-a"

    def test_effective_zone_custom(self):
        """Test that custom zone is used when provided."""
        config = ClusterConfig(
            project_id="test-project",
            region="europe-west1",
            env="dev",
            prefix="myapp",
            zone="europe-west1-c",
        )
        assert config.effective_zone == "europe-west1-c"

    def test_validation_min_max_nodes(self):
        """Test that min_nodes > max_nodes raises error."""
        with pytest.raises(ValueError) as excinfo:
            ClusterConfig(
                project_id="test-project",
                region="us-central1",
                env="dev",
                prefix="myapp",
                min_nodes=5,
                max_nodes=3,
            )
        assert "min_nodes" in str(excinfo.value)
        assert "max_nodes" in str(excinfo.value)

    def test_default_values(self):
        """Test that optional fields have sensible defaults."""
        config = ClusterConfig(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        assert config.machine_type == "e2-medium"
        assert config.node_count == 1
        assert config.min_nodes == 1
        assert config.max_nodes == 3
        assert config.disk_size == 50
        assert config.spot_instances is True
        assert config.master_cidr == "172.16.0.0/28"


class TestProfileIntegration:
    """Tests for profile configuration generation."""

    def test_dev_profile_config(self):
        """Test DevProfile generates correct config."""
        from infrastructure_lib.profiles import DevProfile

        profile = DevProfile(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        config = profile.get_cluster_config()

        assert config.cluster_name == "myapp-dev-cluster"
        assert config.machine_type == "e2-medium"
        assert config.spot_instances is True

    def test_prod_profile_config(self):
        """Test ProdProfile generates correct config."""
        from infrastructure_lib.profiles import ProdProfile

        profile = ProdProfile(
            project_id="test-project", region="us-central1", env="prod", prefix="myapp"
        )
        config = profile.get_cluster_config()

        assert config.cluster_name == "myapp-prod-cluster"
        assert config.machine_type == "n2-standard-4"
        assert config.spot_instances is False
        assert config.min_nodes == 3

    def test_profile_override(self):
        """Test that profile defaults can be overridden."""
        from infrastructure_lib.profiles import DevProfile

        profile = DevProfile(
            project_id="test-project", region="us-central1", env="dev", prefix="myapp"
        )
        config = profile.get_cluster_config(machine_type="e2-standard-4", max_nodes=10)

        assert config.machine_type == "e2-standard-4"
        assert config.max_nodes == 10

# 🏗️ x-infra-kit

**Reusable CDKTF Infrastructure Library for Google Cloud Platform**

Production-ready infrastructure constructs that enable you to deploy GCP resources with a single line of code.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CDKTF](https://img.shields.io/badge/cdktf-0.20+-green.svg)](https://developer.hashicorp.com/terraform/cdktf)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [StandardPlatform (Recommended)](#standardplatform-recommended)
  - [Building Blocks (Advanced)](#building-blocks-advanced)
- [Configuration](#-configuration)
  - [Required Parameters](#required-parameters)
  - [Optional Parameters](#optional-parameters)
  - [Environment Profiles](#environment-profiles)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Testing](#-testing)
- [Contributing](#-contributing)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Single-Line Deployment** | Deploy complete GCP infrastructure with `StandardPlatform` |
| **Golden Path Profiles** | Pre-configured Dev, Staging, and Prod environments |
| **Override Support** | Customize any parameter while keeping sensible defaults |
| **Type Safety** | Full type hints and dataclass validation |
| **Best Practices** | Private clusters, Workload Identity, VPC-native networking |
| **Modular Design** | Use composite or individual building blocks |

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     StandardPlatform                        │
│  (Composite Construct - Recommended for most users)        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Profile   │  │   Profile   │  │      Profile        │ │
│  │  DevProfile │  │StagingProfile│ │    ProdProfile      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         └────────────────┴─────────────────────┘            │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              NetworkConfig / ClusterConfig           │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│         ┌────────────────┼────────────────┐                │
│         ▼                ▼                ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ StandardVPC │  │StandardCluster│ │StandardSecrets│      │
│  │             │  │             │  │(optional)    │        │
│  │ • VPC       │  │ • GKE       │  │             │        │
│  │ • Subnet    │  │ • Node Pool │  ├─────────────┤        │
│  │ • Router    │  │             │  │StandardIdentity│      │
│  │ • NAT       │  │             │  │(optional)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### GCP Resources Created

| Resource | Description |
|----------|-------------|
| `google_compute_network` | Custom VPC |
| `google_compute_subnetwork` | Subnet with secondary ranges |
| `google_compute_router` | Cloud Router for NAT |
| `google_compute_router_nat` | Cloud NAT for private egress |
| `google_container_cluster` | Private GKE cluster |
| `google_container_node_pool` | Managed node pool with autoscaling |
| `google_secret_manager_secret` | Secret Manager secrets (optional) |
| `google_service_account` | Workload Identity SA (optional) |
| `google_project_iam_member` | IAM role bindings (optional) |
| `google_service_account_iam_binding` | Workload Identity binding (optional) |

---

## 🚀 Quick Start

### 1. Install the library

```bash
pip install -e .
# or
pip install x-infra-kit  # when published to PyPI
```

### 2. Create your stack

```python
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_google.provider import GoogleProvider
from infrastructure_lib import StandardPlatform

class MyStack(TerraformStack):
    def __init__(self, scope, id):
        super().__init__(scope, id)
        
        GoogleProvider(self, "Google", 
            project="my-gcp-project", 
            region="europe-west1"
        )
        
        # 🚀 One line to create complete infrastructure!
        platform = StandardPlatform(self, "platform",
            project_id="my-gcp-project",
            region="europe-west1",
            env="prod",
            prefix="myapp"
        )

app = App()
MyStack(app, "my-stack")
app.synth()
```

### 3. Deploy

```bash
cdktf synth    # Generate Terraform JSON
cdktf deploy   # Apply to GCP
```

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- Node.js 16+ (for cdktf-cli)
- Google Cloud SDK (`gcloud`)
- Terraform 1.0+ (installed automatically by cdktf)

### Install from source

```bash
git clone https://github.com/your-org/x-infra-kit.git
cd x-infra-kit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### Install as package

```bash
pip install -e .
```

---

## 📖 Usage

### StandardPlatform (Recommended)

The easiest way to use the library. Creates VPC, GKE, and optionally Secrets and Workload Identity.

```python
from infrastructure_lib import StandardPlatform

# Minimal usage (just 4 required parameters)
platform = StandardPlatform(stack, "platform",
    project_id="my-gcp-project",
    region="europe-west1",
    env="dev",
    prefix="myapp"
)

# Access created resources
print(platform.cluster_name)      # myapp-dev-cluster
print(platform.cluster_endpoint)  # https://...
print(platform.network_id)        # projects/.../networks/myapp-dev-vpc
print(platform.subnet_id)         # projects/.../subnetworks/myapp-dev-subnet
```

#### With Secrets and Workload Identity

```python
platform = StandardPlatform(stack, "platform",
    project_id="my-gcp-project",
    region="europe-west1",
    env="prod",
    prefix="myapp",
    
    # Optional: Create secrets
    secret_ids=["db-password", "api-key", "jwt-secret"],
    
    # Optional: Setup Workload Identity
    workload_identity={
        "sa_id": "external-secrets-sa",
        "k8s_namespace": "external-secrets",
        "k8s_sa_name": "external-secrets",
        "roles": ["roles/secretmanager.secretAccessor"]
    }
)

# Access optional resources (check first!)
if platform.has_secrets:
    print(platform.secrets.secret_ids)

if platform.has_identity:
    print(platform.identity_email)
```

#### With Cluster Overrides

```python
platform = StandardPlatform(stack, "platform",
    project_id="my-gcp-project",
    region="europe-west1",
    env="prod",
    prefix="myapp",
    
    # Override any cluster setting
    machine_type="n2-standard-8",
    max_nodes=20,
    disk_size=200
)
```

---

### Building Blocks (Advanced)

For more control, use individual constructs:

```python
from infrastructure_lib import (
    DevProfile, ProdProfile,
    StandardVPC, StandardCluster, 
    StandardSecrets, StandardIdentity,
    NetworkConfig, ClusterConfig
)

# 1. Choose a profile
profile = ProdProfile(
    project_id="my-project",
    region="us-central1",
    env="prod",
    prefix="myapp"
)

# 2. Create VPC with custom CIDR
vpc = StandardVPC(stack, "vpc",
    config=profile.get_network_config(cidr="10.1.0.0/16")
)

# 3. Create GKE with custom settings
cluster = StandardCluster(stack, "gke",
    config=profile.get_cluster_config(
        machine_type="n2-standard-8",
        max_nodes=15
    ),
    network_id=vpc.network_id,
    subnet_id=vpc.subnet_id
)

# 4. Create secrets separately
secrets = StandardSecrets(stack, "secrets",
    secret_ids=["db-password", "redis-password"]
)

# 5. Setup Workload Identity
identity = StandardIdentity(stack, "identity",
    project_id="my-project",
    sa_id="my-service-account",
    k8s_namespace="default",
    k8s_sa_name="my-k8s-sa",
    roles=["roles/secretmanager.secretAccessor"]
)
```

---

## ⚙️ Configuration

### Required Parameters

These must always be provided:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `project_id` | `str` | GCP Project ID | `"my-gcp-project-123"` |
| `region` | `str` | GCP Region | `"europe-west1"` |
| `env` | `str` | Environment name | `"dev"`, `"staging"`, `"prod"` |
| `prefix` | `str` | Resource naming prefix | `"myapp"` |

### Optional Parameters

#### Network Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cidr` | `10.0.0.0/16` | Primary subnet CIDR |
| `pod_cidr` | `10.11.0.0/21` | Secondary range for pods (~2000 pods) |
| `service_cidr` | `10.12.0.0/21` | Secondary range for services |
| `pod_range_name` | `pod-ranges` | Name of pod secondary range |
| `service_range_name` | `service-ranges` | Name of service secondary range |

#### Cluster Configuration

| Parameter | Dev Default | Prod Default | Description |
|-----------|-------------|--------------|-------------|
| `zone` | `{region}-a` | `{region}-a` | GCP zone |
| `machine_type` | `e2-medium` | `n2-standard-4` | Node machine type |
| `node_count` | `1` | `3` | Initial node count |
| `min_nodes` | `1` | `3` | Autoscaler minimum |
| `max_nodes` | `3` | `10` | Autoscaler maximum |
| `disk_size` | `50` | `100` | Node disk size (GB) |
| `spot_instances` | `true` | `false` | Use spot/preemptible VMs |
| `master_cidr` | `172.16.0.0/28` | `172.16.0.0/28` | Private cluster master CIDR |

### Environment Profiles

| Profile | Use Case | Key Characteristics |
|---------|----------|---------------------|
| `DevProfile` | Development | Cost-optimized, spot instances, small nodes |
| `StagingProfile` | Pre-production | Production-like but with spot instances |
| `ProdProfile` | Production | HA, no spot, larger nodes, deletion protection |

---

## 📚 API Reference

### StandardPlatform

```python
StandardPlatform(
    scope: Construct,
    id: str,
    project_id: str,           # Required
    region: str,               # Required
    env: str,                  # Required
    prefix: str,               # Required
    secret_ids: list[str],     # Optional
    workload_identity: dict,   # Optional
    **cluster_overrides        # Optional
)
```

**Properties:**
- `vpc` → `StandardVPC`
- `cluster` → `StandardCluster`
- `secrets` → `StandardSecrets` (raises `ValueError` if not configured)
- `identity` → `StandardIdentity` (raises `ValueError` if not configured)
- `has_secrets` → `bool`
- `has_identity` → `bool`
- `cluster_name` → `str`
- `cluster_endpoint` → `str`
- `network_id` → `str`
- `subnet_id` → `str`
- `identity_email` → `str`

### StandardVPC

```python
StandardVPC(
    scope: Construct,
    id: str,
    config: NetworkConfig,
    labels: dict[str, str] = None  # Optional
)
```

**Properties:**
- `network` → `ComputeNetwork`
- `subnet` → `ComputeSubnetwork`
- `router` → `ComputeRouter`
- `nat` → `ComputeRouterNat`
- `network_id` → `str`
- `subnet_id` → `str`

### StandardCluster

```python
StandardCluster(
    scope: Construct,
    id: str,
    config: ClusterConfig,
    network_id: str,
    subnet_id: str
)
```

**Properties:**
- `cluster` → `ContainerCluster`
- `node_pool` → `ContainerNodePool`

### StandardSecrets

```python
StandardSecrets(
    scope: Construct,
    id: str,
    secret_ids: list[str]
)
```

**Properties:**
- `secret_ids` → `list[str]`

**Methods:**
- `get_secret(secret_id: str)` → `SecretManagerSecret`

### StandardIdentity

```python
StandardIdentity(
    scope: Construct,
    id: str,
    project_id: str,
    sa_id: str,              # 6-30 characters
    k8s_namespace: str,
    k8s_sa_name: str,
    roles: list[str] = None  # Optional
)
```

**Properties:**
- `gsa` → `ServiceAccount`
- `email` → `str`

---

## 💡 Examples

### Example 1: Basic Dev Environment

```python
platform = StandardPlatform(stack, "dev",
    project_id="my-project",
    region="us-central1",
    env="dev",
    prefix="myapp"
)
```

**Creates:**
- VPC: `myapp-dev-vpc`
- Subnet: `myapp-dev-subnet`
- Cluster: `myapp-dev-cluster` (e2-medium, 1-3 nodes, spot)

### Example 2: Production with HA

```python
platform = StandardPlatform(stack, "prod",
    project_id="my-project",
    region="europe-west1",
    env="prod",
    prefix="myapp",
    max_nodes=20
)
```

**Creates:**
- Cluster with n2-standard-4 nodes
- 3-20 nodes autoscaling
- Deletion protection enabled
- No spot instances

### Example 3: Multiple Environments

```python
import os

env = os.getenv("ENV", "dev")

platform = StandardPlatform(stack, f"{env}-platform",
    project_id=os.getenv("GCP_PROJECT_ID"),
    region=os.getenv("GCP_REGION", "us-central1"),
    env=env,
    prefix="myapp"
)
```

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=infrastructure_lib

# Run specific test
pytest tests/test_config.py::TestClusterConfig -v
```

### Test Coverage

- ✅ Configuration validation
- ✅ Auto-generated properties
- ✅ Profile configuration
- ✅ Override mechanism

---

## 📁 Project Structure

```
x-infra-kit/
├── infrastructure_lib/          # Main library
│   ├── __init__.py             # Public exports
│   ├── config.py               # Configuration dataclasses
│   ├── profiles.py             # Environment profiles
│   ├── networking.py           # VPC, Subnet, NAT
│   ├── gke.py                  # GKE Cluster
│   ├── security.py             # Secrets, Workload Identity
│   └── composites.py           # StandardPlatform
├── tests/                       # Unit tests
│   └── test_config.py
├── main.py                      # Example usage
├── setup.py                     # Package definition
├── requirements.txt             # Dependencies
├── cdktf.json                   # CDKTF configuration
└── README.md                    # This file
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the existing code style:
   - Type hints on all functions
   - Docstrings on all classes and public methods
   - Validation in constructors
   - Tests for new features
4. Run tests (`pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [CDKTF](https://developer.hashicorp.com/terraform/cdktf) - Cloud Development Kit for Terraform
- [Google Cloud Provider](https://registry.terraform.io/providers/hashicorp/google/latest) - Terraform Google Cloud Provider

---

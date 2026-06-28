# AGENTS.md

> This document provides essential context and instructions for AI coding agents working with the Cincinnati Operator (OpenShift Update Service Operator) codebase.

## Project Overview

The **Cincinnati Operator** (also known as **OpenShift Update Service Operator** or **OSUS**) is a Kubernetes operator built using the [Operator SDK](https://sdk.operatorframework.io/) (v1.31.0-ocp). It manages the lifecycle of the OpenShift Update Service, which provides update graph information for OpenShift clusters.

### What This Operator Does

- Deploys and manages Cincinnati/Update Service instances on OpenShift clusters
- Creates and reconciles Deployments, Services, Routes, ConfigMaps, Secrets, PodDisruptionBudgets, and NetworkPolicies
- Handles graph data initialization via init containers
- Supports disconnected/air-gapped environments with external registry CA injection
- Integrates with OpenShift's cluster-wide proxy configuration

### Key Components

| Component | Description |
|-----------|-------------|
| **Graph Builder** | Scrapes release images from container registries and builds update graphs |
| **Policy Engine** | Applies filters to the update graph and exposes it via REST API |
| **Graph Data Init Container** | Loads graph data from a container image at pod startup |

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    UpdateService CR                              │
│  spec.replicas, spec.releases, spec.graphDataImage               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                UpdateServiceReconciler                           │
│  controllers/updateservice_controller.go                         │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────────┐     ┌──────────────┐
   │Deployment│        │   Services   │     │    Route     │
   │  + PDB   │        │ (GB + PE)    │     │   (PE)       │
   └──────────┘        └──────────────┘     └──────────────┘
```

---

## Repository Structure

```
cincinnati-operator/
├── api/v1/                    # CRD types (UpdateService)
│   └── updateservice_types.go # API spec and status definitions
├── controllers/               # Controller logic
│   ├── updateservice_controller.go  # Main reconciliation loop
│   ├── new.go                 # Kubernetes resource creation
│   ├── names.go               # Resource naming conventions
│   ├── mapper.go              # Watch event mapping
│   └── *_test.go              # Unit tests
├── functests/                 # Functional/E2E tests
├── config/                    # Kustomize configurations
│   ├── crd/                   # CustomResourceDefinition
│   ├── manager/               # Operator deployment
│   ├── rbac/                  # RBAC roles and bindings
│   ├── samples/               # Example CRs
│   └── e2e/                   # E2E test configurations
├── bundle/                    # OLM bundle manifests
├── docs/                      # Documentation
├── tools/                     # Helper scripts
├── vendor/                    # Vendored dependencies
├── main.go                    # Entry point
├── Makefile                   # Build and development commands
├── go.mod / go.sum            # Go module definitions
└── PROJECT                    # Kubebuilder project file
```

---

## Development Environment Setup

### Prerequisites

- **Go**: 1.22+ (as specified in `go.mod`)
- **OpenShift/Kubernetes cluster**: Access with cluster-admin privileges
- **oc CLI**: OpenShift command-line tool
- **Container runtime**: Podman or Docker

### Required Environment Variables

```bash
# Always required for running the operator locally
export RELATED_IMAGE_OPERAND="quay.io/app-sre/cincinnati:2873c6b"  # Cincinnati operand image
export OPERATOR_NAME=updateservice-operator
export POD_NAMESPACE=openshift-update-service

# Required for functional tests
export KUBECONFIG="path/to/kubeconfig"
export GRAPH_DATA_IMAGE="your-registry/your-repo/your-init-container:tag"

# Optional: Override operator image
export RELATED_IMAGE_OPERATOR="your-registry/your-operator-image:tag"
```

### Initial Setup

```bash
# Create the operator namespace
oc create namespace openshift-update-service
oc project openshift-update-service

# Install CRDs
make manifests
oc apply -f config/crd/bases/

# Download required tools (kustomize, controller-gen, operator-sdk)
make kustomize controller-gen operator-sdk
```

---

## Frequently Used Commands

### Building

```bash
# Build the operator binary
make build

# Build operator container image
podman build -f ./Dockerfile --platform=linux/amd64 -t your-registry/your-repo/update-service-operator:tag

# Push the image
podman push your-registry/your-repo/update-service-operator:tag
```

### Running Locally

```bash
# Run the operator locally against a cluster (uses current kubeconfig)
export RELATED_IMAGE_OPERAND="quay.io/app-sre/cincinnati:2873c6b"
export POD_NAMESPACE=openshift-update-service
make run
```

### Deploying to Cluster

```bash
# Deploy operator to cluster (uses kustomize)
make deploy

# With custom operator image
export RELATED_IMAGE_OPERATOR="your-registry/your-operator-image:tag"
make deploy
```

### Testing

```bash
# Run unit tests
make unit-test

# Run functional/E2E tests (requires KUBECONFIG and GRAPH_DATA_IMAGE)
export KUBECONFIG="/path/to/kubeconfig"
export GRAPH_DATA_IMAGE="your-registry/graph-data:tag"
make func-test

# Run scorecard tests
make scorecard-test
```

### Code Generation

```bash
# Generate CRD manifests, RBAC, and DeepCopy methods
make manifests generate

# Generate OLM bundle
OPERATOR_VERSION=5.0.0 IMG=your-registry/operator:v5.0.0 make bundle

# Format and vet code
make fmt vet

# Verify generated files are up to date
make verify-generate

# Verify FIPS compliance (no golang.org/x/crypto usage)
make verify-crypto
```

### Cleanup

```bash
make clean
```

---

## Testing Guidelines

### Unit Tests

Unit tests are located in `controllers/*_test.go` and use:
- **testing package**: Standard Go testing
- **testify/assert**: Assertions
- **controller-runtime/pkg/client/fake**: Fake Kubernetes client

**Test patterns used:**

```go
// Table-driven tests with test cases
tests := []struct {
    name           string
    existingObjs   []runtime.Object
    expectedError  error
}{...}

// Create test reconciler with fake client
r := newTestReconciler(test.existingObjs...)

// Execute reconciliation
_, err := r.Reconcile(ctx, request)

// Verify conditions and state
verifyConditions(t, test.expectedConditions, instance)
```

**Running a specific test:**

```bash
go test -v ./controllers/... -run TestEnsureDeployment
```

### Functional Tests

Functional tests are in `functests/` and require a live cluster:

```bash
# Prerequisites
export KUBECONFIG="/path/to/kubeconfig"
export GRAPH_DATA_IMAGE="your-registry/graph-data:tag"

# Run tests
make func-test
```

Functional tests verify:
- Operator deployment is running
- Custom resource creation
- Deployment, Services, PDB, Route creation
- Policy engine endpoint availability

---

## Code Style and Conventions

### Go Conventions

- Follow standard Go formatting (`go fmt`)
- Use Go modules with vendoring (`-mod=vendor`)
- Run `go vet` before committing

### Naming Conventions

Resource names follow patterns defined in `controllers/names.go`:

| Resource | Naming Pattern |
|----------|---------------|
| Deployment | `{instance.Name}` |
| Config ConfigMap | `{instance.Name}-config` |
| Env ConfigMap | `{instance.Name}-env` |
| GraphBuilder Service | `{instance.Name}-graph-builder` |
| PolicyEngine Service | `{instance.Name}-policy-engine` |
| Route | `{instance.Name}-route` |
| PodDisruptionBudget | `{instance.Name}` |
| Pull Secret Copy | `{instance.Name}-pull-secret` |

### API Conventions

- CRD is namespaced
- Group: `updateservice.operator.openshift.io`
- Version: `v1`
- Kind: `UpdateService`

### Controller Patterns

The reconciler follows this pattern:

1. **Gather conditions** - Check cluster state (pull secrets, CA certs)
2. **Create resources** - Build all Kubernetes resources using `newKubeResources()`
3. **Ensure resources** - Reconcile each resource to match desired state

### RBAC Markers

RBAC permissions are defined via kubebuilder markers in `controllers/updateservice_controller.go`:

```go
// +kubebuilder:rbac:groups=...,resources=...,verbs=...
```

After modifying RBAC markers, regenerate with:

```bash
make manifests
```

---

## Key Files to Understand

| File | Purpose |
|------|---------|
| `api/v1/updateservice_types.go` | CRD spec and status types |
| `controllers/updateservice_controller.go` | Main reconciliation logic |
| `controllers/new.go` | Resource creation (Deployment, Services, etc.) |
| `controllers/names.go` | Resource naming functions and constants |
| `controllers/mapper.go` | Watch event mapping for Image and ConfigMap changes |
| `main.go` | Operator entry point, manager setup |
| `Makefile` | Build, test, deploy commands |

---

## Custom Resource Definition

### UpdateService Spec

```yaml
apiVersion: updateservice.operator.openshift.io/v1
kind: UpdateService
metadata:
  name: example
  namespace: openshift-update-service
spec:
  replicas: 2                    # Number of pods (min: 1)
  releases: "quay.io/openshift-release-dev/ocp-release"  # Registry/repo for releases
  graphDataImage: "your-registry/graph-data:tag"         # Init container image
```

### UpdateService Status

```yaml
status:
  conditions:
    - type: ReconcileCompleted
      status: "True"
      reason: Success
    - type: RegistryCACertFound
      status: "True"
      reason: CACertFound
  policyEngineURI: "https://example-route-openshift-update-service.apps.cluster.example.com"
```

### Condition Types

- `ReconcileCompleted`: All resources reconciled successfully
- `RegistryCACertFound`: External registry CA cert was found
- `ReconcileError`: An error occurred during reconciliation

---

## Common Development Tasks

### Adding a New Field to the CRD

1. Edit `api/v1/updateservice_types.go`
2. Add kubebuilder validation markers
3. Run `make manifests generate`
4. Update controller logic in `controllers/`
5. Add unit tests

### Modifying Deployment Spec

1. Edit `controllers/new.go` → `newDeployment()` function
2. Update volume mounts in `newVolumes()` and `newGraphBuilderVolumeMounts()`
3. Update container specs in `newGraphBuilderContainer()` or `newPolicyEngineContainer()`
4. Run tests: `make unit-test`

### Adding RBAC Permissions

1. Add kubebuilder RBAC markers to `controllers/updateservice_controller.go`
2. Run `make manifests`
3. Verify changes in `config/rbac/role.yaml`

### Updating Dependencies

```bash
# Update go.mod
go get <package>@<version>

# Re-vendor dependencies
go mod vendor
go mod tidy

# Verify build
make build
```

---

## Debugging Tips

### Check Operator Logs

```bash
oc logs -n openshift-update-service deployment/updateservice-operator -f
```

### Check UpdateService Instance Status

```bash
oc get updateservice -n openshift-update-service -o yaml
```

### Inspect Created Resources

```bash
# List all resources created by the operator
oc get deployment,service,route,pdb,configmap,secret,networkpolicy \
  -n openshift-update-service -l app=<instance-name>
```

### E2E Test Failure Debugging

On functional test failure, the Makefile runs `oc adm inspect`:

```bash
oc -n openshift-update-service adm inspect \
  --dest-dir="./inspect" \
  namespace/openshift-update-service \
  customresourcedefinition/updateservices.updateservice.operator.openshift.io \
  updateservice/example
```

---

## Security Considerations

### FIPS Compliance

- The operator must NOT use `golang.org/x/crypto`
- Verify with: `make verify-crypto`

### Secrets Handling

- Pull secrets are copied from `openshift-config` namespace to operator namespace
- Never log or expose secret data
- Use Kubernetes secret references, not inline secrets

### Network Policies

- The operator creates NetworkPolicies restricting pod traffic
- Ingress: Only from router namespace to policy-engine port
- Egress: TCP for registry access, DNS to openshift-dns

### Certificate Handling

- External registry CA certs are read from `image.config.openshift.io`
- Cluster-wide proxy CA is automatically injected via labeled ConfigMap
- ConfigMap key for registry CA must be `updateservice-registry` (hardcoded)

---

## OpenShift-Specific Features

### Cluster-Wide Proxy Support

The operator reads proxy environment variables (`HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`) set by OLM and propagates them to the graph-builder container.

### Route Creation

- Routes use edge TLS termination
- Route names must comply with DNS 1123 (max 63 characters)
- Validation error if route name is too long

### Image Registry Integration

The operator watches:
- `image.config.openshift.io/cluster` for `AdditionalTrustedCA` changes
- ConfigMaps in `openshift-config` namespace referenced by the Image config

---

## Related Projects

- [Cincinnati](https://github.com/openshift/cincinnati) - The upstream update service
- [Cincinnati Graph Data](https://github.com/openshift/cincinnati-graph-data) - Update graph data repository
- [Operator SDK](https://sdk.operatorframework.io/) - Operator development framework
- [Controller Runtime](https://github.com/kubernetes-sigs/controller-runtime) - Kubernetes controller library

---

## Quick Reference

### Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `RELATED_IMAGE_OPERAND` | Yes | Cincinnati container image |
| `POD_NAMESPACE` | Yes | Namespace where operator runs |
| `KUBECONFIG` | For tests | Path to kubeconfig file |
| `GRAPH_DATA_IMAGE` | For tests | Graph data init container image |
| `RELATED_IMAGE_OPERATOR` | No | Override operator image for deployment |
| `OPERATOR_VERSION` | For bundle | Version for OLM bundle generation |
| `IMG` | For bundle | Operator image for bundle |

### Make Targets Summary

| Target | Description |
|--------|-------------|
| `make build` | Build operator binary |
| `make run` | Run operator locally |
| `make deploy` | Deploy to cluster |
| `make unit-test` | Run unit tests |
| `make func-test` | Run functional tests |
| `make manifests` | Generate CRD/RBAC manifests |
| `make generate` | Generate DeepCopy methods |
| `make bundle` | Generate OLM bundle |
| `make fmt` | Format Go code |
| `make vet` | Run go vet |
| `make verify-generate` | Verify generated files |
| `make verify-crypto` | Verify FIPS compliance |
| `make clean` | Clean build artifacts |

---

## Troubleshooting Common Issues

### "RELATED_IMAGE_OPERAND must be set"

Set the environment variable before running:
```bash
export RELATED_IMAGE_OPERAND="quay.io/app-sre/cincinnati:latest"
```

### Route Name Too Long

Route names must be ≤63 characters. Error message:
```
UpdateService route name "..." cannot exceed RFC 1123 maximum length of 63
```
Solution: Use a shorter UpdateService name or namespace name.

### OOMKilled Graph Builder

If graph-builder pods are OOMKilled, it usually means there are too many release images to scrape. Copy release images to a separate repository namespace.

### ReconcileCompleted=False

Check the status conditions for the specific reason:
```bash
oc get updateservice <name> -o jsonpath='{.status.conditions}'
```

---

*This document should be updated when significant changes are made to the project structure, build process, or development workflow.*


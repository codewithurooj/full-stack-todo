# Implementation Plan: Helm Charts Deployment

**Branch**: `007-helm-charts` | **Date**: 2025-12-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-helm-charts/spec.md`

## Summary

Create production-ready Helm charts for deploying the full-stack todo application (Next.js frontend + FastAPI backend) to Kubernetes/Minikube with 2 replicas each, ClusterIP services, and NGINX ingress for external access. Charts will support environment variable configuration via values.yaml with Secrets/ConfigMaps management, health probes, resource limits, and deployment to Minikube cluster running on D:/ drive with 2 CPUs and 3GB RAM.

## Technical Context

**Language/Version**: Helm 3.x for packaging, YAML for Kubernetes manifests
**Primary Dependencies**: Docker images (todo-frontend:latest, todo-backend:latest), Minikube v1.32+, kubectl, NGINX ingress controller
**Storage**: External Neon PostgreSQL (not in-cluster), ConfigMaps for non-sensitive config, Secrets for sensitive data
**Testing**: `helm lint`, `helm install --dry-run --debug`, manual deployment verification
**Target Platform**: Minikube on Windows (D:/.minikube, 2 CPUs, 3GB RAM), Kubernetes 1.28+
**Project Type**: Web application (frontend + backend microservices)
**Performance Goals**: Pod startup < 60 seconds, application functional via ingress < 90 seconds
**Constraints**: Minikube resource limits (2 CPUs, 3GB RAM total), external database only, path-based ingress (not subdomain), image sizes matter (D:/ drive space)
**Scale/Scope**: Local development (Minikube), 4 total pods (2 frontend + 2 backend), single namespace (default)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Checking against Constitution v3.0.0, Phase IV (Containerization & Orchestration)**:

✅ **Spec-Driven Development** - Specification created in `specs/007-helm-charts/spec.md` before implementation
✅ **Docker Requirements** - Multi-stage Dockerfiles already exist (`frontend/Dockerfile`, `backend/Dockerfile`)
✅ **Kubernetes Deployment** - Will use 2 replicas per service (meets constitution minimum)
✅ **Helm Charts** - Creating separate charts for frontend and backend as per constitution
✅ **Resource Limits** - Will define requests and limits in values.yaml
✅ **Health Probes** - Dockerfiles already have HEALTHCHECK, will configure liveness/readiness probes
✅ **ConfigMaps/Secrets** - Will properly separate non-sensitive (ConfigMaps) and sensitive (Secrets) configuration
✅ **No Secrets in Images** - Using environment variables and Kubernetes Secrets
✅ **Documentation** - Will include README.md and NOTES.txt in charts

**No violations detected. Proceeding with implementation.**

## User's Helm Chart Builder Skill

**User mentioned during planning**: `helm-chart-builder` skill is available for use during implementation

**Planned Integration**:
- The skill will be invoked during `/sp.implement` phase (not during this planning phase)
- It will generate Helm chart structures from Docker image specifications
- Implementation tasks will explicitly reference the skill for chart generation

**Example usage in implementation tasks**:
```
Task: Generate Frontend Helm Chart
  Action: Use helm-chart-builder skill
  Inputs: Docker image (todo-frontend:latest), port 3000, replicas 2, environment variables
  Outputs: Complete charts/frontend/ with all templates
```

---

## Plan Complete

This implementation plan is ready for task generation via `/sp.tasks`.

**Next Steps**:
1. User reviews this plan
2. Run `/sp.tasks` to break down into actionable tasks
3. Run `/sp.implement` to execute (will invoke helm-chart-builder skill)
4. Test deployment on Minikube
5. Create PHR to document work

**Estimated Implementation Time**: 2-3 hours
**Dependencies**: Docker images exist, Minikube running
**Skill Integration**: helm-chart-builder will be used during implementation

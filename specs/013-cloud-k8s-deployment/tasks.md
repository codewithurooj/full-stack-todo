# Tasks: Cloud Kubernetes Deployment

**Input**: Design documents from `/specs/013-cloud-k8s-deployment/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/ (complete)

**Tests**: Tests are NOT explicitly requested in the feature specification. Infrastructure validation will be done via kubectl/helm commands and smoke tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Infrastructure**: `k8s/`, `charts/`, `.github/workflows/`
- **Documentation**: `docs/runbooks/`
- Paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure for cloud deployment

- [X] T001 Create namespace manifest in k8s/namespaces/todo-app-namespace.yaml
- [X] T002 [P] Create k8s/cert-manager/ directory structure
- [X] T003 [P] Create k8s/ingress/ directory structure
- [X] T004 [P] Create monitoring/prometheus/ directory structure
- [X] T005 [P] Create monitoring/grafana/dashboards/ directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Install NGINX Ingress Controller and verify LoadBalancer IP assignment (run kubectl command documented in quickstart.md)
- [ ] T007 Install cert-manager v1.13+ and verify pods are running (run kubectl command documented in quickstart.md)
- [X] T008 Create ClusterIssuer for Let's Encrypt staging in k8s/cert-manager/cluster-issuer-letsencrypt-staging.yaml
- [X] T009 Create ClusterIssuer for Let's Encrypt production in k8s/cert-manager/cluster-issuer-letsencrypt-prod.yaml
- [ ] T010 Apply ClusterIssuers and verify with kubectl get clusterissuers
- [ ] T011 Create container registry pull secret (regcred) in todo-app namespace per quickstart.md
- [ ] T012 Create application secrets (todo-backend-secret, todo-frontend-secret) in todo-app namespace per quickstart.md

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Deploy Application to Production Cloud (Priority: P1) 🎯 MVP

**Goal**: Deploy the full-stack todo application to a production-grade cloud Kubernetes environment so that users can access the application reliably over the internet

**Independent Test**: Deploy application to cloud cluster and verify it's accessible via a public URL

### Implementation for User Story 1

- [X] T013 [P] [US1] Create cloud-specific values file in charts/backend/values-oke.yaml (Oracle OKE configuration)
- [X] T014 [P] [US1] Create cloud-specific values file in charts/backend/values-aks.yaml (Azure AKS configuration)
- [X] T015 [P] [US1] Create cloud-specific values file in charts/backend/values-gke.yaml (Google GKE configuration)
- [X] T016 [P] [US1] Create cloud-specific values file in charts/frontend/values-oke.yaml (Oracle OKE configuration)
- [X] T017 [P] [US1] Create cloud-specific values file in charts/frontend/values-aks.yaml (Azure AKS configuration)
- [X] T018 [P] [US1] Create cloud-specific values file in charts/frontend/values-gke.yaml (Google GKE configuration)
- [ ] T019 [US1] Update charts/backend/values.yaml to add imagePullSecrets and ingress sections per ingress-templates.yaml contract
- [ ] T020 [US1] Update charts/frontend/values.yaml to add imagePullSecrets and ingress sections per ingress-templates.yaml contract
- [ ] T021 [US1] Build and push backend Docker image to container registry with multi-arch support (linux/amd64,linux/arm64)
- [ ] T022 [US1] Build and push frontend Docker image to container registry with multi-arch support (linux/amd64,linux/arm64)
- [ ] T023 [US1] Deploy backend with helm upgrade --install todo-backend ./charts/backend -n todo-app -f charts/backend/values-oke.yaml
- [ ] T024 [US1] Deploy frontend with helm upgrade --install todo-frontend ./charts/frontend -n todo-app -f charts/frontend/values-oke.yaml
- [ ] T025 [US1] Verify deployment with kubectl get pods -n todo-app and kubectl rollout status deployment/todo-backend -n todo-app
- [ ] T026 [US1] Test application access via port-forward: kubectl port-forward svc/todo-frontend 3000:3000 -n todo-app

**Checkpoint**: Application deployed and accessible. User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Secure HTTPS Access with Automatic Certificates (Priority: P1)

**Goal**: Enable HTTPS with valid TLS certificates so that user data is encrypted in transit

**Independent Test**: Access application URL and verify browser shows a valid, trusted TLS certificate

### Implementation for User Story 2

- [X] T027 [P] [US2] Create combined ingress manifest in k8s/ingress/todo-app-ingress.yaml per ingress-templates.yaml contract
- [X] T028 [US2] Update Helm ingress templates in charts/backend/templates/ingress.yaml with cert-manager annotations
- [X] T029 [US2] Update Helm ingress templates in charts/frontend/templates/ingress.yaml with cert-manager annotations
- [X] T030 [US2] Configure DNS A record: point domain to LoadBalancer external IP (document in docs/runbooks/dns-setup.md)
- [ ] T031 [US2] Apply ingress with staging issuer first (cert-manager.io/cluster-issuer: letsencrypt-staging)
- [ ] T032 [US2] Verify staging certificate issuance with kubectl get certificates -n todo-app and kubectl describe certificate
- [ ] T033 [US2] Switch to production issuer (cert-manager.io/cluster-issuer: letsencrypt-prod) and redeploy
- [ ] T034 [US2] Verify production TLS certificate with openssl s_client command per quickstart.md
- [ ] T035 [US2] Test HTTP to HTTPS redirect by accessing http://todo.domain.com and verifying redirect

**Checkpoint**: HTTPS working with valid certificate. User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Automated CI/CD Pipeline (Priority: P2)

**Goal**: Automatically build, test, and deploy code changes pushed to main branch

**Independent Test**: Push a code change to main branch and verify it's automatically deployed within 15 minutes

### Implementation for User Story 3

- [X] T036 [P] [US3] Create GitHub Actions workflow file in .github/workflows/deploy.yml per github-actions-workflow.yaml contract
- [ ] T037 [US3] Configure GitHub repository secrets (REGISTRY_USERNAME, REGISTRY_PASSWORD, OKE_KUBECONFIG, DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY)
- [X] T038 [US3] Add build-test job to workflow: checkout, setup Python/Node, run pytest, run npm test, build Docker images
- [X] T039 [US3] Add push-images job to workflow: login to registry, push backend/frontend/microservice images with sha-tag and latest
- [X] T040 [US3] Add deploy job to workflow: configure kubectl, create/update secrets, helm upgrade, verify rollout
- [X] T041 [US3] Add smoke test step to deploy job: curl health endpoints after deployment
- [ ] T042 [US3] Test workflow by pushing a minor change and verifying full pipeline execution
- [ ] T043 [US3] Verify deployment blocking on test failure (intentionally break a test, confirm deployment blocked)

**Checkpoint**: CI/CD pipeline functional. Code changes auto-deploy on push to main.

---

## Phase 6: User Story 4 - Container Image Management (Priority: P2)

**Goal**: Store container images securely in a private registry with proper tagging

**Independent Test**: Build and push an image to registry, then verify cluster can pull it

### Implementation for User Story 4

- [X] T044 [P] [US4] Document container registry setup for Oracle OCIR in docs/runbooks/container-registry-setup.md
- [X] T045 [P] [US4] Document container registry setup for Azure ACR in docs/runbooks/container-registry-setup.md
- [X] T046 [P] [US4] Document container registry setup for Google GCR in docs/runbooks/container-registry-setup.md
- [ ] T047 [US4] Update docker-compose.yml to support multi-arch builds using buildx
- [ ] T048 [US4] Configure image tagging strategy in CI/CD: sha-{short}, latest, v{semver} for releases
- [ ] T049 [US4] Create image pull secrets for each supported registry in Helm values files
- [ ] T050 [US4] Document image retention policy (30 days for non-tagged images) in docs/runbooks/container-registry-setup.md
- [ ] T051 [US4] Verify cluster can pull images by deploying with new image tag

**Checkpoint**: Container images properly managed and accessible to cluster.

---

## Phase 7: User Story 5 - Production Monitoring and Alerting (Priority: P3)

**Goal**: Monitor application health, performance, and resource utilization with dashboards and alerts

**Independent Test**: Access monitoring dashboard and verify metrics are displayed for all components

### Implementation for User Story 5

- [X] T052 [P] [US5] Create ServiceMonitor for backend in monitoring/prometheus/servicemonitor-backend.yaml
- [X] T053 [P] [US5] Create ServiceMonitor for frontend in monitoring/prometheus/servicemonitor-frontend.yaml
- [ ] T054 [US5] Install kube-prometheus-stack with Helm per plan.md (helm install prometheus prometheus-community/kube-prometheus-stack)
- [ ] T055 [US5] Configure Prometheus retention to 7 days in Helm values
- [ ] T056 [US5] Import existing alerts from monitoring/alerts.yaml into Prometheus
- [ ] T057 [US5] Import existing Grafana dashboards from monitoring/grafana-dashboards/ into kube-prometheus-stack
- [X] T058 [US5] Create custom Grafana dashboard for todo-app in monitoring/grafana/dashboards/todo-app.json
- [X] T059 [US5] Configure Alertmanager for email/Slack notifications (document in docs/runbooks/alerting-setup.md)
- [ ] T060 [US5] Verify metrics collection: kubectl port-forward svc/prometheus-grafana 3001:80 -n monitoring
- [ ] T061 [US5] Test alert triggering by simulating high error rate or pod failure

**Checkpoint**: Monitoring operational. Dashboards show real-time metrics and alerts fire correctly.

---

## Phase 8: User Story 6 - Multi-Cloud Provider Support (Priority: P3)

**Goal**: Enable deployment to different cloud providers (AKS, GKE, OKE) without code changes

**Independent Test**: Verify deployment configurations exist for each provider and deploy to at least one alternate provider

### Implementation for User Story 6

- [X] T062 [P] [US6] Create cloud-specific values for microservices in charts/notification-service/values-oke.yaml
- [X] T063 [P] [US6] Create cloud-specific values for microservices in charts/notification-service/values-aks.yaml
- [X] T064 [P] [US6] Create cloud-specific values for microservices in charts/recurring-task-service/values-oke.yaml
- [X] T065 [P] [US6] Create cloud-specific values for microservices in charts/recurring-task-service/values-aks.yaml
- [X] T066 [US6] Add cloud_provider input to GitHub Actions workflow_dispatch for provider selection
- [X] T067 [US6] Update deploy job to use provider-specific values files based on input
- [X] T068 [US6] Document provider-specific setup in docs/runbooks/cloud-provider-setup-oke.md
- [X] T069 [US6] Document provider-specific setup in docs/runbooks/cloud-provider-setup-aks.md
- [X] T070 [US6] Document provider-specific setup in docs/runbooks/cloud-provider-setup-gke.md
- [ ] T071 [US6] Validate deployment to alternate provider (if accessible) using workflow_dispatch

**Checkpoint**: Multi-cloud support complete. Same application deployable to AKS, GKE, or OKE.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T072 [P] Create operational runbook for common troubleshooting in docs/runbooks/troubleshooting.md
- [X] T073 [P] Create operational runbook for rollback procedures in docs/runbooks/rollback.md
- [X] T074 [P] Create operational runbook for scaling operations in docs/runbooks/scaling.md
- [X] T075 Document all environment variables and secrets in docs/runbooks/secrets-management.md
- [X] T076 Add NetworkPolicy for security (restrict traffic to ingress controller) per ingress-templates.yaml contract
- [X] T077 Configure HPA for backend and frontend deployments per data-model.md specifications
- [ ] T078 Run full quickstart.md validation - deploy fresh and verify all functionality
- [ ] T079 Update main README.md with cloud deployment instructions and links

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - US1 (Deploy) and US2 (TLS) should complete first as P1 priority
  - US3 (CI/CD) and US4 (Registry) can proceed in parallel after US1
  - US5 (Monitoring) and US6 (Multi-cloud) can proceed in parallel after US1
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after US1 (needs deployed application for TLS verification)
- **User Story 3 (P2)**: Can start after US1 - Automates deployment process
- **User Story 4 (P2)**: Can start after Foundational - Documents registry setup
- **User Story 5 (P3)**: Can start after US1 - Needs deployed application to monitor
- **User Story 6 (P3)**: Can start after US1 - Extends to additional cloud providers

### Within Each User Story

- Infrastructure before deployment
- Deployment before verification
- Verification before next story
- Commit after each task or logical group

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Cloud-specific values files (T013-T018, T062-T065) can be created in parallel
- Documentation runbooks (T044-T046, T068-T070, T072-T074) can be written in parallel
- ServiceMonitors (T052-T053) can be created in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all cloud-specific values files together:
Task: "Create cloud-specific values file in charts/backend/values-oke.yaml"
Task: "Create cloud-specific values file in charts/backend/values-aks.yaml"
Task: "Create cloud-specific values file in charts/backend/values-gke.yaml"
Task: "Create cloud-specific values file in charts/frontend/values-oke.yaml"
Task: "Create cloud-specific values file in charts/frontend/values-aks.yaml"
Task: "Create cloud-specific values file in charts/frontend/values-gke.yaml"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Deploy Application)
4. Complete Phase 4: User Story 2 (HTTPS/TLS)
5. **STOP and VALIDATE**: Application accessible via HTTPS with valid certificate
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Application deployed (MVP!)
3. Add User Story 2 → Test independently → HTTPS working
4. Add User Story 3 → Test independently → CI/CD automated
5. Add User Story 4 → Test independently → Registry documented
6. Add User Story 5 → Test independently → Monitoring operational
7. Add User Story 6 → Test independently → Multi-cloud ready
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Stories 1 + 2 (Deploy + TLS)
   - Developer B: User Story 3 (CI/CD)
   - Developer C: User Stories 4 + 6 (Registry + Multi-cloud)
   - Developer D: User Story 5 (Monitoring)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Use staging TLS issuer first before switching to production
- Multi-arch builds (amd64 + arm64) required for Oracle OKE ARM instances
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

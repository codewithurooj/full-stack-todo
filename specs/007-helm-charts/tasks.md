---
description: "Task list for Helm Charts Deployment feature"
---

# Tasks: Helm Charts Deployment

**Input**: Design documents from `/specs/007-helm-charts/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: No tests requested in specification - focus on deployment validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `charts/frontend/`, `charts/backend/`
- Kubernetes manifests in `charts/[service]/templates/`
- Configuration in `charts/[service]/values.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create Helm chart directory structure and initialize both charts

- [ ] T001 Create charts directory structure with `charts/frontend/` and `charts/backend/` directories
- [ ] T002 [P] Create Chart.yaml for frontend chart in charts/frontend/Chart.yaml
- [ ] T003 [P] Create Chart.yaml for backend chart in charts/backend/Chart.yaml
- [ ] T004 [P] Create values.yaml for frontend chart in charts/frontend/values.yaml
- [ ] T005 [P] Create values.yaml for backend chart in charts/backend/values.yaml
- [ ] T006 [P] Create templates directory for frontend in charts/frontend/templates/
- [ ] T007 [P] Create templates directory for backend in charts/backend/templates/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core configuration resources that MUST be complete before ANY user story deployment

**⚠️ CRITICAL**: No deployment can happen until ConfigMaps and Secrets are defined

- [ ] T008 [P] Create ConfigMap template for frontend non-sensitive config in charts/frontend/templates/configmap.yaml
- [ ] T009 [P] Create ConfigMap template for backend non-sensitive config in charts/backend/templates/configmap.yaml
- [ ] T010 [P] Create Secret template for frontend sensitive config in charts/frontend/templates/secret.yaml
- [ ] T011 [P] Create Secret template for backend sensitive config in charts/backend/templates/secret.yaml
- [ ] T012 [P] Create Service template for frontend (ClusterIP) in charts/frontend/templates/service.yaml
- [ ] T013 [P] Create Service template for backend (ClusterIP) in charts/backend/templates/service.yaml
- [ ] T014 [P] Create helpers template for frontend in charts/frontend/templates/_helpers.tpl
- [ ] T015 [P] Create helpers template for backend in charts/backend/templates/_helpers.tpl

**Checkpoint**: Configuration resources ready - deployments can now reference ConfigMaps/Secrets

---

## Phase 3: User Story 1 - Deploy Full-Stack Application to Minikube (Priority: P1) 🎯 MVP

**Goal**: Deploy complete application with 2 frontend and 2 backend replicas, all pods running successfully

**Independent Test**: Run `helm install todo-app ./charts/frontend` and `helm install todo-api ./charts/backend`, verify 4 pods reach Running state with `kubectl get pods`

### Implementation for User Story 1

- [ ] T016 [P] [US1] Create Deployment template for frontend with 2 replicas in charts/frontend/templates/deployment.yaml
- [ ] T017 [P] [US1] Create Deployment template for backend with 2 replicas in charts/backend/templates/deployment.yaml
- [ ] T018 [US1] Configure environment variables from ConfigMap in frontend Deployment (depends on T016, T008)
- [ ] T019 [US1] Configure environment variables from ConfigMap in backend Deployment (depends on T017, T009)
- [ ] T020 [US1] Configure environment variables from Secret in frontend Deployment (depends on T016, T010)
- [ ] T021 [US1] Configure environment variables from Secret in backend Deployment (depends on T017, T011)
- [ ] T022 [P] [US1] Configure liveness probe for frontend (HTTP GET /) in charts/frontend/templates/deployment.yaml
- [ ] T023 [P] [US1] Configure readiness probe for frontend (HTTP GET /) in charts/frontend/templates/deployment.yaml
- [ ] T024 [P] [US1] Configure liveness probe for backend (HTTP GET /health) in charts/backend/templates/deployment.yaml
- [ ] T025 [P] [US1] Configure readiness probe for backend (HTTP GET /health) in charts/backend/templates/deployment.yaml
- [ ] T026 [P] [US1] Create NOTES.txt with installation instructions in charts/frontend/templates/NOTES.txt
- [ ] T027 [P] [US1] Create NOTES.txt with installation instructions in charts/backend/templates/NOTES.txt
- [ ] T028 [US1] Build Docker images and load into Minikube (frontend and backend)
- [ ] T029 [US1] Deploy frontend chart with `helm install todo-app ./charts/frontend`
- [ ] T030 [US1] Deploy backend chart with `helm install todo-api ./charts/backend`
- [ ] T031 [US1] Verify all 4 pods are Running with `kubectl get pods`

**Checkpoint**: At this point, basic deployment should work - 4 pods running, services created

---

## Phase 4: User Story 2 - Configure Environment Variables (Priority: P2)

**Goal**: Enable configuration customization through Helm values without rebuilding images

**Independent Test**: Install charts with custom values.yaml, verify environment variables in pods via `kubectl exec`

### Implementation for User Story 2

- [ ] T032 [P] [US2] Define frontend environment variables in charts/frontend/values.yaml (NEXT_PUBLIC_API_URL, NEXT_PUBLIC_OPENAI_DOMAIN_KEY)
- [ ] T033 [P] [US2] Define backend environment variables in charts/backend/values.yaml (DATABASE_URL, BETTER_AUTH_SECRET, OPENAI_API_KEY)
- [ ] T034 [US2] Update frontend ConfigMap template to use values from values.yaml (depends on T032)
- [ ] T035 [US2] Update backend ConfigMap template to use values from values.yaml (depends on T033)
- [ ] T036 [US2] Update frontend Secret template to use values from values.yaml (depends on T032)
- [ ] T037 [US2] Update backend Secret template to use values from values.yaml (depends on T033)
- [ ] T038 [P] [US2] Create example custom values file in charts/frontend/values-example.yaml
- [ ] T039 [P] [US2] Create example custom values file in charts/backend/values-example.yaml
- [ ] T040 [US2] Test upgrade with custom values using `helm upgrade -f values-example.yaml`
- [ ] T041 [US2] Verify environment variables in pods using `kubectl exec`

**Checkpoint**: Configuration should be fully parameterized through values.yaml

---

## Phase 5: User Story 3 - Access Application via Ingress (Priority: P1)

**Goal**: Enable external access through single ingress URL with path-based routing

**Independent Test**: Visit `http://todo.local/` for frontend and `http://todo.local/api/health` for backend API

### Implementation for User Story 3

- [ ] T042 [US3] Create Ingress template with path-based routing in charts/frontend/templates/ingress.yaml
- [ ] T043 [US3] Configure Ingress host (todo.local) and frontend path (/) in charts/frontend/values.yaml
- [ ] T044 [US3] Configure backend path (/api) routing to backend service in charts/frontend/templates/ingress.yaml
- [ ] T045 [US3] Add ingress annotations for NGINX controller in charts/frontend/templates/ingress.yaml
- [ ] T046 [US3] Enable ingress in Minikube with `minikube addons enable ingress`
- [ ] T047 [US3] Add /etc/hosts entry for todo.local (127.0.0.1 todo.local on Windows)
- [ ] T048 [US3] Start Minikube tunnel with `minikube tunnel`
- [ ] T049 [US3] Test frontend access at http://todo.local/
- [ ] T050 [US3] Test backend access at http://todo.local/api/health
- [ ] T051 [US3] Verify CORS configuration allows frontend to call backend API

**Checkpoint**: Application should be fully accessible via ingress with production-like routing

---

## Phase 6: User Story 4 - Upgrade and Rollback Deployments (Priority: P3)

**Goal**: Enable safe deployment updates with rollback capability

**Independent Test**: Perform `helm upgrade` with new image tag, then `helm rollback`, verify successful version changes

### Implementation for User Story 4

- [ ] T052 [P] [US4] Add image.tag parameter to frontend values.yaml with default "latest"
- [ ] T053 [P] [US4] Add image.tag parameter to backend values.yaml with default "latest"
- [ ] T054 [US4] Update frontend Deployment to use image.tag from values (depends on T052)
- [ ] T055 [US4] Update backend Deployment to use image.tag from values (depends on T053)
- [ ] T056 [P] [US4] Configure rolling update strategy in frontend Deployment (maxSurge: 1, maxUnavailable: 0)
- [ ] T057 [P] [US4] Configure rolling update strategy in backend Deployment (maxSurge: 1, maxUnavailable: 0)
- [ ] T058 [US4] Test upgrade: Build new image with tag "1.1" and load into Minikube
- [ ] T059 [US4] Execute upgrade with `helm upgrade todo-app --set image.tag=1.1`
- [ ] T060 [US4] Verify new pods are created and old pods terminate gracefully
- [ ] T061 [US4] Test rollback with `helm rollback todo-app`
- [ ] T062 [US4] Verify system returns to previous version successfully

**Checkpoint**: Helm upgrade and rollback should work reliably with zero downtime

---

## Phase 7: User Story 5 - Monitor Resource Usage (Priority: P3)

**Goal**: Set resource limits to ensure efficient operation within Minikube constraints

**Independent Test**: Install charts with resource definitions, verify limits with `kubectl describe pod`

### Implementation for User Story 5

- [ ] T063 [P] [US5] Define frontend resource requests in values.yaml (cpu: 100m, memory: 128Mi)
- [ ] T064 [P] [US5] Define frontend resource limits in values.yaml (cpu: 500m, memory: 256Mi)
- [ ] T065 [P] [US5] Define backend resource requests in values.yaml (cpu: 200m, memory: 256Mi)
- [ ] T066 [P] [US5] Define backend resource limits in values.yaml (cpu: 1000m, memory: 512Mi)
- [ ] T067 [US5] Update frontend Deployment to include resource requests/limits (depends on T063, T064)
- [ ] T068 [US5] Update backend Deployment to include resource requests/limits (depends on T065, T066)
- [ ] T069 [US5] Verify total resource requests fit within Minikube limits (2 CPUs, 3GB RAM)
- [ ] T070 [US5] Deploy with resource limits and verify with `kubectl describe pod`
- [ ] T071 [US5] Monitor pod resource usage with `kubectl top pods` (requires metrics-server)

**Checkpoint**: Resource management should prevent pods from exceeding limits

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation across all charts

- [ ] T072 [P] Create README.md for frontend chart in charts/frontend/README.md
- [ ] T073 [P] Create README.md for backend chart in charts/backend/README.md
- [ ] T074 [P] Document values.yaml parameters with comments in charts/frontend/values.yaml
- [ ] T075 [P] Document values.yaml parameters with comments in charts/backend/values.yaml
- [ ] T076 [P] Validate frontend chart with `helm lint charts/frontend`
- [ ] T077 [P] Validate backend chart with `helm lint charts/backend`
- [ ] T078 [P] Test dry-run for frontend with `helm install --dry-run --debug todo-app charts/frontend`
- [ ] T079 [P] Test dry-run for backend with `helm install --dry-run --debug todo-api charts/backend`
- [ ] T080 Create master documentation in docs/007-helm-deployment-guide.md
- [ ] T081 Update main README.md with Helm deployment instructions
- [ ] T082 Create quickstart script for complete deployment in scripts/helm-deploy.sh

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all deployments
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) - Core MVP deployment
- **User Story 2 (Phase 4)**: Depends on US1 - Enhances configuration management
- **User Story 3 (Phase 5)**: Depends on US1 - Adds external access
- **User Story 4 (Phase 6)**: Depends on US1 - Adds upgrade/rollback capability
- **User Story 5 (Phase 7)**: Depends on US1 - Adds resource management
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ REQUIRED FOR MVP
- **User Story 2 (P2)**: Enhances US1 - Can be tested independently with custom values
- **User Story 3 (P1)**: Depends on US1 for basic deployment - Adds ingress routing ✅ REQUIRED FOR MVP
- **User Story 4 (P3)**: Depends on US1 for initial deployment - Tests upgrade scenarios
- **User Story 5 (P3)**: Depends on US1 for deployment - Adds resource constraints

### Within Each User Story

- **US1**: ConfigMaps/Secrets (T008-T015) → Deployments (T016-T017) → Health Probes (T022-T025) → Deploy & Verify (T028-T031)
- **US2**: Define values (T032-T033) → Update templates (T034-T037) → Test upgrade (T040-T041)
- **US3**: Ingress template (T042-T045) → Minikube setup (T046-T048) → Verify access (T049-T051)
- **US4**: Image tags (T052-T055) → Rolling strategy (T056-T057) → Test upgrade/rollback (T058-T062)
- **US5**: Define resources (T063-T066) → Update deployments (T067-T068) → Verify limits (T069-T071)

### Parallel Opportunities

**Phase 1 (Setup)**: All tasks T002-T007 can run in parallel (different files)

**Phase 2 (Foundational)**: All tasks T008-T015 can run in parallel (different templates)

**Phase 3 (US1)**:
- T016, T017 can run in parallel (different charts)
- T022, T023, T024, T025 can run in parallel (different probe configurations)
- T026, T027 can run in parallel (different NOTES files)

**Phase 4 (US2)**:
- T032, T033 can run in parallel (different values files)
- T038, T039 can run in parallel (different example files)

**Phase 5 (US3)**: Most tasks sequential (ingress configuration → testing)

**Phase 6 (US4)**:
- T052, T053, T054, T055, T056, T057 can run in parallel (chart updates)

**Phase 7 (US5)**:
- T063, T064, T065, T066 can run in parallel (values configuration)

**Phase 8 (Polish)**:
- All documentation tasks T072-T079 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all chart structure tasks together:
Task: "Create Chart.yaml for frontend chart in charts/frontend/Chart.yaml"
Task: "Create Chart.yaml for backend chart in charts/backend/Chart.yaml"
Task: "Create values.yaml for frontend chart in charts/frontend/values.yaml"
Task: "Create values.yaml for backend chart in charts/backend/values.yaml"

# Launch all ConfigMap/Secret templates together:
Task: "Create ConfigMap template for frontend in charts/frontend/templates/configmap.yaml"
Task: "Create ConfigMap template for backend in charts/backend/templates/configmap.yaml"
Task: "Create Secret template for frontend in charts/frontend/templates/secret.yaml"
Task: "Create Secret template for backend in charts/backend/templates/secret.yaml"

# Launch all health probe configurations together:
Task: "Configure liveness probe for frontend in charts/frontend/templates/deployment.yaml"
Task: "Configure readiness probe for frontend in charts/frontend/templates/deployment.yaml"
Task: "Configure liveness probe for backend in charts/backend/templates/deployment.yaml"
Task: "Configure readiness probe for backend in charts/backend/templates/deployment.yaml"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 3 Only)

**Phase 1**: Setup
1. Complete all T001-T007 (chart structure)

**Phase 2**: Foundational
2. Complete all T008-T015 (ConfigMaps, Secrets, Services)

**Phase 3**: User Story 1 (Basic Deployment)
3. Complete T016-T031 (deployments with health probes)
4. **STOP and VALIDATE**: Verify 4 pods running

**Phase 5**: User Story 3 (Ingress Access)
5. Complete T042-T051 (ingress configuration)
6. **STOP and VALIDATE**: Access app via http://todo.local/

**DEPLOY/DEMO MVP**: Application fully functional via ingress

### Incremental Delivery

1. **Foundation** (Setup + Foundational) → Chart structure ready
2. **MVP** (US1 + US3) → Working application accessible via ingress ✅
3. **Enhanced Config** (US2) → Add configurable values
4. **Safe Updates** (US4) → Add upgrade/rollback capability
5. **Resource Management** (US5) → Add resource limits
6. **Polish** (Phase 8) → Documentation and validation

### Skill Integration

The `helm-chart-builder` skill will be used during implementation:
- **Invocation point**: During `/sp.implement` phase (not during planning)
- **Primary use**: T002-T007 (Chart structure), T016-T017 (Deployments), T012-T013 (Services)
- **Input**: Docker image specs, ports, replicas, environment variables
- **Output**: Complete chart templates ready for customization

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability (US1-US5)
- MVP requires User Story 1 (deployment) + User Story 3 (ingress)
- User Story 2, 4, 5 are enhancements but not required for basic functionality
- Docker images must be built before deployment (T028)
- Minikube must have ingress addon enabled (T046)
- Test each phase checkpoint before proceeding
- Commit after each logical group of tasks
- Use `helm-chart-builder` skill during implementation to accelerate chart generation
- All paths assume repository root is C:/Users/pc1/Desktop/full-stack-todo

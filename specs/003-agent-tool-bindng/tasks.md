# Tasks: Agent-Tool Binding Management

**Input**: Design documents from `/specs/003-agent-tool-bindng/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in specification. Tests can be added in Polish phase if needed.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project structure**: `src/aiops_tools/` for source code
- Paths follow existing project patterns from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and basic structure for agent-tool binding feature

- [x] T001 Create AgentToolBinding model file in src/aiops_tools/models/agent_binding.py
- [x] T002 Create agent binding schemas file in src/aiops_tools/schemas/agent_binding.py
- [x] T003 Create agent binding endpoints file in src/aiops_tools/api/v1/endpoints/agent_binding.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model and schema infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement AgentToolBinding SQLModel in src/aiops_tools/models/agent_binding.py with fields: id (UUID), agent_id (String 255), tool_id (FK to tools.id with CASCADE delete), created_at, updated_at
- [x] T005 Add unique constraint index on (agent_id, tool_id) in AgentToolBinding model
- [x] T006 Export AgentToolBinding in src/aiops_tools/models/__init__.py
- [x] T007 [P] Create base request schemas (BoundToolsRequest, UnboundToolsRequest, BindToolsRequest) in src/aiops_tools/schemas/agent_binding.py following constitution pagination standards
- [x] T008 [P] Create response schemas (BindingPaginatedData, BindingListResponse, BindToolsResponse, BindingResult) in src/aiops_tools/schemas/agent_binding.py following constitution response format
- [x] T009 Export all binding schemas in src/aiops_tools/schemas/__init__.py
- [x] T010 Create APIRouter for binding endpoints in src/aiops_tools/api/v1/endpoints/agent_binding.py
- [x] T011 Register binding router in src/aiops_tools/api/v1/router.py with prefix /agent-bindng

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Query Bound Tools (Priority: P1) 🎯 MVP

**Goal**: Enable querying all tools currently bound to a specific agent with pagination

**Independent Test**: Call `POST /api/tools/v1/agent-bindng/bound` with an agentId and verify paginated tool list is returned

### Implementation for User Story 1

- [x] T012 [US1] Implement bound tools query endpoint `POST /api/tools/v1/agent-bindng/bound` in src/aiops_tools/api/v1/endpoints/agent_binding.py
- [x] T013 [US1] Implement SQLAlchemy query to join AgentToolBinding with Tool filtered by agent_id and status=active in bound tools endpoint
- [x] T014 [US1] Add pagination logic (page, size, totalElements, totalPages, first, last) following constitution standards
- [x] T015 [US1] Return empty list with totalElements=0 when agent has no bindings (handle gracefully per FR-007)
- [x] T016 [US1] Add input validation for agentId (non-empty, max 255 chars) with clear error messages

**Checkpoint**: User Story 1 complete - can query bound tools for any agent

---

## Phase 4: User Story 2 - Query Unbound Tools (Priority: P2)

**Goal**: Enable querying all active tools that are NOT bound to a specific agent

**Independent Test**: Call `POST /api/tools/v1/agent-bindng/unbound` with an agentId and verify returned tools do not include already-bound tools

### Implementation for User Story 2

- [x] T017 [US2] Implement unbound tools query endpoint `POST /api/tools/v1/agent-bindng/unbound` in src/aiops_tools/api/v1/endpoints/agent_binding.py
- [x] T018 [US2] Implement SQLAlchemy query to select active tools NOT IN agent's bound tool_ids
- [x] T019 [US2] Add pagination logic following constitution standards (reuse pattern from US1)
- [x] T020 [US2] Return all active tools when agent has no bindings (new agent scenario)

**Checkpoint**: User Stories 1 AND 2 complete - can query both bound and unbound tools

---

## Phase 5: User Story 3 - Bind Tools to Agent (Priority: P1)

**Goal**: Enable binding a set of tools to an agent using full replacement semantics

**Independent Test**: Call `POST /api/tools/v1/agent-bindng/bindng` with agentId and toolIds, then verify with bound tools query

### Implementation for User Story 3

- [x] T021 [US3] Implement bind tools endpoint `POST /api/tools/v1/agent-bindng/bindng` in src/aiops_tools/api/v1/endpoints/agent_binding.py
- [x] T022 [US3] Implement tool ID validation - check all toolIds exist and have status=active (FR-005)
- [x] T023 [US3] Return error with list of invalid tool IDs if validation fails (FR-009)
- [x] T024 [US3] Implement deduplication of tool IDs in request (FR-008)
- [x] T025 [US3] Implement full replacement logic: DELETE existing bindings for agent_id, then INSERT new bindings in transaction
- [x] T026 [US3] Handle empty toolIds array to unbind all tools from agent
- [x] T027 [US3] Return BindToolsResponse with agentId, boundToolCount, and toolIds list

**Checkpoint**: All user stories complete - full binding management functionality available

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 Add logging for all binding operations in src/aiops_tools/api/v1/endpoints/agent_binding.py
- [x] T029 Update Swagger documentation tags for Agent Binding endpoints in src/aiops_tools/main.py
- [x] T030 Validate all endpoints against quickstart.md examples using curl commands
- [x] T031 Run database migration to create agent_tool_bindings table (alembic or manual)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US1 and US3 are both P1 priority
  - US2 is P2 priority but can run in parallel with others
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Query Bound Tools - Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Query Unbound Tools - Can start after Foundational - Independent of other stories
- **User Story 3 (P1)**: Bind Tools - Can start after Foundational - Independent but best tested after US1 is complete for verification

### Within Each User Story

- Endpoint implementation before query logic
- Query logic before pagination
- Core functionality before edge case handling

### Parallel Opportunities

- T007 and T008 can run in parallel (different schema sections)
- All user stories can run in parallel after Foundational phase
- T028 and T029 can run in parallel (different files)

---

## Parallel Example: Foundational Phase

```bash
# Launch schema tasks in parallel:
Task: "Create base request schemas in src/aiops_tools/schemas/agent_binding.py"
Task: "Create response schemas in src/aiops_tools/schemas/agent_binding.py"
```

## Parallel Example: User Stories

```bash
# After Foundational complete, launch user stories in parallel:
Task: "[US1] Implement bound tools query endpoint"
Task: "[US2] Implement unbound tools query endpoint"
Task: "[US3] Implement bind tools endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Query Bound Tools)
4. Complete Phase 5: User Story 3 (Bind Tools)
5. **STOP and VALIDATE**: Can now bind tools and verify bindings
6. Deploy/demo if ready

### Full Feature Delivery

1. Complete MVP above
2. Add Phase 4: User Story 2 (Query Unbound Tools)
3. Complete Phase 6: Polish
4. Full binding management functionality available

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Can query bound tools → Demo
3. Add User Story 3 → Can bind tools → Demo (MVP complete!)
4. Add User Story 2 → Can discover unbound tools → Demo
5. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution compliance: POST-only, pagination, response wrapper for all endpoints
- Foreign key with CASCADE ensures binding cleanup when tools are deleted

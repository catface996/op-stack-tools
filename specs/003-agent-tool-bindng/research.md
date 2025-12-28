# Research: Agent-Tool Binding Management

**Feature**: 003-agent-tool-bindng
**Date**: 2025-12-28

## Overview

This document consolidates research findings for implementing the agent-tool binding feature. No critical unknowns were identified in the Technical Context as the feature builds on existing patterns in the codebase.

## Research Topics

### 1. Database Model Pattern

**Decision**: Use SQLModel with a simple join table pattern (AgentToolBinding)

**Rationale**:
- Consistent with existing models (Tool, ToolCategory, ToolExecution)
- SQLModel provides both SQLAlchemy ORM and Pydantic validation
- Simple many-to-many relationship without additional attributes beyond created_at

**Alternatives Considered**:
- Association proxy pattern: Rejected - adds complexity without benefit for this use case
- Separate binding service with Redis: Rejected - overkill for relationship data, PostgreSQL handles this well

### 2. Full Replacement Binding Strategy

**Decision**: Use DELETE + batch INSERT within a transaction

**Rationale**:
- Simplest implementation matching the spec's "full replacement" requirement
- Atomic operation ensures consistency
- Efficient with PostgreSQL's bulk insert capabilities

**Alternatives Considered**:
- UPSERT with diff calculation: Rejected - more complex, no benefit for full replacement semantics
- Soft delete with active flag: Rejected - adds complexity, no audit trail requirement in spec

### 3. Pagination Implementation

**Decision**: Reuse existing `PaginationRequest` and pagination response patterns

**Rationale**:
- Constitution compliance (Principle V)
- Existing schemas in `schemas/tool.py` provide the pattern
- Consistent with `categories/list` and `tools/list` endpoints

**Implementation Details**:
- Create `AgentBindingPaginatedData` for bound tools response
- Create `BindingListRequest` extending `PaginationRequest` with `agentId` field

### 4. Tool Validation on Binding

**Decision**: Validate all tool IDs exist and are active before binding

**Rationale**:
- Spec requirement FR-005 and FR-009
- Prevents orphaned bindings to non-existent tools
- Returns clear error messages listing invalid tool IDs

**Implementation**:
```python
# Query to find invalid tool IDs
invalid_ids = set(requested_tool_ids) - set(valid_tool_ids_from_db)
if invalid_ids:
    raise ValidationError(f"Tool IDs not found: {invalid_ids}")
```

### 5. Agent ID Handling

**Decision**: Accept any non-empty string up to 255 characters as agentId

**Rationale**:
- Spec states: "Agent IDs are managed externally"
- No need to validate against external agent registry
- Simple string field with length constraint

**Validation Rules**:
- Not empty/null
- Max length: 255 characters
- No format restrictions (can be UUID, slug, or any identifier)

### 6. API URL Structure

**Decision**: Use `/api/tools/v1/agent-bindng/` prefix

**Rationale**:
- Follows constitution URL convention
- Groups all binding-related endpoints logically
- Consistent with existing endpoint patterns

**Endpoints**:
- `POST /api/tools/v1/agent-bindng/bound` - Query bound tools
- `POST /api/tools/v1/agent-bindng/unbound` - Query unbound tools
- `POST /api/tools/v1/agent-bindng/bindng` - Bind tools to agent

### 7. Cascade Delete Behavior

**Decision**: ON DELETE CASCADE for tool_id foreign key

**Rationale**:
- When a tool is deleted, its bindings should be automatically removed
- Prevents orphaned binding records
- Matches spec edge case: "binding record should be automatically cleaned up"

## Technology Decisions Summary

| Topic | Decision | Key Reason |
|-------|----------|------------|
| Model | SQLModel table | Consistency with codebase |
| Binding Strategy | DELETE + INSERT | Matches full replacement requirement |
| Pagination | Existing patterns | Constitution compliance |
| Validation | Pre-check all tool IDs | Clear error messages |
| Agent ID | String (255 max) | External management |
| FK Behavior | CASCADE delete | Auto-cleanup |

## No Unknowns Remaining

All technical decisions have been made based on:
1. Existing codebase patterns
2. Constitution requirements
3. Feature specification constraints

Ready to proceed to Phase 1: Design & Contracts.

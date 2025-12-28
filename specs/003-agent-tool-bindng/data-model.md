# Data Model: Agent-Tool Binding

**Feature**: 003-agent-tool-bindng
**Date**: 2025-12-28

## Entity Relationship Diagram

```
┌─────────────────────┐          ┌─────────────────────┐
│       Tool          │          │  AgentToolBinding   │
├─────────────────────┤          ├─────────────────────┤
│ id (PK, UUID)       │◄─────────│ tool_id (FK, UUID)  │
│ name                │    1:N   │ agent_id (String)   │
│ status              │          │ id (PK, UUID)       │
│ ...                 │          │ created_at          │
└─────────────────────┘          │ updated_at          │
                                 └─────────────────────┘
                                        │
                                   Composite Index:
                                   (agent_id, tool_id) UNIQUE
```

## Entities

### AgentToolBinding (NEW)

**Table Name**: `agent_tool_bindings`

**Purpose**: Stores the many-to-many relationship between external agents and tools.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK, NOT NULL | Unique binding record ID |
| agent_id | VARCHAR(255) | NOT NULL, INDEX | External agent identifier |
| tool_id | UUID | FK(tools.id), NOT NULL | Reference to bound tool |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Binding creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes**:
- `idx_agent_tool_bindings_agent_id` on `agent_id` - Fast lookup by agent
- `idx_agent_tool_bindings_agent_tool` on `(agent_id, tool_id)` UNIQUE - Prevent duplicates

**Foreign Keys**:
- `tool_id` → `tools.id` ON DELETE CASCADE

### Tool (EXISTING - Referenced)

The existing `Tool` model is referenced but not modified:

| Column | Relevant for Binding |
|--------|---------------------|
| id | Referenced by AgentToolBinding.tool_id |
| status | Used to filter active tools only |
| name | Returned in query responses |
| display_name | Returned in query responses |
| description | Returned in query responses |

## Validation Rules

### AgentToolBinding

1. **agent_id**:
   - Required (NOT NULL)
   - Maximum length: 255 characters
   - Minimum length: 1 character (non-empty)
   - No format restrictions

2. **tool_id**:
   - Required (NOT NULL)
   - Must reference existing Tool with status = ACTIVE
   - Validated before binding creation

3. **Uniqueness**:
   - Combination of (agent_id, tool_id) must be unique
   - Duplicate tool_ids in binding request are deduplicated

## State Transitions

AgentToolBinding has no explicit state field. Records are either:
- **Exists**: Tool is bound to agent
- **Deleted**: Tool is unbound from agent

Transitions:
- Create binding: Insert new record
- Full replacement: Delete all for agent_id, insert new records
- Tool deleted: Cascade delete removes binding records

## Query Patterns

### Bound Tools for Agent
```sql
SELECT t.* FROM tools t
INNER JOIN agent_tool_bindings b ON t.id = b.tool_id
WHERE b.agent_id = :agent_id AND t.status = 'active'
ORDER BY t.name
LIMIT :size OFFSET :offset
```

### Unbound Tools for Agent
```sql
SELECT t.* FROM tools t
WHERE t.status = 'active'
  AND t.id NOT IN (
    SELECT tool_id FROM agent_tool_bindings WHERE agent_id = :agent_id
  )
ORDER BY t.name
LIMIT :size OFFSET :offset
```

### Bind Tools (Full Replacement)
```sql
BEGIN;
DELETE FROM agent_tool_bindings WHERE agent_id = :agent_id;
INSERT INTO agent_tool_bindings (id, agent_id, tool_id, created_at, updated_at)
VALUES (:id1, :agent_id, :tool_id1, NOW(), NOW()),
       (:id2, :agent_id, :tool_id2, NOW(), NOW()),
       ...;
COMMIT;
```

## Migration Notes

### New Table Creation
```sql
CREATE TABLE agent_tool_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) NOT NULL,
    tool_id UUID NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_tool_bindings_agent_id ON agent_tool_bindings(agent_id);
CREATE UNIQUE INDEX idx_agent_tool_bindings_agent_tool ON agent_tool_bindings(agent_id, tool_id);
```

### Rollback
```sql
DROP TABLE IF EXISTS agent_tool_bindings;
```

# Quickstart: Agent-Tool Binding API

## Overview

This guide demonstrates how to use the Agent-Tool Binding API to manage which tools are available to external agents.

## Prerequisites

- AIOps Tools API running on `http://localhost:8083`
- At least one active tool in the system

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/tools/v1/agent-bindng/bound` | Query tools bound to an agent |
| `POST /api/tools/v1/agent-bindng/unbound` | Query tools NOT bound to an agent |
| `POST /api/tools/v1/agent-bindng/bindng` | Bind tools to an agent (full replacement) |

## Usage Examples

### 1. Query Bound Tools for an Agent

Get all tools currently bound to agent "my-agent-001":

```bash
curl -X POST http://localhost:8083/api/tools/v1/agent-bindng/bound \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "my-agent-001",
    "page": 1,
    "size": 20
  }'
```

**Response** (agent has 2 bound tools):
```json
{
  "code": 0,
  "message": "success",
  "success": true,
  "data": {
    "content": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "k8s_list_pods",
        "displayName": "List Kubernetes Pods",
        "description": "List all pods in a namespace",
        "status": "active"
      },
      {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "db_execute_query",
        "displayName": "Execute Database Query",
        "description": "Execute a SQL query",
        "status": "active"
      }
    ],
    "page": 1,
    "size": 20,
    "totalElements": 2,
    "totalPages": 1,
    "first": true,
    "last": true
  }
}
```

### 2. Query Unbound Tools for an Agent

Get all tools NOT bound to agent "my-agent-001":

```bash
curl -X POST http://localhost:8083/api/tools/v1/agent-bindng/unbound \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "my-agent-001",
    "page": 1,
    "size": 20
  }'
```

**Response** (3 tools available for binding):
```json
{
  "code": 0,
  "message": "success",
  "success": true,
  "data": {
    "content": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "name": "aws_list_ec2",
        "displayName": "List EC2 Instances",
        "status": "active"
      }
    ],
    "page": 1,
    "size": 20,
    "totalElements": 1,
    "totalPages": 1,
    "first": true,
    "last": true
  }
}
```

### 3. Bind Tools to an Agent

Bind specific tools to an agent (replaces all existing bindings):

```bash
curl -X POST http://localhost:8083/api/tools/v1/agent-bindng/bindng \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "my-agent-001",
    "toolIds": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440002"
    ]
  }'
```

**Response**:
```json
{
  "code": 0,
  "message": "success",
  "success": true,
  "data": {
    "agentId": "my-agent-001",
    "boundToolCount": 2,
    "toolIds": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440002"
    ]
  }
}
```

### 4. Unbind All Tools from an Agent

Pass an empty `toolIds` array to unbind all tools:

```bash
curl -X POST http://localhost:8083/api/tools/v1/agent-bindng/bindng \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "my-agent-001",
    "toolIds": []
  }'
```

**Response**:
```json
{
  "code": 0,
  "message": "success",
  "success": true,
  "data": {
    "agentId": "my-agent-001",
    "boundToolCount": 0,
    "toolIds": []
  }
}
```

## Error Handling

### Invalid Tool IDs

If you try to bind non-existent or inactive tools:

```bash
curl -X POST http://localhost:8083/api/tools/v1/agent-bindng/bindng \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "my-agent-001",
    "toolIds": ["invalid-uuid-here"]
  }'
```

**Response**:
```json
{
  "code": 400,
  "message": "Validation failed",
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_TOOL_IDS",
    "message": "Some tool IDs do not exist or are not active",
    "field": "toolIds",
    "suggestion": "Use POST /api/tools/v1/tools/list to see available tools"
  }
}
```

### Empty Agent ID

```json
{
  "code": 422,
  "message": "Request validation failed",
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "field": "agentId",
    "message": "Agent ID is required and cannot be empty"
  }
}
```

## Typical Workflow

1. **List available tools**: `POST /api/tools/v1/tools/list`
2. **Query current bindings**: `POST /api/tools/v1/agent-bindng/bound`
3. **See available tools**: `POST /api/tools/v1/agent-bindng/unbound`
4. **Update bindings**: `POST /api/tools/v1/agent-bindng/bindng`

## Notes

- Agent IDs are strings up to 255 characters (managed externally)
- Only active tools can be bound
- Binding uses full replacement - always specify the complete set of tools
- Duplicate tool IDs in requests are automatically deduplicated

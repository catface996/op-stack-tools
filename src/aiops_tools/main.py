"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from aiops_tools.api.v1.router import api_router
from aiops_tools.core.config import settings
from aiops_tools.core.database import init_db
from aiops_tools.core.redis import close_redis, get_redis


# API Description in Markdown format (matching Spring version style)
API_DESCRIPTION = """
AIOps Tools API 文档 - LLM 工具管理平台

## 功能模块

### 工具管理
- **分类管理**: 工具分类 CRUD、层级分类支持
- **工具管理**: 工具 CRUD、版本控制、状态管理
- **工具执行**: Python 脚本安全执行、30秒超时保护

### LLM 集成
- **工具发现**: OpenAI function calling 格式的工具列表
- **工具调用**: 统一的工具调用接口，支持 JSON 输入输出

## 认证方式

需要认证的接口需在请求头中携带 JWT Token：
```
Authorization: Bearer <token>
```

## API 规范

- 所有业务接口使用 POST 方法
- 请求/响应均为 JSON 格式
- URL 格式: `/api/tools/v1/{module}/{action}`
"""

# OpenAPI tags metadata for better documentation organization
tags_metadata = [
    {
        "name": "Categories",
        "description": "分类管理 - 创建和管理工具分类",
    },
    {
        "name": "Tools",
        "description": "工具管理 - 工具的增删改查、启用/禁用",
    },
    {
        "name": "LLM",
        "description": "LLM 接口 - OpenAI function calling 格式的工具发现和调用",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    await init_db()
    await get_redis()
    yield
    # Shutdown
    await close_redis()


def custom_openapi():
    """Generate custom OpenAPI schema matching Spring version protocol."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AIOps Tools API",
        version="1.0.0",
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=tags_metadata,
    )

    # Add servers (matching Spring version)
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:6060",
            "description": "本地开发环境",
        },
        {
            "url": "https://api.aiops-tools.example.com",
            "description": "生产环境",
        },
    ]

    # Add contact info (matching Spring version)
    openapi_schema["info"]["contact"] = {
        "name": "AIOps Team",
        "email": "aiops@example.com",
    }

    # Add license (matching Spring version - Apache 2.0)
    openapi_schema["info"]["license"] = {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    }

    # Add security scheme (Bearer JWT - matching Spring version)
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Authentication": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT 认证，请在登录接口获取 Token 后填入",
        }
    }

    # Add global security requirement
    openapi_schema["security"] = [{"Bearer Authentication": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app = FastAPI(
    title="AIOps Tools API",
    version="1.0.0",
    description=API_DESCRIPTION,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=None,  # Disable default docs, we'll add custom routes
    redoc_url=None,  # Disable default redoc
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

# Override the openapi method with custom implementation
app.openapi = custom_openapi


# Swagger UI at /swagger-ui.html (matching Spring version URL)
@app.get("/swagger-ui.html", include_in_schema=False)
async def swagger_ui_html():
    """Swagger UI documentation (Spring-compatible URL)."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        title="AIOps Tools API - Swagger UI",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# Also available at /docs for convenience
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Swagger UI documentation."""
    return get_swagger_ui_html(
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        title="AIOps Tools API - Swagger UI",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# OpenAPI JSON at /v3/api-docs (matching Spring version URL)
@app.get("/v3/api-docs", include_in_schema=False)
async def openapi_json():
    """OpenAPI JSON specification (Spring-compatible URL)."""
    return app.openapi()


# OpenAPI YAML at /v3/api-docs.yaml (matching Spring version URL)
@app.get("/v3/api-docs.yaml", include_in_schema=False)
async def openapi_yaml():
    """OpenAPI YAML specification (Spring-compatible URL)."""
    import yaml
    return yaml.dump(app.openapi(), allow_unicode=True, default_flow_style=False)


# ReDoc at /redoc
@app.get("/redoc", include_in_schema=False)
async def custom_redoc_html():
    """ReDoc documentation."""
    return get_redoc_html(
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        title="AIOps Tools API - ReDoc",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": "AIOps Tools API",
        "version": "1.0.0",
        "docs": "/docs",
        "swagger-ui": "/swagger-ui.html",
        "redoc": "/redoc",
        "openapi-json": "/v3/api-docs",
        "openapi-yaml": "/v3/api-docs.yaml",
        "openapi": f"{settings.api_v1_prefix}/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "aiops_tools.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

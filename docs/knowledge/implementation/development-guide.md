# MIRIX 开发实施指导文档

## 📋 文档概述

本文档为MIRIX项目的开发实施指导，提供从环境搭建到具体实现的完整开发指南。面向开发人员，确保能够快速上手并高效开发MIRIX系统。

---

## 🎯 第一层：开发环境大纲

### 开发环境全景图
```mermaid
graph TB
    subgraph "开发环境"
        A[Python 3.11+] --> B[虚拟环境]
        B --> C[依赖管理]
        C --> D[开发工具]
    end
    
    subgraph "数据库环境"
        E[PostgreSQL 16+] --> F[pgvector扩展]
        G[Redis 7+] --> H[缓存配置]
    end
    
    subgraph "开发工具链"
        I[IDE配置] --> J[代码质量]
        J --> K[测试框架]
        K --> L[调试工具]
    end
    
    subgraph "部署环境"
        M[Docker] --> N[Docker Compose]
        N --> O[环境变量]
        O --> P[配置管理]
    end
```

### 核心开发模块
- **环境配置模块**：Python环境、数据库环境、开发工具配置
- **代码开发模块**：核心功能实现、API开发、前端开发
- **测试验证模块**：单元测试、集成测试、端到端测试
- **部署运维模块**：容器化部署、监控配置、日志管理

### 开发流程导航
- **环境搭建流程**：系统要求 → 环境安装 → 配置验证 → 开发准备
- **功能开发流程**：需求分析 → 设计实现 → 代码编写 → 测试验证
- **部署发布流程**：构建打包 → 环境部署 → 功能验证 → 监控运维

---

## 🏗️ 第二层：技术实施设计

### 开发环境架构设计

#### 本地开发环境
```python
# config/development.py
import os
from pathlib import Path

class DevelopmentConfig:
    """开发环境配置"""
    
    # 基础配置
    DEBUG = True
    TESTING = False
    
    # 数据库配置
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://mirix:mirix@localhost:5432/mirix_dev"
    )
    
    # Redis配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # 日志配置
    LOG_LEVEL = "DEBUG"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 开发工具配置
    RELOAD = True
    HOT_RELOAD = True
    AUTO_MIGRATION = True
    
    @classmethod
    def validate(cls):
        """验证配置"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"缺少必需的环境变量: {', '.join(missing_vars)}")
```

#### 开发工具集成
```python
# tools/dev_tools.py
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

class DevTools:
    """开发工具管理"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.venv_path = project_root / "venv"
    
    def setup_environment(self):
        """设置开发环境"""
        print("🚀 设置MIRIX开发环境...")
        
        # 创建虚拟环境
        self._create_virtual_env()
        
        # 安装依赖
        self._install_dependencies()
        
        # 设置pre-commit钩子
        self._setup_pre_commit()
        
        # 初始化数据库
        self._init_database()
        
        print("✅ 开发环境设置完成！")
    
    def _create_virtual_env(self):
        """创建虚拟环境"""
        if not self.venv_path.exists():
            print("📦 创建Python虚拟环境...")
            subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], check=True)
    
    def _install_dependencies(self):
        """安装依赖"""
        print("📚 安装项目依赖...")
        pip_path = self.venv_path / "Scripts" / "pip.exe"  # Windows
        if not pip_path.exists():
            pip_path = self.venv_path / "bin" / "pip"  # Linux/Mac
        
        # 安装生产依赖
        subprocess.run([
            str(pip_path), "install", "-r", "requirements.txt"
        ], check=True)
        
        # 安装开发依赖
        subprocess.run([
            str(pip_path), "install", "-r", "requirements-dev.txt"
        ], check=True)
    
    def _setup_pre_commit(self):
        """设置pre-commit钩子"""
        print("🔧 设置代码质量检查...")
        subprocess.run([
            str(self.venv_path / "Scripts" / "pre-commit"), "install"
        ], check=True)
    
    def _init_database(self):
        """初始化数据库"""
        print("🗄️ 初始化数据库...")
        # 这里添加数据库初始化逻辑
        pass
    
    def run_tests(self, test_path: Optional[str] = None):
        """运行测试"""
        pytest_path = self.venv_path / "Scripts" / "pytest.exe"
        cmd = [str(pytest_path), "-v", "--cov=mirix"]
        
        if test_path:
            cmd.append(test_path)
        else:
            cmd.append("tests/")
        
        subprocess.run(cmd, check=True)
    
    def run_linting(self):
        """运行代码检查"""
        print("🔍 运行代码质量检查...")
        
        # 运行flake8
        subprocess.run([
            str(self.venv_path / "Scripts" / "flake8"), "mirix/", "tests/"
        ], check=True)
        
        # 运行pylint
        subprocess.run([
            str(self.venv_path / "Scripts" / "pylint"), "mirix/"
        ], check=True)
        
        # 运行mypy
        subprocess.run([
            str(self.venv_path / "Scripts" / "mypy"), "mirix/"
        ], check=True)
    
    def format_code(self):
        """格式化代码"""
        print("🎨 格式化代码...")
        
        # 使用black格式化
        subprocess.run([
            str(self.venv_path / "Scripts" / "black"), "mirix/", "tests/"
        ], check=True)
        
        # 使用isort整理导入
        subprocess.run([
            str(self.venv_path / "Scripts" / "isort"), "mirix/", "tests/"
        ], check=True)
```

### 数据库开发设计

#### 数据库迁移管理
```python
# migrations/migration_manager.py
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import text
from mirix.orm.base import get_async_session

class MigrationManager:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.migrations_dir = Path("migrations/versions")
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_migration(self, name: str, description: str = ""):
        """创建新的迁移文件"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.py"
        filepath = self.migrations_dir / filename
        
        migration_template = f'''"""
{description}

Revision ID: {timestamp}
Create Date: {datetime.utcnow().isoformat()}
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """升级数据库结构"""
    pass

def downgrade():
    """回滚数据库结构"""
    pass
'''
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(migration_template)
        
        self.logger.info(f"创建迁移文件: {filename}")
        return filepath
    
    async def run_migrations(self):
        """运行数据库迁移"""
        async with get_async_session() as session:
            # 创建迁移历史表
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_history (
                    id SERIAL PRIMARY KEY,
                    revision VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            
            # 获取已应用的迁移
            result = await session.execute(text(
                "SELECT revision FROM migration_history ORDER BY applied_at"
            ))
            applied_migrations = {row[0] for row in result.fetchall()}
            
            # 获取所有迁移文件
            migration_files = sorted(self.migrations_dir.glob("*.py"))
            
            for migration_file in migration_files:
                revision = migration_file.stem.split('_')[0]
                
                if revision not in applied_migrations:
                    await self._apply_migration(session, migration_file, revision)
            
            await session.commit()
    
    async def _apply_migration(self, session, migration_file: Path, revision: str):
        """应用单个迁移"""
        self.logger.info(f"应用迁移: {migration_file.name}")
        
        # 动态导入迁移模块
        spec = importlib.util.spec_from_file_location(
            f"migration_{revision}", migration_file
        )
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        # 执行升级函数
        if hasattr(migration_module, 'upgrade'):
            migration_module.upgrade()
        
        # 记录迁移历史
        await session.execute(text("""
            INSERT INTO migration_history (revision, description)
            VALUES (:revision, :description)
        """), {
            "revision": revision,
            "description": getattr(migration_module, '__doc__', '').strip()
        })
```

#### 开发数据种子
```python
# seeds/dev_seeds.py
import asyncio
import logging
from datetime import datetime, timedelta
from mirix.orm.base import get_async_session
from mirix.orm.user import User
from mirix.orm.agent import Agent
from mirix.orm.message import Message

class DevSeeds:
    """开发环境数据种子"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def seed_all(self):
        """创建所有种子数据"""
        self.logger.info("🌱 开始创建开发种子数据...")
        
        async with get_async_session() as session:
            # 创建测试用户
            users = await self._create_test_users(session)
            
            # 创建测试智能体
            agents = await self._create_test_agents(session, users)
            
            # 创建测试消息
            await self._create_test_messages(session, agents)
            
            # 创建测试记忆
            await self._create_test_memories(session, agents)
            
            await session.commit()
        
        self.logger.info("✅ 开发种子数据创建完成！")
    
    async def _create_test_users(self, session) -> List[User]:
        """创建测试用户"""
        users_data = [
            {
                "username": "admin",
                "email": "admin@mirix.dev",
                "full_name": "系统管理员",
                "is_active": True,
                "is_superuser": True,
            },
            {
                "username": "developer",
                "email": "dev@mirix.dev", 
                "full_name": "开发者",
                "is_active": True,
                "is_superuser": False,
            },
            {
                "username": "tester",
                "email": "test@mirix.dev",
                "full_name": "测试用户",
                "is_active": True,
                "is_superuser": False,
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data)
            session.add(user)
            users.append(user)
        
        await session.flush()  # 获取ID
        return users
    
    async def _create_test_agents(self, session, users: List[User]) -> List[Agent]:
        """创建测试智能体"""
        agents_data = [
            {
                "name": "助手智能体",
                "agent_type": "assistant",
                "description": "通用助手智能体，用于日常对话和任务处理",
                "user_id": users[0].id,
                "is_active": True,
            },
            {
                "name": "代码智能体", 
                "agent_type": "code_assistant",
                "description": "专门用于代码生成和编程辅助的智能体",
                "user_id": users[1].id,
                "is_active": True,
            },
            {
                "name": "分析智能体",
                "agent_type": "analyst",
                "description": "数据分析和报告生成智能体",
                "user_id": users[1].id,
                "is_active": True,
            }
        ]
        
        agents = []
        for agent_data in agents_data:
            agent = Agent(**agent_data)
            session.add(agent)
            agents.append(agent)
        
        await session.flush()
        return agents
    
    async def _create_test_messages(self, session, agents: List[Agent]):
        """创建测试消息"""
        messages_data = [
            {
                "role": "user",
                "content": "你好，请介绍一下MIRIX系统",
                "agent_id": agents[0].id,
            },
            {
                "role": "assistant", 
                "content": "MIRIX是一个多智能体系统，支持多种AI模型和工具集成...",
                "agent_id": agents[0].id,
            },
            {
                "role": "user",
                "content": "请帮我生成一个Python函数来计算斐波那契数列",
                "agent_id": agents[1].id,
            },
            {
                "role": "assistant",
                "content": "```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```",
                "agent_id": agents[1].id,
            }
        ]
        
        for msg_data in messages_data:
            message = Message(**msg_data)
            session.add(message)
```

### API开发设计

#### API开发框架
```python
# api/base.py
from typing import Any, Dict, List, Optional, Type, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from mirix.orm.base import get_async_session
from mirix.services.auth import get_current_user
from mirix.schemas.user import User

T = TypeVar('T', bound=BaseModel)

class BaseAPI:
    """API基础类"""
    
    def __init__(self, prefix: str, tags: List[str]):
        self.router = APIRouter(prefix=prefix, tags=tags)
        self.security = HTTPBearer()
    
    def get_router(self) -> APIRouter:
        """获取路由器"""
        return self.router
    
    async def get_db(self) -> AsyncSession:
        """获取数据库会话"""
        async with get_async_session() as session:
            yield session
    
    async def get_current_user_dependency(
        self, 
        token: str = Depends(HTTPBearer()),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """获取当前用户依赖"""
        return await get_current_user(token.credentials, db)
    
    def create_endpoint(
        self,
        path: str,
        methods: List[str],
        response_model: Optional[Type[T]] = None,
        status_code: int = status.HTTP_200_OK,
        require_auth: bool = True
    ):
        """创建API端点装饰器"""
        def decorator(func):
            # 构建依赖列表
            dependencies = []
            if require_auth:
                dependencies.append(Depends(self.get_current_user_dependency))
            
            # 注册路由
            for method in methods:
                self.router.add_api_route(
                    path=path,
                    endpoint=func,
                    methods=[method.upper()],
                    response_model=response_model,
                    status_code=status_code,
                    dependencies=dependencies
                )
            
            return func
        return decorator

# 使用示例
class AgentAPI(BaseAPI):
    """智能体API"""
    
    def __init__(self):
        super().__init__(prefix="/api/v1/agents", tags=["agents"])
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        
        @self.create_endpoint("/", ["GET"], response_model=List[AgentResponse])
        async def list_agents(
            self,
            current_user: User = Depends(self.get_current_user_dependency),
            db: AsyncSession = Depends(self.get_db)
        ):
            """获取智能体列表"""
            # 实现逻辑
            pass
        
        @self.create_endpoint("/", ["POST"], response_model=AgentResponse, status_code=201)
        async def create_agent(
            self,
            agent_data: AgentCreateRequest,
            current_user: User = Depends(self.get_current_user_dependency),
            db: AsyncSession = Depends(self.get_db)
        ):
            """创建智能体"""
            # 实现逻辑
            pass
```

---

## 🛠️ 第三层：具体实现指导

### 环境配置实现

#### 1. 系统要求检查
```bash
# scripts/check_requirements.ps1
# Windows PowerShell脚本

Write-Host "🔍 检查MIRIX系统要求..." -ForegroundColor Green

# 检查Python版本
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.1[1-9]") {
    Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ 需要Python 3.11或更高版本，当前: $pythonVersion" -ForegroundColor Red
    exit 1
}

# 检查Git
try {
    $gitVersion = git --version
    Write-Host "✅ Git版本: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未安装Git" -ForegroundColor Red
    exit 1
}

# 检查Docker
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker版本: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 未安装Docker（可选）" -ForegroundColor Yellow
}

# 检查PostgreSQL
try {
    $pgVersion = psql --version
    Write-Host "✅ PostgreSQL版本: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ 未安装PostgreSQL（将使用Docker）" -ForegroundColor Yellow
}

Write-Host "🎉 系统要求检查完成！" -ForegroundColor Green
```

#### 2. 快速启动脚本
```bash
# scripts/quick_start.ps1
param(
    [switch]$UseDocker = $false,
    [switch]$SkipTests = $false
)

Write-Host "🚀 MIRIX快速启动脚本" -ForegroundColor Cyan

# 设置错误处理
$ErrorActionPreference = "Stop"

try {
    # 1. 检查系统要求
    Write-Host "1️⃣ 检查系统要求..." -ForegroundColor Yellow
    .\scripts\check_requirements.ps1

    # 2. 创建虚拟环境
    Write-Host "2️⃣ 创建Python虚拟环境..." -ForegroundColor Yellow
    if (!(Test-Path "venv")) {
        python -m venv venv
    }
    
    # 激活虚拟环境
    .\venv\Scripts\Activate.ps1

    # 3. 安装依赖
    Write-Host "3️⃣ 安装项目依赖..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

    # 4. 环境变量配置
    Write-Host "4️⃣ 配置环境变量..." -ForegroundColor Yellow
    if (!(Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "⚠️ 请编辑.env文件配置必要的环境变量" -ForegroundColor Yellow
    }

    # 5. 启动数据库
    if ($UseDocker) {
        Write-Host "5️⃣ 启动Docker数据库..." -ForegroundColor Yellow
        docker-compose up -d postgres redis
        
        # 等待数据库启动
        Write-Host "等待数据库启动..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
    }

    # 6. 数据库迁移
    Write-Host "6️⃣ 运行数据库迁移..." -ForegroundColor Yellow
    python -m alembic upgrade head

    # 7. 创建种子数据
    Write-Host "7️⃣ 创建开发种子数据..." -ForegroundColor Yellow
    python -c "
import asyncio
from seeds.dev_seeds import DevSeeds
asyncio.run(DevSeeds().seed_all())
"

    # 8. 运行测试
    if (!$SkipTests) {
        Write-Host "8️⃣ 运行测试..." -ForegroundColor Yellow
        python -m pytest tests/ -v --tb=short
    }

    # 9. 启动开发服务器
    Write-Host "9️⃣ 启动开发服务器..." -ForegroundColor Yellow
    Write-Host "🎉 MIRIX开发环境启动成功！" -ForegroundColor Green
    Write-Host "📱 API文档: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "🔧 管理界面: http://localhost:8000/admin" -ForegroundColor Cyan
    
    # 启动服务器
    python -m uvicorn mirix.main:app --reload --host 0.0.0.0 --port 8000

} catch {
    Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
```

#### 3. 开发环境配置文件
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: mirix_dev
      POSTGRES_USER: mirix
      POSTGRES_PASSWORD: mirix_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mirix -d mirix_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  mirix-api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://mirix:mirix_dev_password@postgres:5432/mirix_dev
      - REDIS_URL=redis://redis:6379/0
      - DEBUG=true
    volumes:
      - .:/app
      - /app/venv  # 排除虚拟环境
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn mirix.main:app --reload --host 0.0.0.0 --port 8000

  mirix-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - CHOKIDAR_USEPOLLING=true
    command: npm start

volumes:
  postgres_dev_data:
  redis_dev_data:
```

### 核心功能实现示例

#### 1. 智能体管理实现
```python
# mirix/services/agent_service.py
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from mirix.orm.agent import Agent
from mirix.orm.user import User
from mirix.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from mirix.services.memory_service import MemoryService
from mirix.services.llm_service import LLMService

class AgentService:
    """智能体服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.memory_service = MemoryService(db)
        self.llm_service = LLMService()
    
    async def create_agent(
        self, 
        agent_data: AgentCreate, 
        user_id: int
    ) -> AgentResponse:
        """创建智能体"""
        self.logger.info(f"创建智能体: {agent_data.name}")
        
        # 创建智能体实例
        agent = Agent(
            name=agent_data.name,
            agent_type=agent_data.agent_type,
            description=agent_data.description,
            system_prompt=agent_data.system_prompt,
            model_config=agent_data.model_config,
            user_id=user_id,
            is_active=True
        )
        
        self.db.add(agent)
        await self.db.flush()  # 获取ID
        
        # 初始化智能体记忆系统
        await self.memory_service.initialize_agent_memory(agent.id)
        
        # 初始化核心记忆
        if agent_data.core_memory:
            await self.memory_service.update_core_memory(
                agent.id, 
                agent_data.core_memory
            )
        
        await self.db.commit()
        await self.db.refresh(agent)
        
        self.logger.info(f"智能体创建成功: {agent.id}")
        return AgentResponse.from_orm(agent)
    
    async def get_agent(self, agent_id: int, user_id: int) -> Optional[AgentResponse]:
        """获取智能体"""
        query = select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == user_id,
            Agent.is_deleted == False
        ).options(
            selectinload(Agent.messages),
            selectinload(Agent.memory_items)
        )
        
        result = await self.db.execute(query)
        agent = result.scalar_one_or_none()
        
        if not agent:
            return None
        
        return AgentResponse.from_orm(agent)
    
    async def list_agents(
        self, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None
    ) -> List[AgentResponse]:
        """获取智能体列表"""
        query = select(Agent).where(
            Agent.user_id == user_id,
            Agent.is_deleted == False
        )
        
        if agent_type:
            query = query.where(Agent.agent_type == agent_type)
        
        query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())
        
        result = await self.db.execute(query)
        agents = result.scalars().all()
        
        return [AgentResponse.from_orm(agent) for agent in agents]
    
    async def update_agent(
        self, 
        agent_id: int, 
        agent_data: AgentUpdate, 
        user_id: int
    ) -> Optional[AgentResponse]:
        """更新智能体"""
        # 检查权限
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            return None
        
        # 构建更新数据
        update_data = agent_data.dict(exclude_unset=True)
        
        # 执行更新
        query = update(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == user_id
        ).values(**update_data)
        
        await self.db.execute(query)
        await self.db.commit()
        
        # 返回更新后的智能体
        return await self.get_agent(agent_id, user_id)
    
    async def delete_agent(self, agent_id: int, user_id: int) -> bool:
        """删除智能体（软删除）"""
        query = update(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == user_id
        ).values(is_deleted=True)
        
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def chat_with_agent(
        self, 
        agent_id: int, 
        message: str, 
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """与智能体对话"""
        # 获取智能体
        agent = await self.get_agent(agent_id, user_id)
        if not agent:
            raise ValueError("智能体不存在")
        
        # 获取对话历史
        conversation_history = await self.memory_service.get_conversation_history(
            agent_id, limit=10
        )
        
        # 获取相关记忆
        relevant_memories = await self.memory_service.search_memories(
            agent_id, message, limit=5
        )
        
        # 构建提示词
        system_prompt = self._build_system_prompt(
            agent, relevant_memories, context
        )
        
        # 调用LLM
        response = await self.llm_service.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history,
                {"role": "user", "content": message}
            ],
            model=agent.model_config.get("model", "gpt-3.5-turbo"),
            **agent.model_config.get("parameters", {})
        )
        
        # 保存对话记录
        await self.memory_service.save_conversation(
            agent_id, 
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]
        )
        
        # 更新记忆
        await self.memory_service.update_episodic_memory(
            agent_id, message, response
        )
        
        return response
    
    def _build_system_prompt(
        self, 
        agent: AgentResponse, 
        memories: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建系统提示词"""
        prompt_parts = [agent.system_prompt or "你是一个有用的AI助手。"]
        
        # 添加核心记忆
        if agent.core_memory:
            prompt_parts.append(f"\n核心记忆:\n{agent.core_memory}")
        
        # 添加相关记忆
        if memories:
            memory_text = "\n".join([
                f"- {memory['content']}" for memory in memories
            ])
            prompt_parts.append(f"\n相关记忆:\n{memory_text}")
        
        # 添加上下文
        if context:
            context_text = "\n".join([
                f"{key}: {value}" for key, value in context.items()
            ])
            prompt_parts.append(f"\n当前上下文:\n{context_text}")
        
        return "\n".join(prompt_parts)
```

#### 2. 消息流处理实现
```python
# mirix/services/message_service.py
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from datetime import datetime

from mirix.orm.message import Message
from mirix.orm.agent import Agent
from mirix.services.agent_service import AgentService
from mirix.services.llm_service import LLMService

class MessageService:
    """消息服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.agent_service = AgentService(db)
        self.llm_service = LLMService()
    
    async def stream_chat(
        self,
        agent_id: int,
        message: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话"""
        try:
            # 发送开始事件
            yield {
                "event": "start",
                "data": {
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # 获取智能体
            agent = await self.agent_service.get_agent(agent_id, user_id)
            if not agent:
                yield {
                    "event": "error",
                    "data": {"message": "智能体不存在"}
                }
                return
            
            # 发送思考事件
            yield {
                "event": "thinking",
                "data": {"message": "正在思考..."}
            }
            
            # 获取对话上下文
            conversation_history = await self._get_conversation_context(
                agent_id, message
            )
            
            # 流式调用LLM
            response_chunks = []
            async for chunk in self.llm_service.stream_chat_completion(
                messages=conversation_history,
                model=agent.model_config.get("model", "gpt-3.5-turbo")
            ):
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        content = delta["content"]
                        response_chunks.append(content)
                        
                        # 发送内容块
                        yield {
                            "event": "content",
                            "data": {"content": content}
                        }
            
            # 完整响应
            full_response = "".join(response_chunks)
            
            # 保存消息
            await self._save_conversation(
                agent_id, message, full_response, user_id
            )
            
            # 发送完成事件
            yield {
                "event": "complete",
                "data": {
                    "message": full_response,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"流式对话错误: {e}")
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }
    
    async def _get_conversation_context(
        self, 
        agent_id: int, 
        current_message: str
    ) -> List[Dict[str, str]]:
        """获取对话上下文"""
        # 获取智能体信息
        agent = await self.agent_service.get_agent(agent_id, user_id=None)
        
        # 获取历史消息
        query = select(Message).where(
            Message.agent_id == agent_id,
            Message.is_deleted == False
        ).order_by(Message.created_at.desc()).limit(10)
        
        result = await self.db.execute(query)
        messages = result.scalars().all()
        
        # 构建对话历史
        conversation = []
        
        # 添加系统提示
        if agent and agent.system_prompt:
            conversation.append({
                "role": "system",
                "content": agent.system_prompt
            })
        
        # 添加历史消息（倒序）
        for msg in reversed(messages):
            conversation.append({
                "role": msg.role,
                "content": msg.content or msg.text
            })
        
        # 添加当前消息
        conversation.append({
            "role": "user",
            "content": current_message
        })
        
        return conversation
    
    async def _save_conversation(
        self,
        agent_id: int,
        user_message: str,
        assistant_response: str,
        user_id: int
    ):
        """保存对话记录"""
        # 保存用户消息
        user_msg = Message(
            role="user",
            content=user_message,
            agent_id=agent_id,
            sender_id=user_id
        )
        self.db.add(user_msg)
        
        # 保存助手响应
        assistant_msg = Message(
            role="assistant",
            content=assistant_response,
            agent_id=agent_id
        )
        self.db.add(assistant_msg)
        
        await self.db.commit()
```

### 测试实现示例

#### 1. 单元测试
```python
# tests/test_agent_service.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from mirix.services.agent_service import AgentService
from mirix.schemas.agent import AgentCreate, AgentResponse
from mirix.orm.agent import Agent

class TestAgentService:
    """智能体服务测试"""
    
    @pytest.fixture
    async def db_session(self):
        """数据库会话fixture"""
        session = AsyncMock(spec=AsyncSession)
        return session
    
    @pytest.fixture
    def agent_service(self, db_session):
        """智能体服务fixture"""
        return AgentService(db_session)
    
    @pytest.fixture
    def sample_agent_data(self):
        """示例智能体数据"""
        return AgentCreate(
            name="测试智能体",
            agent_type="assistant",
            description="用于测试的智能体",
            system_prompt="你是一个测试助手",
            model_config={"model": "gpt-3.5-turbo"}
        )
    
    async def test_create_agent_success(
        self, 
        agent_service, 
        sample_agent_data, 
        db_session
    ):
        """测试成功创建智能体"""
        # 模拟数据库操作
        db_session.flush = AsyncMock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()
        
        # 模拟记忆服务
        agent_service.memory_service.initialize_agent_memory = AsyncMock()
        agent_service.memory_service.update_core_memory = AsyncMock()
        
        # 执行测试
        result = await agent_service.create_agent(sample_agent_data, user_id=1)
        
        # 验证结果
        assert isinstance(result, AgentResponse)
        assert result.name == sample_agent_data.name
        assert result.agent_type == sample_agent_data.agent_type
        
        # 验证数据库操作
        db_session.add.assert_called_once()
        db_session.flush.assert_called_once()
        db_session.commit.assert_called_once()
    
    async def test_get_agent_not_found(self, agent_service, db_session):
        """测试获取不存在的智能体"""
        # 模拟数据库查询返回None
        db_session.execute = AsyncMock()
        db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # 执行测试
        result = await agent_service.get_agent(999, user_id=1)
        
        # 验证结果
        assert result is None
    
    async def test_chat_with_agent(self, agent_service, db_session):
        """测试与智能体对话"""
        # 模拟智能体
        mock_agent = AgentResponse(
            id=1,
            name="测试智能体",
            agent_type="assistant",
            system_prompt="你是一个测试助手",
            model_config={"model": "gpt-3.5-turbo"}
        )
        
        # 模拟服务方法
        agent_service.get_agent = AsyncMock(return_value=mock_agent)
        agent_service.memory_service.get_conversation_history = AsyncMock(
            return_value=[]
        )
        agent_service.memory_service.search_memories = AsyncMock(
            return_value=[]
        )
        agent_service.llm_service.chat_completion = AsyncMock(
            return_value="这是测试响应"
        )
        agent_service.memory_service.save_conversation = AsyncMock()
        agent_service.memory_service.update_episodic_memory = AsyncMock()
        
        # 执行测试
        response = await agent_service.chat_with_agent(
            agent_id=1,
            message="你好",
            user_id=1
        )
        
        # 验证结果
        assert response == "这是测试响应"
        
        # 验证调用
        agent_service.llm_service.chat_completion.assert_called_once()
        agent_service.memory_service.save_conversation.assert_called_once()

# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

#### 2. 集成测试
```python
# tests/integration/test_api_integration.py
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from mirix.main import app
from mirix.orm.base import get_async_session
from tests.conftest import override_get_db, test_db

class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture
    async def client(self):
        """测试客户端"""
        app.dependency_overrides[get_async_session] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    @pytest.fixture
    async def auth_headers(self, client):
        """认证头"""
        # 创建测试用户并获取token
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        # 注册用户
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 登录获取token
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    async def test_agent_crud_flow(self, client, auth_headers):
        """测试智能体CRUD完整流程"""
        # 1. 创建智能体
        agent_data = {
            "name": "集成测试智能体",
            "agent_type": "assistant",
            "description": "用于集成测试",
            "system_prompt": "你是一个测试助手"
        }
        
        response = await client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        created_agent = response.json()
        agent_id = created_agent["id"]
        assert created_agent["name"] == agent_data["name"]
        
        # 2. 获取智能体
        response = await client.get(
            f"/api/v1/agents/{agent_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        agent = response.json()
        assert agent["id"] == agent_id
        assert agent["name"] == agent_data["name"]
        
        # 3. 更新智能体
        update_data = {"description": "更新后的描述"}
        response = await client.put(
            f"/api/v1/agents/{agent_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        updated_agent = response.json()
        assert updated_agent["description"] == update_data["description"]
        
        # 4. 与智能体对话
        chat_data = {"message": "你好，请介绍一下自己"}
        response = await client.post(
            f"/api/v1/agents/{agent_id}/chat",
            json=chat_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        chat_response = response.json()
        assert "response" in chat_response
        assert len(chat_response["response"]) > 0
        
        # 5. 获取对话历史
        response = await client.get(
            f"/api/v1/agents/{agent_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        messages = response.json()
        assert len(messages) >= 2  # 用户消息 + 助手响应
        
        # 6. 删除智能体
        response = await client.delete(
            f"/api/v1/agents/{agent_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # 7. 验证删除
        response = await client.get(
            f"/api/v1/agents/{agent_id}",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    async def test_streaming_chat(self, client, auth_headers):
        """测试流式对话"""
        # 先创建智能体
        agent_data = {
            "name": "流式测试智能体",
            "agent_type": "assistant"
        }
        
        response = await client.post(
            "/api/v1/agents/",
            json=agent_data,
            headers=auth_headers
        )
        agent_id = response.json()["id"]
        
        # 测试流式对话
        chat_data = {"message": "请写一首关于春天的诗"}
        
        async with client.stream(
            "POST",
            f"/api/v1/agents/{agent_id}/stream-chat",
            json=chat_data,
            headers=auth_headers
        ) as response:
            assert response.status_code == 200
            
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = line[6:]  # 去掉 "data: " 前缀
                    if event_data != "[DONE]":
                        events.append(json.loads(event_data))
            
            # 验证事件序列
            assert len(events) > 0
            assert events[0]["event"] == "start"
            assert events[-1]["event"] == "complete"
            
            # 验证包含内容事件
            content_events = [e for e in events if e["event"] == "content"]
            assert len(content_events) > 0
```

### 部署配置实现

#### 1. 生产环境Dockerfile
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
COPY requirements-prod.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# 生产阶段
FROM python:3.11-slim as production

# 创建非root用户
RUN groupadd -r mirix && useradd -r -g mirix mirix

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 从builder阶段复制Python包
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY . .

# 设置权限
RUN chown -R mirix:mirix /app

# 切换到非root用户
USER mirix

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "mirix.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### 2. Kubernetes部署配置
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mirix-api
  labels:
    app: mirix-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mirix-api
  template:
    metadata:
      labels:
        app: mirix-api
    spec:
      containers:
      - name: mirix-api
        image: mirix/mirix:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mirix-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mirix-secrets
              key: redis-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: mirix-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: mirix-api-service
spec:
  selector:
    app: mirix-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mirix-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.mirix.com
    secretName: mirix-tls
  rules:
  - host: api.mirix.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mirix-api-service
            port:
              number: 80
```

---

## 📚 总结

MIRIX开发实施指导文档提供了完整的三层开发指南：

1. **第一层 - 开发环境大纲**：环境全景图、核心模块、开发流程导航
2. **第二层 - 技术实施设计**：开发环境架构、数据库设计、API开发框架
3. **第三层 - 具体实现指导**：环境配置、功能实现、测试示例、部署配置

通过这个开发指导，开发团队可以：
- **快速搭建**：使用脚本快速搭建完整的开发环境
- **规范开发**：遵循统一的代码规范和开发流程
- **高效测试**：使用完整的测试框架确保代码质量
- **便捷部署**：使用容器化和K8s实现自动化部署

该指导确保了MIRIX项目的：
- **开发效率**：标准化的开发环境和工具链
- **代码质量**：完整的测试覆盖和代码检查
- **部署可靠**：自动化的构建和部署流程
- **团队协作**：统一的开发规范和最佳实践
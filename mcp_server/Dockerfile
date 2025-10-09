# MCP Server Docker镜像
# 基于Python 3.11的轻量级镜像构建MCP服务器

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT_TYPE=sse
ENV MCP_SSE_HOST=0.0.0.0
ENV MCP_SSE_PORT=18002

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt /app/
COPY mcp_server/requirements.txt /app/mcp_server/

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r mcp_server/requirements.txt

# 复制项目文件
COPY . /app/

# 创建非root用户
RUN useradd --create-home --shell /bin/bash mcpuser && \
    chown -R mcpuser:mcpuser /app
USER mcpuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:18002/health', timeout=5)" || exit 1

# 暴露端口
EXPOSE 18002

# 启动命令
CMD ["python", "-m", "mcp_server", "--host", "0.0.0.0", "--port", "18002"]

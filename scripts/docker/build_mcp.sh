#!/bin/bash
# MCP Server Docker镜像构建脚本
#
# 功能：
# 1. 构建MCP Server Docker镜像
# 2. 支持多种构建选项
# 3. 自动标签管理
#
# 使用方法：
#   bash scripts/docker/build_mcp.sh [选项]
#   
# 选项：
#   --tag TAG        指定镜像标签 (默认: latest)
#   --no-cache       不使用缓存构建
#   --push           构建后推送到仓库
#   --registry URL   指定镜像仓库地址
#   --help           显示帮助信息

set -e

# 颜色输出函数
print_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 默认配置
IMAGE_NAME="mirix-mcp-server"
TAG="latest"
NO_CACHE=""
PUSH_IMAGE=false
REGISTRY=""
BUILD_ARGS=""

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# 显示帮助信息
show_help() {
    cat << EOF
MCP Server Docker镜像构建脚本

使用方法:
    $0 [选项]

选项:
    --tag TAG        指定镜像标签 (默认: latest)
    --no-cache       不使用缓存构建
    --push           构建后推送到仓库
    --registry URL   指定镜像仓库地址
    --build-arg ARG  传递构建参数
    --help           显示此帮助信息

示例:
    $0                                    # 使用默认配置构建
    $0 --tag v1.0.0                      # 指定标签构建
    $0 --tag dev --no-cache              # 不使用缓存构建开发版本
    $0 --tag prod --push --registry hub.docker.com/mirix
    $0 --build-arg ENV=production        # 传递构建参数

环境变量:
    DOCKER_REGISTRY  默认镜像仓库地址
    DOCKER_BUILDKIT  启用BuildKit (推荐设置为1)
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --build-arg)
            BUILD_ARGS="$BUILD_ARGS --build-arg $2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 使用环境变量中的仓库地址（如果未指定）
if [ -z "$REGISTRY" ] && [ -n "$DOCKER_REGISTRY" ]; then
    REGISTRY="$DOCKER_REGISTRY"
fi

# 构建完整的镜像名称
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$TAG"
else
    FULL_IMAGE_NAME="$IMAGE_NAME:$TAG"
fi

print_info "=== MCP Server Docker镜像构建 ==="
print_info "项目根目录: $PROJECT_ROOT"
print_info "镜像名称: $FULL_IMAGE_NAME"
print_info "构建选项: $NO_CACHE $BUILD_ARGS"

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装或不可用"
    exit 1
fi

# 检查Docker服务是否运行
if ! docker info &> /dev/null; then
    print_error "Docker 服务未运行"
    exit 1
fi

# 检查Dockerfile是否存在
DOCKERFILE_PATH="$PROJECT_ROOT/mcp_server/Dockerfile"
if [ ! -f "$DOCKERFILE_PATH" ]; then
    print_error "Dockerfile 不存在: $DOCKERFILE_PATH"
    exit 1
fi

# 启用BuildKit（如果可用）
export DOCKER_BUILDKIT=1

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 构建镜像
print_info "开始构建Docker镜像..."
BUILD_START_TIME=$(date +%s)

docker build \
    -f mcp_server/Dockerfile \
    -t "$FULL_IMAGE_NAME" \
    $NO_CACHE \
    $BUILD_ARGS \
    .

BUILD_END_TIME=$(date +%s)
BUILD_DURATION=$((BUILD_END_TIME - BUILD_START_TIME))

print_success "镜像构建完成！"
print_info "构建时间: ${BUILD_DURATION}秒"
print_info "镜像名称: $FULL_IMAGE_NAME"

# 显示镜像信息
print_info "镜像信息:"
docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# 推送镜像（如果指定）
if [ "$PUSH_IMAGE" = true ]; then
    if [ -z "$REGISTRY" ]; then
        print_warning "未指定仓库地址，跳过推送"
    else
        print_info "推送镜像到仓库..."
        docker push "$FULL_IMAGE_NAME"
        print_success "镜像推送完成！"
    fi
fi

# 创建额外标签
if [ "$TAG" != "latest" ]; then
    LATEST_IMAGE_NAME="${FULL_IMAGE_NAME%:*}:latest"
    print_info "创建latest标签: $LATEST_IMAGE_NAME"
    docker tag "$FULL_IMAGE_NAME" "$LATEST_IMAGE_NAME"
    
    if [ "$PUSH_IMAGE" = true ] && [ -n "$REGISTRY" ]; then
        docker push "$LATEST_IMAGE_NAME"
    fi
fi

print_success "=== 构建完成 ==="
echo ""
print_info "使用以下命令运行容器:"
echo "  docker run -d --name mcp-server -p 18002:18002 $FULL_IMAGE_NAME"
echo ""
print_info "使用以下命令查看日志:"
echo "  docker logs -f mcp-server"

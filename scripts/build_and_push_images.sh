#!/bin/bash

# ============================================================================
# MIRIX Docker 镜像构建和推送脚本
# ============================================================================
# 功能:
#   - 构建 MIRIX 后端、前端和 MCP SSE 服务的 Docker 镜像
#   - 支持多架构构建 (AMD64, ARM64)
#   - 推送镜像到私有 Docker 仓库
# ============================================================================

set -e  # 遇到错误立即退出

# ============================================================================
# 配置变量
# ============================================================================
PROJECT_ROOT=$(pwd)
DEFAULT_VERSION="latest"
DOCKER_REGISTRY="10.157.152.192:10443"  # 默认私有仓库地址
DOCKER_USERNAME="zxsc-dev"
DOCKER_PASSWORD="Zxsc-dev@123"
ERROR_LOG_FILE="docker_build_push_error.log"
SUCCESS_LOG_FILE="docker_build_push_success.log"

# 多架构平台定义
AMD64_PLATFORM="linux/amd64"
ARM64_PLATFORM="linux/arm64"
ALL_PLATFORMS="$AMD64_PLATFORM,$ARM64_PLATFORM"

# 构建模式：buildx（推荐）或 manual（手动分别构建）
BUILD_MODE="buildx"  # 可选值: buildx, manual

# MIRIX 项目组件
BACKEND_NAME="mirix-backend"
FRONTEND_NAME="mirix-frontend"
MCP_SSE_NAME="mirix-mcp-sse"

# 清除旧日志
rm -f "$ERROR_LOG_FILE" "$SUCCESS_LOG_FILE"

# ============================================================================
# 日志函数
# ============================================================================
log_error() {
    local error_message="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - 错误: $error_message" | tee -a "$ERROR_LOG_FILE" >&2
}

log_success() {
    local success_message="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - 成功: $success_message" | tee -a "$SUCCESS_LOG_FILE"
}

log_info() {
    local info_message="$1"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - 信息: $info_message"
}

# ============================================================================
# 帮助信息
# ============================================================================
show_help() {
    cat << EOF
使用方法:
  $0 [选项]

选项:
  -n, --namespace NAME     指定镜像命名空间 (默认: mirix)
  -v, --version VERSION    指定镜像版本标签 (默认: latest)
  -r, --registry URL       指定 Docker 镜像仓库地址 (默认: 10.157.152.192:10443)
  -u, --username USER      指定 Docker 仓库用户名 (默认: zxsc-dev)
  -w, --password PASS      指定 Docker 仓库密码
  -m, --mode MODE          构建模式 (buildx|manual) 默认: buildx
  -c, --component COMP     只构建指定组件 (backend|frontend|mcp-sse|all) 默认: all
  --amd64-only            只构建 AMD64 架构
  --arm64-only            只构建 ARM64 架构
  --no-push               构建镜像但不推送
  --insecure              允许使用不安全的 HTTP 连接到仓库
  -h, --help              显示帮助信息

构建模式说明:
  buildx: 使用 docker buildx 一次性构建多架构 (推荐)
  manual: 分别构建各架构然后创建 manifest 清单

组件说明:
  backend:  MIRIX 后端服务 (FastAPI)
  frontend: MIRIX 前端 (React)
  mcp-sse:  MCP SSE 服务
  all:      构建所有组件 (默认)

示例:
  $0 -n mirix -v v1.0.0                    # 构建所有组件的 v1.0.0 版本
  $0 -c backend -v v1.0.0                  # 只构建后端
  $0 -v v1.0.0 --amd64-only                # 只构建 AMD64 架构
  $0 -v v1.0.0 -m manual --insecure        # 使用 manual 模式和不安全连接

EOF
}

# ============================================================================
# Docker 环境诊断
# ============================================================================
diagnose_docker_environment() {
    log_info "=== Docker 环境诊断 ==="

    # 检查 Docker 版本
    if ! docker --version &>/dev/null; then
        log_error "Docker 未安装或无法访问"
        exit 1
    fi

    local docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
    log_info "Docker 版本: $docker_version"

    # 检查 buildx（如果使用 buildx 模式）
    if [ "$BUILD_MODE" = "buildx" ]; then
        if ! docker buildx version &>/dev/null; then
            log_error "Docker Buildx 未安装"
            log_info "请安装 Docker Buildx 或使用 manual 模式: -m manual"
            exit 1
        fi
        log_success "✓ Docker Buildx 可用"
    fi

    # 测试仓库连接
    log_info "测试仓库连接: $DOCKER_REGISTRY"
    if curl -k -s --max-time 5 "https://$DOCKER_REGISTRY/v2/" &>/dev/null || \
       curl -s --max-time 5 "http://$DOCKER_REGISTRY/v2/" &>/dev/null; then
        log_success "✓ 仓库连接成功"
    else
        log_error "✗ 仓库连接失败，请检查网络和仓库地址"
    fi

    log_info "=== 诊断完成 ==="
}

# ============================================================================
# 设置 Buildx 环境
# ============================================================================
setup_buildx() {
    if [ "$BUILD_MODE" != "buildx" ]; then
        return 0
    fi

    log_info "设置多架构构建环境"

    local builder_name="mirix-builder"

    # 删除现有构建器
    if docker buildx ls | grep -q "$builder_name"; then
        log_info "删除现有构建器: $builder_name"
        docker buildx rm "$builder_name" 2>/dev/null || true
    fi

    # 创建新的构建器配置
    if [ "$USE_INSECURE" = true ]; then
        cat > /tmp/buildkitd.toml << EOF
[registry."$DOCKER_REGISTRY"]
  http = true
  insecure = true
EOF
        docker buildx create --name "$builder_name" --driver docker-container \
            --config /tmp/buildkitd.toml --bootstrap --use
        rm -f /tmp/buildkitd.toml
    else
        docker buildx create --name "$builder_name" --driver docker-container \
            --bootstrap --use
    fi

    log_success "构建器创建成功: $builder_name"

    # 显示支持的平台
    local supported_platforms=$(docker buildx inspect --bootstrap | grep "Platforms:" | sed 's/Platforms: //' || echo "unknown")
    log_info "支持的平台: $supported_platforms"
}

# ============================================================================
# Docker 登录
# ============================================================================
docker_login() {
    log_info "登录到 Docker 仓库: $DOCKER_REGISTRY"

    # 尝试多种登录方式
    if echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin "$DOCKER_REGISTRY" 2>/dev/null || \
       echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin "http://$DOCKER_REGISTRY" 2>/dev/null; then
        log_success "Docker 仓库登录成功"
    else
        log_error "Docker 仓库登录失败"
        log_error "请检查用户名、密码和仓库地址"
        exit 1
    fi
}

# ============================================================================
# 使用 Buildx 构建多架构镜像
# ============================================================================
build_with_buildx() {
    local component_name="$1"
    local dockerfile_path="$2"
    local build_context="$3"
    local version="$4"
    local platforms="$5"

    local image_tag="$DOCKER_REGISTRY/$NAMESPACE/$component_name:$version"
    log_info "使用 buildx 构建: $image_tag (平台: $platforms)"

    local push_flag=""
    if [ "$NO_PUSH" != true ]; then
        push_flag="--push"
    fi

    if docker buildx build \
        --platform "$platforms" \
        --tag "$image_tag" \
        --file "$dockerfile_path" \
        $push_flag \
        "$build_context"; then
        log_success "镜像构建成功: $image_tag"
        return 0
    else
        log_error "镜像构建失败: $image_tag"
        return 1
    fi
}

# ============================================================================
# 使用 Manual 模式构建
# ============================================================================
build_with_manual() {
    local component_name="$1"
    local dockerfile_path="$2"
    local build_context="$3"
    local version="$4"
    local platforms="$5"

    local base_tag="$DOCKER_REGISTRY/$NAMESPACE/$component_name"
    local version_tag="$base_tag:$version"

    log_info "使用 manual 模式构建: $version_tag"

    local arch_tags=()
    local build_success=true

    # 分别构建各个架构
    for platform in $(echo "$platforms" | tr ',' ' '); do
        local arch=$(echo "$platform" | cut -d'/' -f2)
        local arch_tag="$base_tag:$version-$arch"

        log_info "构建 $arch 架构: $arch_tag"

        if docker build \
            --platform "$platform" \
            --tag "$arch_tag" \
            --file "$dockerfile_path" \
            "$build_context"; then

            log_success "$arch 架构构建成功"

            if [ "$NO_PUSH" != true ]; then
                log_info "推送 $arch 架构镜像"
                if docker push "$arch_tag"; then
                    log_success "$arch 架构推送成功"
                    arch_tags+=("$arch_tag")
                else
                    log_error "$arch 架构推送失败"
                    build_success=false
                fi
            else
                arch_tags+=("$arch_tag")
            fi
        else
            log_error "$arch 架构构建失败"
            build_success=false
        fi
    done

    if [ "$build_success" = false ]; then
        return 1
    fi

    # 创建 manifest（仅当有多个架构时）
    if [ ${#arch_tags[@]} -gt 1 ] && [ "$NO_PUSH" != true ]; then
        log_info "创建 manifest: $version_tag"

        docker manifest rm "$version_tag" 2>/dev/null || true

        local manifest_cmd="docker manifest create $version_tag"
        for arch_tag in "${arch_tags[@]}"; do
            manifest_cmd="$manifest_cmd --amend $arch_tag"
        done

        if eval "$manifest_cmd" && docker manifest push "$version_tag"; then
            log_success "Manifest 创建并推送成功"
        else
            log_error "Manifest 创建或推送失败"
            return 1
        fi
    fi

    return 0
}

# ============================================================================
# 构建单个组件
# ============================================================================
build_component() {
    local component="$1"
    local version="$2"
    local platforms="$3"

    case "$component" in
        backend)
            log_info "构建 MIRIX 后端服务"
            local dockerfile="$PROJECT_ROOT/Dockerfile.backend"
            local context="$PROJECT_ROOT"
            ;;
        frontend)
            log_info "构建 MIRIX 前端"
            local dockerfile="$PROJECT_ROOT/Dockerfile.frontend"
            local context="$PROJECT_ROOT"
            ;;
        mcp-sse)
            log_info "构建 MCP SSE 服务"
            local dockerfile="$PROJECT_ROOT/Dockerfile.mcp-sse"
            local context="$PROJECT_ROOT"
            ;;
        *)
            log_error "未知组件: $component"
            return 1
            ;;
    esac

    # 检查 Dockerfile 是否存在
    if [ ! -f "$dockerfile" ]; then
        log_error "Dockerfile 不存在: $dockerfile"
        return 1
    fi

    # 根据构建模式选择构建方法
    if [ "$BUILD_MODE" = "buildx" ]; then
        build_with_buildx "$component" "$dockerfile" "$context" "$version" "$platforms"
    else
        build_with_manual "$component" "$dockerfile" "$context" "$version" "$platforms"
    fi
}

# ============================================================================
# 主程序
# ============================================================================
main() {
    # 默认值
    NAMESPACE="mirix"
    VERSION="$DEFAULT_VERSION"
    PLATFORMS="$ALL_PLATFORMS"
    COMPONENT="all"
    NO_PUSH=false
    USE_INSECURE=false

    # 参数解析
    while [ $# -gt 0 ]; do
        case "$1" in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            -u|--username)
                DOCKER_USERNAME="$2"
                shift 2
                ;;
            -w|--password)
                DOCKER_PASSWORD="$2"
                shift 2
                ;;
            -m|--mode)
                BUILD_MODE="$2"
                if [ "$BUILD_MODE" != "buildx" ] && [ "$BUILD_MODE" != "manual" ]; then
                    log_error "无效的构建模式: $BUILD_MODE"
                    exit 1
                fi
                shift 2
                ;;
            -c|--component)
                COMPONENT="$2"
                shift 2
                ;;
            --amd64-only)
                PLATFORMS="$AMD64_PLATFORM"
                shift
                ;;
            --arm64-only)
                PLATFORMS="$ARM64_PLATFORM"
                shift
                ;;
            --no-push)
                NO_PUSH=true
                shift
                ;;
            --insecure)
                USE_INSECURE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示配置
    log_info "=== 构建配置 ==="
    log_info "命名空间: $NAMESPACE"
    log_info "版本: $VERSION"
    log_info "仓库: $DOCKER_REGISTRY"
    log_info "构建模式: $BUILD_MODE"
    log_info "平台: $PLATFORMS"
    log_info "组件: $COMPONENT"
    log_info "推送: $([ "$NO_PUSH" = true ] && echo '否' || echo '是')"
    log_info "================"

    # 诊断环境
    diagnose_docker_environment

    # 设置 buildx
    setup_buildx

    # 登录仓库
    if [ "$NO_PUSH" != true ]; then
        docker_login
    fi

    # 构建组件
    local success_count=0
    local fail_count=0

    if [ "$COMPONENT" = "all" ]; then
        for comp in backend frontend mcp-sse; do
            if build_component "$comp" "$VERSION" "$PLATFORMS"; then
                ((success_count++))
            else
                ((fail_count++))
            fi
        done
    else
        if build_component "$COMPONENT" "$VERSION" "$PLATFORMS"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    fi

    # 总结
    log_info "=== 构建完成 ==="
    log_info "成功: $success_count"
    log_info "失败: $fail_count"

    if [ $fail_count -gt 0 ]; then
        log_error "存在构建失败，请查看日志: $ERROR_LOG_FILE"
        exit 1
    else
        log_success "所有镜像构建成功！"
        exit 0
    fi
}

# 执行主程序
main "$@"

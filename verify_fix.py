#!/usr/bin/env python3
"""
修复验证脚本

这个脚本验证本地代码修复是否正确，以及容器是否需要重建
"""

import sys
from pathlib import Path

def check_code_fixes():
    """检查代码修复是否正确"""
    server_file = Path("/opt/MIRIX/mcp_server/server.py")
    
    if not server_file.exists():
        print("❌ 找不到 server.py 文件")
        return False
    
    content = server_file.read_text(encoding='utf-8')
    
    # 检查关键修复点
    checks = [
        ("memory_add修复", "memory_data = {" in content and "await self.mirix_adapter.add_memory(memory_data)" in content),
        ("memory_chat修复", "chat_data = {" in content and "await self.mirix_adapter.chat_with_memory(chat_data)" in content),  
        ("memory_search修复", "search_data = {" in content and "await self.mirix_adapter.search_memory(search_data)" in content),
        ("get_user_profile修复", "profile_data = {" in content and "await self.mirix_adapter.get_user_profile(profile_data)" in content),
        ("错误字段统一", "result.get('error'," in content),
        ("没有旧调用方式", "await self.mirix_adapter.add_memory(user_id, content)" not in content)
    ]
    
    all_passed = True
    print("=== 代码修复验证 ===")
    
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}: {'通过' if passed else '失败'}")
        if not passed:
            all_passed = False
    
    return all_passed

def check_container_sync():
    """检查容器是否需要重建"""
    import subprocess
    import time
    
    print("\n=== 容器同步检查 ===")
    
    try:
        # 测试连接
        import urllib.request
        url = "http://localhost:18002/sse"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                print("✅ MCP服务器运行正常")
                return True
            else:
                print(f"⚠️  MCP服务器响应异常: {response.getcode()}")
                return False
    except Exception as e:
        print(f"❌ MCP服务器连接失败: {e}")
        print("提示: 可能需要启动服务或重建容器")
        return False

def main():
    """主函数"""
    print("MIRIX MCP 修复验证工具")
    print("=" * 50)
    
    # 检查代码修复
    code_fixed = check_code_fixes()
    
    # 检查容器状态
    container_ok = check_container_sync()
    
    print("\n" + "=" * 50)
    print("验证结果总结:")
    
    if code_fixed:
        print("✅ 本地代码修复正确")
    else:
        print("❌ 本地代码修复有问题，需要重新检查")
        return 1
    
    if not container_ok:
        print("⚠️  容器可能未使用最新代码")
        print("\n建议执行以下命令重建容器：")
        print("cd /opt/MIRIX && ./force_rebuild_mcp.sh")
        print("\n或手动重建：")
        print("sudo docker-compose stop mirix-mcp")
        print("sudo docker-compose rm -f mirix-mcp") 
        print("sudo docker-compose build --no-cache mirix-mcp")
        print("sudo docker-compose up -d mirix-mcp")
    
    print("\n修复状态: ", end="")
    if code_fixed and container_ok:
        print("🎉 完全修复，可以开始测试！")
        return 0
    elif code_fixed:
        print("🔄 代码已修复，需要重建容器")
        return 2
    else:
        print("🚨 需要修复代码")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
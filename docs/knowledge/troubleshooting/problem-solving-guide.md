# MIRIX 问题排查与解决方案指南

## 📋 文档概述

本文档为MIRIX系统的问题排查与解决方案指南，提供系统性的故障诊断方法、常见问题解决方案和预防措施。面向开发人员、运维人员和系统管理员，确保能够快速定位和解决系统问题。

---

## 🎯 第一层：问题分类大纲

### 问题分类体系
```mermaid
graph TB
    subgraph "系统层问题"
        A[环境配置问题] --> A1[Python环境]
        A --> A2[数据库连接]
        A --> A3[依赖冲突]
        A --> A4[权限问题]
    end
    
    subgraph "应用层问题"
        B[API服务问题] --> B1[启动失败]
        B --> B2[响应超时]
        B --> B3[认证错误]
        B --> B4[数据验证]
    end
    
    subgraph "智能体问题"
        C[Agent问题] --> C1[创建失败]
        C --> C2[对话异常]
        C --> C3[记忆错误]
        C --> C4[模型调用]
    end
    
    subgraph "性能问题"
        D[性能问题] --> D1[响应慢]
        D --> D2[内存泄漏]
        D --> D3[数据库慢查询]
        D --> D4[并发问题]
    end
```

### 问题严重级别
- **P0 - 紧急**：系统完全不可用，影响所有用户
- **P1 - 高优先级**：核心功能异常，影响大部分用户
- **P2 - 中优先级**：部分功能异常，影响少数用户
- **P3 - 低优先级**：轻微问题，不影响核心功能

### 问题排查流程
```mermaid
sequenceDiagram
    participant U as 用户报告
    participant D as 问题诊断
    participant L as 日志分析
    participant T as 测试验证
    participant S as 解决方案
    participant V as 验证修复
    
    U->>D: 问题描述
    D->>L: 收集日志
    L->>T: 重现问题
    T->>S: 制定方案
    S->>V: 实施修复
    V->>U: 确认解决
```

---

## 🔧 第二层：诊断方法与工具

### 系统诊断工具

#### 1. 健康检查脚本
```python
# scripts/health_check.py
import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any, List
import psutil
import aiohttp
import asyncpg
import redis.asyncio as redis

class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.checks = []
        self.results = {}
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """运行所有健康检查"""
        print("🏥 开始系统健康检查...")
        
        checks = [
            self.check_system_resources(),
            self.check_database_connection(),
            self.check_redis_connection(),
            self.check_api_endpoints(),
            self.check_disk_space(),
            self.check_memory_usage(),
            self.check_process_status()
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # 汇总结果
        overall_status = "healthy"
        issues = []
        
        for i, result in enumerate(results):
            check_name = [
                "system_resources", "database", "redis", 
                "api_endpoints", "disk_space", "memory", "processes"
            ][i]
            
            if isinstance(result, Exception):
                self.results[check_name] = {
                    "status": "error",
                    "error": str(result)
                }
                overall_status = "unhealthy"
                issues.append(f"{check_name}: {result}")
            else:
                self.results[check_name] = result
                if result.get("status") != "ok":
                    overall_status = "degraded"
                    issues.append(f"{check_name}: {result.get('message', 'Unknown issue')}")
        
        # 生成报告
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status,
            "checks": self.results,
            "issues": issues,
            "recommendations": self._generate_recommendations()
        }
        
        self._print_report(report)
        return report
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """检查系统资源"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "ok"
            warnings = []
            
            if cpu_percent > 80:
                status = "warning"
                warnings.append(f"CPU使用率过高: {cpu_percent}%")
            
            if memory.percent > 85:
                status = "warning"
                warnings.append(f"内存使用率过高: {memory.percent}%")
            
            if disk.percent > 90:
                status = "critical"
                warnings.append(f"磁盘使用率过高: {disk.percent}%")
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "warnings": warnings
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            # 从环境变量获取数据库URL
            db_url = os.getenv("DATABASE_URL", "postgresql://mirix:mirix@localhost:5432/mirix")
            
            # 解析连接参数
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:]  # 去掉开头的 /
            )
            
            # 执行测试查询
            result = await conn.fetchval("SELECT 1")
            await conn.close()
            
            if result == 1:
                return {"status": "ok", "message": "数据库连接正常"}
            else:
                return {"status": "error", "message": "数据库查询异常"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_redis_connection(self) -> Dict[str, Any]:
        """检查Redis连接"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
            r = redis.from_url(redis_url)
            await r.ping()
            await r.close()
            
            return {"status": "ok", "message": "Redis连接正常"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_api_endpoints(self) -> Dict[str, Any]:
        """检查API端点"""
        try:
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            
            endpoints = [
                "/health",
                "/api/v1/agents",
                "/docs"
            ]
            
            results = {}
            overall_status = "ok"
            
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        async with session.get(f"{base_url}{endpoint}") as response:
                            if response.status == 200:
                                results[endpoint] = "ok"
                            else:
                                results[endpoint] = f"HTTP {response.status}"
                                overall_status = "warning"
                    except Exception as e:
                        results[endpoint] = f"error: {e}"
                        overall_status = "error"
            
            return {
                "status": overall_status,
                "endpoints": results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """检查磁盘空间"""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            
            status = "ok"
            if free_gb < 1:  # 少于1GB
                status = "critical"
            elif free_gb < 5:  # 少于5GB
                status = "warning"
            
            return {
                "status": status,
                "free_space_gb": round(free_gb, 2),
                "total_space_gb": round(disk_usage.total / (1024**3), 2),
                "used_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            
            # 检查MIRIX进程的内存使用
            mirix_memory = 0
            for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    if 'mirix' in proc.info['name'].lower() or 'uvicorn' in proc.info['name'].lower():
                        mirix_memory += proc.info['memory_info'].rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            mirix_memory_mb = mirix_memory / (1024**2)
            
            status = "ok"
            if mirix_memory_mb > 1024:  # 超过1GB
                status = "warning"
            elif mirix_memory_mb > 2048:  # 超过2GB
                status = "critical"
            
            return {
                "status": status,
                "system_memory_percent": memory.percent,
                "mirix_memory_mb": round(mirix_memory_mb, 2),
                "available_memory_gb": round(memory.available / (1024**3), 2)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_process_status(self) -> Dict[str, Any]:
        """检查进程状态"""
        try:
            processes = {}
            
            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent']):
                try:
                    name = proc.info['name'].lower()
                    if any(keyword in name for keyword in ['mirix', 'uvicorn', 'gunicorn', 'postgres', 'redis']):
                        processes[proc.info['name']] = {
                            "pid": proc.info['pid'],
                            "status": proc.info['status'],
                            "cpu_percent": proc.info['cpu_percent']
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 检查关键进程是否运行
            required_processes = ['postgres', 'redis']
            missing_processes = []
            
            for req_proc in required_processes:
                if not any(req_proc in name.lower() for name in processes.keys()):
                    missing_processes.append(req_proc)
            
            status = "ok" if not missing_processes else "warning"
            
            return {
                "status": status,
                "processes": processes,
                "missing_processes": missing_processes
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于检查结果生成建议
        if "system_resources" in self.results:
            res = self.results["system_resources"]
            if res.get("cpu_percent", 0) > 80:
                recommendations.append("考虑增加CPU资源或优化高CPU使用的进程")
            if res.get("memory_percent", 0) > 85:
                recommendations.append("考虑增加内存或检查内存泄漏")
            if res.get("disk_percent", 0) > 90:
                recommendations.append("清理磁盘空间或增加存储容量")
        
        if "database" in self.results and self.results["database"].get("status") != "ok":
            recommendations.append("检查数据库服务状态和连接配置")
        
        if "redis" in self.results and self.results["redis"].get("status") != "ok":
            recommendations.append("检查Redis服务状态和连接配置")
        
        return recommendations
    
    def _print_report(self, report: Dict[str, Any]):
        """打印报告"""
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        
        print(f"\n{status_emoji.get(report['overall_status'], '❓')} 系统状态: {report['overall_status'].upper()}")
        print(f"📅 检查时间: {report['timestamp']}")
        
        if report['issues']:
            print("\n🚨 发现的问题:")
            for issue in report['issues']:
                print(f"  - {issue}")
        
        if report['recommendations']:
            print("\n💡 建议:")
            for rec in report['recommendations']:
                print(f"  - {rec}")
        
        print("\n📊 详细检查结果:")
        for check_name, result in report['checks'].items():
            status = result.get('status', 'unknown')
            emoji = "✅" if status == "ok" else "⚠️" if status == "warning" else "❌"
            print(f"  {emoji} {check_name}: {status}")

# 使用示例
async def main():
    checker = SystemHealthChecker()
    report = await checker.run_all_checks()
    
    # 保存报告
    import json
    with open(f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    asyncio.run(main())
```

#### 2. 日志分析工具
```python
# scripts/log_analyzer.py
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

class LogAnalyzer:
    """日志分析器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.patterns = {
            "error": re.compile(r"ERROR|CRITICAL|Exception|Traceback", re.IGNORECASE),
            "warning": re.compile(r"WARNING|WARN", re.IGNORECASE),
            "api_request": re.compile(r"(GET|POST|PUT|DELETE)\s+(/[^\s]*)\s+(\d{3})"),
            "database": re.compile(r"database|sql|query", re.IGNORECASE),
            "memory": re.compile(r"memory|oom|out of memory", re.IGNORECASE),
            "timeout": re.compile(r"timeout|timed out", re.IGNORECASE)
        }
    
    def analyze_logs(
        self, 
        hours: int = 24,
        log_level: str = "all"
    ) -> Dict[str, Any]:
        """分析日志"""
        print(f"📊 分析最近{hours}小时的日志...")
        
        # 获取日志文件
        log_files = self._get_recent_log_files(hours)
        
        if not log_files:
            return {"error": "未找到日志文件"}
        
        # 分析结果
        analysis = {
            "summary": {
                "total_lines": 0,
                "error_count": 0,
                "warning_count": 0,
                "time_range": {
                    "start": None,
                    "end": None
                }
            },
            "errors": [],
            "warnings": [],
            "api_stats": {
                "total_requests": 0,
                "status_codes": {},
                "endpoints": {},
                "response_times": []
            },
            "patterns": {
                "database_issues": [],
                "memory_issues": [],
                "timeout_issues": []
            },
            "recommendations": []
        }
        
        # 处理每个日志文件
        for log_file in log_files:
            self._analyze_file(log_file, analysis)
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        # 打印摘要
        self._print_analysis_summary(analysis)
        
        return analysis
    
    def _get_recent_log_files(self, hours: int) -> List[Path]:
        """获取最近的日志文件"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        log_files = []
        
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime > cutoff_time.timestamp():
                log_files.append(log_file)
        
        return sorted(log_files, key=lambda x: x.stat().st_mtime)
    
    def _analyze_file(self, log_file: Path, analysis: Dict[str, Any]):
        """分析单个日志文件"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    analysis["summary"]["total_lines"] += 1
                    
                    # 检查错误
                    if self.patterns["error"].search(line):
                        analysis["summary"]["error_count"] += 1
                        analysis["errors"].append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip(),
                            "timestamp": self._extract_timestamp(line)
                        })
                    
                    # 检查警告
                    elif self.patterns["warning"].search(line):
                        analysis["summary"]["warning_count"] += 1
                        analysis["warnings"].append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip(),
                            "timestamp": self._extract_timestamp(line)
                        })
                    
                    # 检查API请求
                    api_match = self.patterns["api_request"].search(line)
                    if api_match:
                        method, endpoint, status_code = api_match.groups()
                        analysis["api_stats"]["total_requests"] += 1
                        
                        # 统计状态码
                        if status_code not in analysis["api_stats"]["status_codes"]:
                            analysis["api_stats"]["status_codes"][status_code] = 0
                        analysis["api_stats"]["status_codes"][status_code] += 1
                        
                        # 统计端点
                        if endpoint not in analysis["api_stats"]["endpoints"]:
                            analysis["api_stats"]["endpoints"][endpoint] = 0
                        analysis["api_stats"]["endpoints"][endpoint] += 1
                    
                    # 检查特定模式
                    if self.patterns["database"].search(line):
                        analysis["patterns"]["database_issues"].append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip()
                        })
                    
                    if self.patterns["memory"].search(line):
                        analysis["patterns"]["memory_issues"].append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip()
                        })
                    
                    if self.patterns["timeout"].search(line):
                        analysis["patterns"]["timeout_issues"].append({
                            "file": str(log_file),
                            "line": line_num,
                            "content": line.strip()
                        })
        
        except Exception as e:
            print(f"❌ 分析文件 {log_file} 时出错: {e}")
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """提取时间戳"""
        # 常见的时间戳格式
        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}",
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]"
        ]
        
        for pattern in timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
        
        return None
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于错误数量
        error_count = analysis["summary"]["error_count"]
        if error_count > 100:
            recommendations.append("错误数量过多，建议检查系统稳定性")
        elif error_count > 50:
            recommendations.append("存在较多错误，建议关注错误模式")
        
        # 基于API状态码
        status_codes = analysis["api_stats"]["status_codes"]
        if "500" in status_codes and status_codes["500"] > 10:
            recommendations.append("存在大量5xx错误，检查服务器内部错误")
        if "404" in status_codes and status_codes["404"] > 50:
            recommendations.append("存在大量404错误，检查路由配置")
        
        # 基于特定模式
        if len(analysis["patterns"]["database_issues"]) > 20:
            recommendations.append("数据库相关问题较多，检查数据库性能和连接")
        
        if len(analysis["patterns"]["memory_issues"]) > 0:
            recommendations.append("发现内存相关问题，检查内存泄漏")
        
        if len(analysis["patterns"]["timeout_issues"]) > 10:
            recommendations.append("超时问题较多，检查网络和服务响应时间")
        
        return recommendations
    
    def _print_analysis_summary(self, analysis: Dict[str, Any]):
        """打印分析摘要"""
        print("\n📊 日志分析摘要")
        print("=" * 50)
        
        summary = analysis["summary"]
        print(f"📄 总行数: {summary['total_lines']:,}")
        print(f"❌ 错误数: {summary['error_count']:,}")
        print(f"⚠️ 警告数: {summary['warning_count']:,}")
        
        api_stats = analysis["api_stats"]
        print(f"\n🌐 API统计")
        print(f"📊 总请求数: {api_stats['total_requests']:,}")
        
        if api_stats["status_codes"]:
            print("📈 状态码分布:")
            for code, count in sorted(api_stats["status_codes"].items()):
                print(f"  {code}: {count:,}")
        
        if api_stats["endpoints"]:
            print("🔗 热门端点 (前5):")
            sorted_endpoints = sorted(
                api_stats["endpoints"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            for endpoint, count in sorted_endpoints:
                print(f"  {endpoint}: {count:,}")
        
        # 打印建议
        if analysis["recommendations"]:
            print(f"\n💡 建议:")
            for rec in analysis["recommendations"]:
                print(f"  - {rec}")
        
        # 打印最近的错误
        if analysis["errors"]:
            print(f"\n🚨 最近的错误 (前3):")
            for error in analysis["errors"][-3:]:
                print(f"  📍 {error['file']}:{error['line']}")
                print(f"     {error['content'][:100]}...")

# 使用示例
def main():
    analyzer = LogAnalyzer()
    
    # 分析最近24小时的日志
    analysis = analyzer.analyze_logs(hours=24)
    
    # 保存分析结果
    with open(f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

if __name__ == "__main__":
    main()
```

### 性能监控工具

#### 1. 性能监控脚本
```python
# scripts/performance_monitor.py
import asyncio
import time
import psutil
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import pandas as pd

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.metrics = {
            "timestamp": [],
            "cpu_percent": [],
            "memory_percent": [],
            "disk_io": [],
            "network_io": [],
            "api_response_time": [],
            "active_connections": []
        }
    
    async def start_monitoring(self, duration_minutes: int = 60, interval_seconds: int = 30):
        """开始性能监控"""
        print(f"🔍 开始性能监控，持续{duration_minutes}分钟，间隔{interval_seconds}秒")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            await self._collect_metrics()
            await asyncio.sleep(interval_seconds)
        
        # 生成报告
        self._generate_report()
    
    async def _collect_metrics(self):
        """收集性能指标"""
        timestamp = datetime.now()
        
        # 系统资源
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()
        
        # API响应时间
        api_response_time = await self._measure_api_response_time()
        
        # 活跃连接数
        active_connections = len(psutil.net_connections())
        
        # 记录指标
        self.metrics["timestamp"].append(timestamp)
        self.metrics["cpu_percent"].append(cpu_percent)
        self.metrics["memory_percent"].append(memory.percent)
        self.metrics["disk_io"].append(disk_io.read_bytes + disk_io.write_bytes if disk_io else 0)
        self.metrics["network_io"].append(network_io.bytes_sent + network_io.bytes_recv if network_io else 0)
        self.metrics["api_response_time"].append(api_response_time)
        self.metrics["active_connections"].append(active_connections)
        
        print(f"📊 {timestamp.strftime('%H:%M:%S')} - CPU: {cpu_percent}%, 内存: {memory.percent}%, API响应: {api_response_time}ms")
    
    async def _measure_api_response_time(self) -> float:
        """测量API响应时间"""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base_url}/health") as response:
                    await response.text()
            
            end_time = time.time()
            return round((end_time - start_time) * 1000, 2)  # 毫秒
            
        except Exception as e:
            print(f"⚠️ API响应时间测量失败: {e}")
            return -1
    
    def _generate_report(self):
        """生成性能报告"""
        if not self.metrics["timestamp"]:
            print("❌ 没有收集到性能数据")
            return
        
        # 创建DataFrame
        df = pd.DataFrame(self.metrics)
        
        # 计算统计信息
        stats = {
            "cpu": {
                "avg": df["cpu_percent"].mean(),
                "max": df["cpu_percent"].max(),
                "min": df["cpu_percent"].min()
            },
            "memory": {
                "avg": df["memory_percent"].mean(),
                "max": df["memory_percent"].max(),
                "min": df["memory_percent"].min()
            },
            "api_response_time": {
                "avg": df[df["api_response_time"] > 0]["api_response_time"].mean(),
                "max": df[df["api_response_time"] > 0]["api_response_time"].max(),
                "min": df[df["api_response_time"] > 0]["api_response_time"].min()
            }
        }
        
        # 打印统计信息
        print("\n📈 性能监控报告")
        print("=" * 50)
        print(f"📅 监控时间: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
        print(f"📊 数据点数: {len(df)}")
        
        print(f"\n💻 CPU使用率:")
        print(f"  平均: {stats['cpu']['avg']:.1f}%")
        print(f"  最高: {stats['cpu']['max']:.1f}%")
        print(f"  最低: {stats['cpu']['min']:.1f}%")
        
        print(f"\n🧠 内存使用率:")
        print(f"  平均: {stats['memory']['avg']:.1f}%")
        print(f"  最高: {stats['memory']['max']:.1f}%")
        print(f"  最低: {stats['memory']['min']:.1f}%")
        
        if stats['api_response_time']['avg'] > 0:
            print(f"\n🌐 API响应时间:")
            print(f"  平均: {stats['api_response_time']['avg']:.1f}ms")
            print(f"  最慢: {stats['api_response_time']['max']:.1f}ms")
            print(f"  最快: {stats['api_response_time']['min']:.1f}ms")
        
        # 生成图表
        self._create_charts(df)
        
        # 生成建议
        recommendations = self._generate_performance_recommendations(stats)
        if recommendations:
            print(f"\n💡 性能优化建议:")
            for rec in recommendations:
                print(f"  - {rec}")
    
    def _create_charts(self, df: pd.DataFrame):
        """创建性能图表"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('MIRIX 性能监控报告', fontsize=16)
            
            # CPU使用率
            axes[0, 0].plot(df['timestamp'], df['cpu_percent'])
            axes[0, 0].set_title('CPU使用率 (%)')
            axes[0, 0].set_ylabel('百分比')
            axes[0, 0].grid(True)
            
            # 内存使用率
            axes[0, 1].plot(df['timestamp'], df['memory_percent'], color='orange')
            axes[0, 1].set_title('内存使用率 (%)')
            axes[0, 1].set_ylabel('百分比')
            axes[0, 1].grid(True)
            
            # API响应时间
            valid_api_data = df[df['api_response_time'] > 0]
            if not valid_api_data.empty:
                axes[1, 0].plot(valid_api_data['timestamp'], valid_api_data['api_response_time'], color='green')
                axes[1, 0].set_title('API响应时间 (ms)')
                axes[1, 0].set_ylabel('毫秒')
                axes[1, 0].grid(True)
            
            # 活跃连接数
            axes[1, 1].plot(df['timestamp'], df['active_connections'], color='red')
            axes[1, 1].set_title('活跃连接数')
            axes[1, 1].set_ylabel('连接数')
            axes[1, 1].grid(True)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            chart_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            print(f"\n📊 性能图表已保存: {chart_filename}")
            
        except Exception as e:
            print(f"⚠️ 生成图表失败: {e}")
    
    def _generate_performance_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成性能建议"""
        recommendations = []
        
        # CPU建议
        if stats['cpu']['avg'] > 70:
            recommendations.append("CPU平均使用率较高，考虑优化计算密集型操作或增加CPU资源")
        if stats['cpu']['max'] > 90:
            recommendations.append("CPU峰值使用率过高，检查是否有CPU密集型任务")
        
        # 内存建议
        if stats['memory']['avg'] > 80:
            recommendations.append("内存平均使用率较高，检查内存泄漏或考虑增加内存")
        if stats['memory']['max'] > 95:
            recommendations.append("内存使用率接近极限，立即检查内存使用情况")
        
        # API响应时间建议
        if stats['api_response_time']['avg'] > 1000:
            recommendations.append("API平均响应时间过长，优化数据库查询和业务逻辑")
        if stats['api_response_time']['max'] > 5000:
            recommendations.append("API最大响应时间过长，检查慢查询和超时配置")
        
        return recommendations

# 使用示例
async def main():
    monitor = PerformanceMonitor()
    
    # 监控30分钟，每15秒收集一次数据
    await monitor.start_monitoring(duration_minutes=30, interval_seconds=15)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🛠️ 第三层：具体问题解决方案

### 环境配置问题

#### 1. Python环境问题
```bash
# 问题：Python版本不兼容
# 症状：ImportError, SyntaxError, 模块不存在

# 解决方案1：检查Python版本
python --version
# 确保版本 >= 3.11

# 解决方案2：重新创建虚拟环境
Remove-Item -Recurse -Force venv  # Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# 解决方案3：使用pyenv管理Python版本（Linux/Mac）
# pyenv install 3.11.5
# pyenv local 3.11.5
```

#### 2. 依赖冲突问题
```python
# scripts/dependency_resolver.py
import subprocess
import sys
from typing import List, Dict, Any

class DependencyResolver:
    """依赖冲突解决器"""
    
    def __init__(self):
        self.conflicts = []
        self.resolutions = []
    
    def check_dependencies(self) -> Dict[str, Any]:
        """检查依赖冲突"""
        print("🔍 检查依赖冲突...")
        
        try:
            # 运行pip check
            result = subprocess.run([
                sys.executable, "-m", "pip", "check"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 没有发现依赖冲突")
                return {"status": "ok", "conflicts": []}
            else:
                conflicts = self._parse_conflicts(result.stdout)
                print(f"❌ 发现 {len(conflicts)} 个依赖冲突")
                
                for conflict in conflicts:
                    print(f"  - {conflict}")
                
                return {"status": "conflicts", "conflicts": conflicts}
                
        except Exception as e:
            print(f"❌ 检查依赖时出错: {e}")
            return {"status": "error", "error": str(e)}
    
    def _parse_conflicts(self, output: str) -> List[str]:
        """解析冲突输出"""
        conflicts = []
        for line in output.strip().split('\n'):
            if line.strip():
                conflicts.append(line.strip())
        return conflicts
    
    def resolve_conflicts(self):
        """解决依赖冲突"""
        print("🔧 尝试解决依赖冲突...")
        
        # 常见解决方案
        solutions = [
            self._upgrade_pip,
            self._reinstall_requirements,
            self._use_pip_tools,
            self._create_clean_environment
        ]
        
        for solution in solutions:
            try:
                if solution():
                    print("✅ 依赖冲突已解决")
                    return True
            except Exception as e:
                print(f"⚠️ 解决方案失败: {e}")
                continue
        
        print("❌ 无法自动解决依赖冲突，需要手动处理")
        return False
    
    def _upgrade_pip(self) -> bool:
        """升级pip"""
        print("📦 升级pip...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], capture_output=True)
        return result.returncode == 0
    
    def _reinstall_requirements(self) -> bool:
        """重新安装依赖"""
        print("🔄 重新安装依赖...")
        
        # 卸载所有包
        result = subprocess.run([
            sys.executable, "-m", "pip", "freeze"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            packages = [line.split('==')[0] for line in result.stdout.strip().split('\n') if line]
            
            for package in packages:
                subprocess.run([
                    sys.executable, "-m", "pip", "uninstall", "-y", package
                ], capture_output=True)
        
        # 重新安装
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True)
        
        return result.returncode == 0
    
    def _use_pip_tools(self) -> bool:
        """使用pip-tools解决冲突"""
        print("🛠️ 使用pip-tools...")
        
        # 安装pip-tools
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pip-tools"
        ], capture_output=True)
        
        # 编译依赖
        result = subprocess.run([
            sys.executable, "-m", "piptools", "compile", "requirements.in"
        ], capture_output=True)
        
        if result.returncode == 0:
            # 同步依赖
            result = subprocess.run([
                sys.executable, "-m", "piptools", "sync", "requirements.txt"
            ], capture_output=True)
            return result.returncode == 0
        
        return False
    
    def _create_clean_environment(self) -> bool:
        """创建干净的环境"""
        print("🧹 创建干净的虚拟环境...")
        
        import shutil
        import os
        
        # 删除现有虚拟环境
        if os.path.exists("venv"):
            shutil.rmtree("venv")
        
        # 创建新环境
        result = subprocess.run([
            sys.executable, "-m", "venv", "venv"
        ], capture_output=True)
        
        if result.returncode == 0:
            # 激活并安装依赖
            if os.name == 'nt':  # Windows
                pip_path = "venv\\Scripts\\pip.exe"
            else:  # Linux/Mac
                pip_path = "venv/bin/pip"
            
            result = subprocess.run([
                pip_path, "install", "-r", "requirements.txt"
            ], capture_output=True)
            
            return result.returncode == 0
        
        return False

# 使用示例
def main():
    resolver = DependencyResolver()
    
    # 检查冲突
    check_result = resolver.check_dependencies()
    
    # 如果有冲突，尝试解决
    if check_result["status"] == "conflicts":
        resolver.resolve_conflicts()

if __name__ == "__main__":
    main()
```

#### 3. 数据库连接问题
```python
# scripts/database_troubleshoot.py
import asyncio
import asyncpg
import psutil
import subprocess
from typing import Dict, Any, Optional

class DatabaseTroubleshooter:
    """数据库故障排除器"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.connection_params = self._parse_db_url(db_url)
    
    def _parse_db_url(self, db_url: str) -> Dict[str, Any]:
        """解析数据库URL"""
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path[1:] if parsed.path else None
        }
    
    async def diagnose_connection_issues(self) -> Dict[str, Any]:
        """诊断连接问题"""
        print("🔍 诊断数据库连接问题...")
        
        diagnosis = {
            "connection_test": await self._test_connection(),
            "service_status": self._check_postgres_service(),
            "port_availability": self._check_port_availability(),
            "authentication": await self._test_authentication(),
            "database_exists": await self._check_database_exists(),
            "permissions": await self._check_permissions()
        }
        
        # 生成建议
        diagnosis["recommendations"] = self._generate_db_recommendations(diagnosis)
        
        self._print_diagnosis(diagnosis)
        return diagnosis
    
    async def _test_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            conn = await asyncpg.connect(**self.connection_params)
            await conn.close()
            return {"status": "success", "message": "连接成功"}
        except asyncpg.InvalidCatalogNameError:
            return {"status": "error", "type": "database_not_exists", "message": "数据库不存在"}
        except asyncpg.InvalidPasswordError:
            return {"status": "error", "type": "auth_failed", "message": "认证失败"}
        except asyncpg.CannotConnectNowError:
            return {"status": "error", "type": "service_unavailable", "message": "服务不可用"}
        except ConnectionRefusedError:
            return {"status": "error", "type": "connection_refused", "message": "连接被拒绝"}
        except Exception as e:
            return {"status": "error", "type": "unknown", "message": str(e)}
    
    def _check_postgres_service(self) -> Dict[str, Any]:
        """检查PostgreSQL服务状态"""
        try:
            # 检查PostgreSQL进程
            postgres_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if 'postgres' in proc.info['name'].lower():
                        postgres_processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "status": proc.info['status']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if postgres_processes:
                return {
                    "status": "running",
                    "processes": postgres_processes,
                    "message": f"发现 {len(postgres_processes)} 个PostgreSQL进程"
                }
            else:
                return {
                    "status": "not_running",
                    "processes": [],
                    "message": "未发现PostgreSQL进程"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_port_availability(self) -> Dict[str, Any]:
        """检查端口可用性"""
        try:
            import socket
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            result = sock.connect_ex((
                self.connection_params["host"], 
                self.connection_params["port"]
            ))
            sock.close()
            
            if result == 0:
                return {"status": "open", "message": f"端口 {self.connection_params['port']} 可访问"}
            else:
                return {"status": "closed", "message": f"端口 {self.connection_params['port']} 不可访问"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _test_authentication(self) -> Dict[str, Any]:
        """测试认证"""
        try:
            # 尝试连接到默认数据库
            test_params = self.connection_params.copy()
            test_params["database"] = "postgres"  # 默认数据库
            
            conn = await asyncpg.connect(**test_params)
            await conn.close()
            
            return {"status": "success", "message": "认证成功"}
            
        except asyncpg.InvalidPasswordError:
            return {"status": "failed", "message": "用户名或密码错误"}
        except asyncpg.InvalidAuthorizationSpecificationError:
            return {"status": "failed", "message": "用户不存在或权限不足"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _check_database_exists(self) -> Dict[str, Any]:
        """检查数据库是否存在"""
        try:
            # 连接到默认数据库查询
            test_params = self.connection_params.copy()
            test_params["database"] = "postgres"
            
            conn = await asyncpg.connect(**test_params)
            
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.connection_params["database"]
            )
            
            await conn.close()
            
            if result:
                return {"status": "exists", "message": "数据库存在"}
            else:
                return {"status": "not_exists", "message": "数据库不存在"}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _check_permissions(self) -> Dict[str, Any]:
        """检查用户权限"""
        try:
            conn = await asyncpg.connect(**self.connection_params)
            
            # 检查基本权限
            permissions = {}
            
            # 检查连接权限
            permissions["connect"] = True
            
            # 检查创建表权限
            try:
                await conn.execute("CREATE TABLE IF NOT EXISTS test_permissions (id INTEGER)")
                await conn.execute("DROP TABLE test_permissions")
                permissions["create_table"] = True
            except:
                permissions["create_table"] = False
            
            # 检查扩展权限（pgvector）
            try:
                await conn.fetchval("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                permissions["vector_extension"] = True
            except:
                permissions["vector_extension"] = False
            
            await conn.close()
            
            return {"status": "success", "permissions": permissions}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _generate_db_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """生成数据库建议"""
        recommendations = []
        
        # 连接问题
        conn_test = diagnosis["connection_test"]
        if conn_test["status"] == "error":
            if conn_test["type"] == "connection_refused":
                recommendations.append("PostgreSQL服务未启动，请启动PostgreSQL服务")
            elif conn_test["type"] == "auth_failed":
                recommendations.append("检查数据库用户名和密码配置")
            elif conn_test["type"] == "database_not_exists":
                recommendations.append("创建目标数据库或检查数据库名称配置")
        
        # 服务状态
        service_status = diagnosis["service_status"]
        if service_status["status"] == "not_running":
            recommendations.append("启动PostgreSQL服务：sudo systemctl start postgresql")
        
        # 端口问题
        port_status = diagnosis["port_availability"]
        if port_status["status"] == "closed":
            recommendations.append("检查PostgreSQL配置文件中的监听地址和端口设置")
        
        # 数据库不存在
        db_exists = diagnosis["database_exists"]
        if db_exists["status"] == "not_exists":
            recommendations.append(f"创建数据库：CREATE DATABASE {self.connection_params['database']}")
        
        # 权限问题
        permissions = diagnosis.get("permissions", {})
        if permissions.get("status") == "success":
            perms = permissions.get("permissions", {})
            if not perms.get("create_table"):
                recommendations.append("用户缺少创建表权限，请授予相应权限")
            if not perms.get("vector_extension"):
                recommendations.append("安装pgvector扩展：CREATE EXTENSION vector")
        
        return recommendations
    
    def _print_diagnosis(self, diagnosis: Dict[str, Any]):
        """打印诊断结果"""
        print("\n🏥 数据库诊断结果")
        print("=" * 50)
        
        # 连接测试
        conn_test = diagnosis["connection_test"]
        status_emoji = "✅" if conn_test["status"] == "success" else "❌"
        print(f"{status_emoji} 连接测试: {conn_test['message']}")
        
        # 服务状态
        service = diagnosis["service_status"]
        status_emoji = "✅" if service["status"] == "running" else "❌"
        print(f"{status_emoji} 服务状态: {service['message']}")
        
        # 端口状态
        port = diagnosis["port_availability"]
        status_emoji = "✅" if port["status"] == "open" else "❌"
        print(f"{status_emoji} 端口状态: {port['message']}")
        
        # 认证测试
        auth = diagnosis["authentication"]
        status_emoji = "✅" if auth["status"] == "success" else "❌"
        print(f"{status_emoji} 认证测试: {auth['message']}")
        
        # 数据库存在性
        db_exists = diagnosis["database_exists"]
        status_emoji = "✅" if db_exists["status"] == "exists" else "❌"
        print(f"{status_emoji} 数据库存在: {db_exists['message']}")
        
        # 权限检查
        permissions = diagnosis["permissions"]
        if permissions["status"] == "success":
            perms = permissions["permissions"]
            print(f"🔐 权限检查:")
            print(f"  ✅ 连接权限: {'是' if perms.get('connect') else '否'}")
            print(f"  {'✅' if perms.get('create_table') else '❌'} 创建表权限: {'是' if perms.get('create_table') else '否'}")
            print(f"  {'✅' if perms.get('vector_extension') else '❌'} Vector扩展: {'已安装' if perms.get('vector_extension') else '未安装'}")
        
        # 建议
        if diagnosis["recommendations"]:
            print(f"\n💡 解决建议:")
            for rec in diagnosis["recommendations"]:
                print(f"  - {rec}")

# 使用示例
async def main():
    import os
    
    db_url = os.getenv("DATABASE_URL", "postgresql://mirix:mirix@localhost:5432/mirix")
    troubleshooter = DatabaseTroubleshooter(db_url)
    
    await troubleshooter.diagnose_connection_issues()

if __name__ == "__main__":
    asyncio.run(main())
```

### API服务问题

#### 1. 启动失败问题
```python
# scripts/api_troubleshoot.py
import subprocess
import sys
import os
import json
import time
from typing import Dict, Any, List
import requests

class APITroubleshooter:
    """API服务故障排除器"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.common_issues = {
            "port_in_use": "端口被占用",
            "import_error": "模块导入错误",
            "config_error": "配置错误",
            "dependency_error": "依赖错误",
            "database_error": "数据库连接错误"
        }
    
    def diagnose_startup_issues(self) -> Dict[str, Any]:
        """诊断启动问题"""
        print("🔍 诊断API服务启动问题...")
        
        diagnosis = {
            "port_check": self._check_port_usage(),
            "config_validation": self._validate_config(),
            "dependency_check": self._check_dependencies(),
            "import_test": self._test_imports(),
            "database_connectivity": self._test_database_connection(),
            "startup_test": self._test_startup()
        }
        
        diagnosis["recommendations"] = self._generate_api_recommendations(diagnosis)
        self._print_api_diagnosis(diagnosis)
        
        return diagnosis
    
    def _check_port_usage(self) -> Dict[str, Any]:
        """检查端口使用情况"""
        try:
            import psutil
            
            port = 8000  # 默认端口
            connections = psutil.net_connections()
            
            port_users = []
            for conn in connections:
                if conn.laddr and conn.laddr.port == port:
                    try:
                        process = psutil.Process(conn.pid)
                        port_users.append({
                            "pid": conn.pid,
                            "name": process.name(),
                            "status": conn.status
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        port_users.append({
                            "pid": conn.pid,
                            "name": "unknown",
                            "status": conn.status
                        })
            
            if port_users:
                return {
                    "status": "occupied",
                    "port": port,
                    "users": port_users,
                    "message": f"端口 {port} 被占用"
                }
            else:
                return {
                    "status": "available",
                    "port": port,
                    "message": f"端口 {port} 可用"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _validate_config(self) -> Dict[str, Any]:
        """验证配置"""
        try:
            config_issues = []
            
            # 检查环境变量
            required_env_vars = [
                "DATABASE_URL",
                "OPENAI_API_KEY"
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                config_issues.append(f"缺少环境变量: {', '.join(missing_vars)}")
            
            # 检查配置文件
            config_files = [".env", "config.yaml", "settings.py"]
            existing_configs = []
            
            for config_file in config_files:
                if os.path.exists(config_file):
                    existing_configs.append(config_file)
            
            if not existing_configs:
                config_issues.append("未找到配置文件")
            
            if config_issues:
                return {
                    "status": "invalid",
                    "issues": config_issues,
                    "message": "配置验证失败"
                }
            else:
                return {
                    "status": "valid",
                    "message": "配置验证通过"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖"""
        try:
            # 检查关键依赖
            critical_packages = [
                "fastapi",
                "uvicorn",
                "sqlalchemy",
                "asyncpg",
                "pydantic"
            ]
            
            missing_packages = []
            version_info = {}
            
            for package in critical_packages:
                try:
                    result = subprocess.run([
                        sys.executable, "-c", f"import {package}; print({package}.__version__)"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        version_info[package] = result.stdout.strip()
                    else:
                        missing_packages.append(package)
                        
                except subprocess.TimeoutExpired:
                    missing_packages.append(f"{package} (timeout)")
                except Exception:
                    missing_packages.append(f"{package} (error)")
            
            if missing_packages:
                return {
                    "status": "missing",
                    "missing_packages": missing_packages,
                    "installed_packages": version_info,
                    "message": f"缺少关键依赖: {', '.join(missing_packages)}"
                }
            else:
                return {
                    "status": "complete",
                    "installed_packages": version_info,
                    "message": "所有关键依赖已安装"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_imports(self) -> Dict[str, Any]:
        """测试模块导入"""
        try:
            # 测试关键模块导入
            test_imports = [
                "from mirix.server.fastapi_server import app",
                "from mirix.orm.base import Base",
                "from mirix.services.agent_service import AgentService",
                "import uvicorn",
                "import fastapi"
            ]
            
            import_results = {}
            failed_imports = []
            
            for import_stmt in test_imports:
                try:
                    result = subprocess.run([
                        sys.executable, "-c", import_stmt
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        import_results[import_stmt] = "success"
                    else:
                        import_results[import_stmt] = result.stderr.strip()
                        failed_imports.append(import_stmt)
                        
                except subprocess.TimeoutExpired:
                    import_results[import_stmt] = "timeout"
                    failed_imports.append(import_stmt)
                except Exception as e:
                    import_results[import_stmt] = str(e)
                    failed_imports.append(import_stmt)
            
            if failed_imports:
                return {
                    "status": "failed",
                    "failed_imports": failed_imports,
                    "results": import_results,
                    "message": f"{len(failed_imports)} 个导入失败"
                }
            else:
                return {
                    "status": "success",
                    "results": import_results,
                    "message": "所有模块导入成功"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_database_connection(self) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                return {
                    "status": "no_config",
                    "message": "未配置DATABASE_URL"
                }
            
            # 简单的连接测试
            result = subprocess.run([
                sys.executable, "-c", 
                f"""
import asyncio
import asyncpg
import os

async def test_db():
    try:
        conn = await asyncpg.connect('{db_url}')
        await conn.close()
        print('success')
    except Exception as e:
        print(f'error: {{e}}')

asyncio.run(test_db())
"""
            ], capture_output=True, text=True, timeout=30)
            
            if "success" in result.stdout:
                return {
                    "status": "connected",
                    "message": "数据库连接成功"
                }
            else:
                return {
                    "status": "failed",
                    "error": result.stdout.strip(),
                    "message": "数据库连接失败"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_startup(self) -> Dict[str, Any]:
        """测试启动"""
        try:
            print("🚀 测试API服务启动...")
            
            # 尝试启动服务（短时间）
            startup_cmd = [
                sys.executable, "-m", "uvicorn", 
                "mirix.server.fastapi_server:app",
                "--host", "0.0.0.0",
                "--port", "8001",  # 使用不同端口避免冲突
                "--timeout-keep-alive", "5"
            ]
            
            process = subprocess.Popen(
                startup_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待几秒钟
            time.sleep(5)
            
            # 检查进程状态
            if process.poll() is None:
                # 进程仍在运行，尝试访问
                try:
                    response = requests.get("http://localhost:8001/health", timeout=5)
                    if response.status_code == 200:
                        result = {
                            "status": "success",
                            "message": "服务启动成功"
                        }
                    else:
                        result = {
                            "status": "partial",
                            "message": f"服务启动但响应异常: {response.status_code}"
                        }
                except requests.RequestException as e:
                    result = {
                        "status": "no_response",
                        "message": f"服务启动但无响应: {e}"
                    }
                
                # 终止测试进程
                process.terminate()
                process.wait(timeout=5)
                
            else:
                # 进程已退出
                stdout, stderr = process.communicate()
                result = {
                    "status": "failed",
                    "exit_code": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "message": "服务启动失败"
                }
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _generate_api_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """生成API建议"""
        recommendations = []
        
        # 端口问题
        port_check = diagnosis["port_check"]
        if port_check["status"] == "occupied":
            recommendations.append("终止占用端口的进程或使用不同端口启动服务")
        
        # 配置问题
        config_validation = diagnosis["config_validation"]
        if config_validation["status"] == "invalid":
            for issue in config_validation.get("issues", []):
                recommendations.append(f"配置问题: {issue}")
        
        # 依赖问题
        dependency_check = diagnosis["dependency_check"]
        if dependency_check["status"] == "missing":
            recommendations.append("安装缺少的依赖: pip install -r requirements.txt")
        
        # 导入问题
        import_test = diagnosis["import_test"]
        if import_test["status"] == "failed":
            recommendations.append("修复模块导入问题，检查Python路径和模块结构")
        
        # 数据库问题
        db_connectivity = diagnosis["database_connectivity"]
        if db_connectivity["status"] in ["no_config", "failed"]:
            recommendations.append("配置正确的数据库连接字符串")
        
        # 启动问题
        startup_test = diagnosis["startup_test"]
        if startup_test["status"] == "failed":
            recommendations.append("检查启动日志，修复配置或代码错误")
        
        return recommendations
    
    def _print_api_diagnosis(self, diagnosis: Dict[str, Any]):
        """打印API诊断结果"""
        print("\n🔧 API服务诊断结果")
        print("=" * 50)
        
        checks = [
            ("端口检查", "port_check"),
            ("配置验证", "config_validation"),
            ("依赖检查", "dependency_check"),
            ("导入测试", "import_test"),
            ("数据库连接", "database_connectivity"),
            ("启动测试", "startup_test")
        ]
        
        for name, key in checks:
            result = diagnosis[key]
            status = result["status"]
            
            if status in ["success", "complete", "connected", "valid", "available"]:
                emoji = "✅"
            elif status in ["partial", "warning"]:
                emoji = "⚠️"
            else:
                emoji = "❌"
            
            print(f"{emoji} {name}: {result['message']}")
        
        # 建议
        if diagnosis["recommendations"]:
            print(f"\n💡 解决建议:")
            for rec in diagnosis["recommendations"]:
                print(f"  - {rec}")

# 使用示例
def main():
    troubleshooter = APITroubleshooter()
    troubleshooter.diagnose_startup_issues()

if __name__ == "__main__":
    main()
```

### 智能体问题解决

#### 1. Agent创建失败
```python
# 常见问题和解决方案

# 问题1: 模型配置错误
# 症状: Agent创建时报告模型不可用
# 解决方案:
def fix_model_config():
    """修复模型配置"""
    import os
    
    # 检查API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ 未设置OPENAI_API_KEY环境变量")
        return False
    
    # 验证API密钥
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # 测试API调用
        response = client.models.list()
        print("✅ OpenAI API连接正常")
        
        # 检查可用模型
        available_models = [model.id for model in response.data]
        recommended_models = ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
        
        usable_models = [m for m in recommended_models if m in available_models]
        if usable_models:
            print(f"✅ 可用模型: {', '.join(usable_models)}")
            return True
        else:
            print("⚠️ 未找到推荐的模型")
            return False
            
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

# 问题2: 内存系统初始化失败
# 解决方案:
async def fix_memory_system():
    """修复内存系统"""
    try:
        from mirix.orm.base import Base
        from mirix.database import engine
        
        # 创建数据库表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ 内存系统数据库表创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 内存系统初始化失败: {e}")
        return False

# 问题3: 权限不足
# 解决方案:
def check_agent_permissions():
    """检查Agent权限"""
    # 实现权限检查逻辑
    pass
```

#### 2. 对话异常处理
```python
# scripts/chat_troubleshoot.py
import asyncio
import json
from typing import Dict, Any, List, Optional

class ChatTroubleshooter:
    """对话故障排除器"""
    
    def __init__(self):
        self.common_issues = {
            "token_limit": "Token限制超出",
            "model_error": "模型调用错误",
            "memory_error": "记忆系统错误",
            "timeout": "响应超时",
            "format_error": "响应格式错误"
        }
    
    async def diagnose_chat_issues(self, agent_id: str, conversation_id: str = None) -> Dict[str, Any]:
        """诊断对话问题"""
        print(f"🔍 诊断Agent {agent_id} 的对话问题...")
        
        diagnosis = {
            "agent_status": await self._check_agent_status(agent_id),
            "model_availability": await self._check_model_availability(agent_id),
            "memory_integrity": await self._check_memory_integrity(agent_id),
            "conversation_history": await self._analyze_conversation_history(agent_id, conversation_id),
            "token_usage": await self._analyze_token_usage(agent_id),
            "error_patterns": await self._analyze_error_patterns(agent_id)
        }
        
        diagnosis["recommendations"] = self._generate_chat_recommendations(diagnosis)
        self._print_chat_diagnosis(diagnosis)
        
        return diagnosis
    
    async def _check_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """检查Agent状态"""
        try:
            # 这里应该调用实际的Agent服务
            # 示例实现
            from mirix.services.agent_service import AgentService
            
            agent_service = AgentService()
            agent = await agent_service.get_agent(agent_id)
            
            if agent:
                return {
                    "status": "active",
                    "agent_info": {
                        "id": agent.id,
                        "name": agent.name,
                        "model": agent.model,
                        "created_at": agent.created_at.isoformat()
                    },
                    "message": "Agent状态正常"
                }
            else:
                return {
                    "status": "not_found",
                    "message": "Agent不存在"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _check_model_availability(self, agent_id: str) -> Dict[str, Any]:
        """检查模型可用性"""
        try:
            # 获取Agent的模型配置
            from mirix.services.agent_service import AgentService
            
            agent_service = AgentService()
            agent = await agent_service.get_agent(agent_id)
            
            if not agent:
                return {"status": "no_agent", "message": "Agent不存在"}
            
            model_name = agent.model
            
            # 测试模型调用
            import openai
            client = openai.OpenAI()
            
            try:
                response = await client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                
                return {
                    "status": "available",
                    "model": model_name,
                    "message": "模型可用"
                }
                
            except openai.RateLimitError:
                return {
                    "status": "rate_limited",
                    "model": model_name,
                    "message": "模型调用频率限制"
                }
            except openai.AuthenticationError:
                return {
                    "status": "auth_error",
                    "model": model_name,
                    "message": "API认证错误"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "model": model_name,
                    "message": str(e)
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _check_memory_integrity(self, agent_id: str) -> Dict[str, Any]:
        """检查记忆完整性"""
        try:
            from mirix.services.memory_service import MemoryService
            
            memory_service = MemoryService()
            
            # 检查核心记忆
            core_memory = await memory_service.get_core_memory(agent_id)
            
            # 检查对话历史
            conversation_count = await memory_service.get_conversation_count(agent_id)
            
            # 检查记忆索引
            memory_index_status = await memory_service.check_memory_index(agent_id)
            
            issues = []
            if not core_memory:
                issues.append("核心记忆为空")
            
            if conversation_count == 0:
                issues.append("无对话历史")
            
            if not memory_index_status:
                issues.append("记忆索引异常")
            
            if issues:
                return {
                    "status": "issues",
                    "issues": issues,
                    "message": f"发现 {len(issues)} 个记忆问题"
                }
            else:
                return {
                    "status": "healthy",
                    "core_memory_size": len(core_memory) if core_memory else 0,
                    "conversation_count": conversation_count,
                    "message": "记忆系统正常"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _analyze_conversation_history(self, agent_id: str, conversation_id: str = None) -> Dict[str, Any]:
        """分析对话历史"""
        try:
            from mirix.services.message_service import MessageService
            
            message_service = MessageService()
            
            # 获取最近的对话
            recent_messages = await message_service.get_recent_messages(
                agent_id, 
                conversation_id=conversation_id,
                limit=50
            )
            
            if not recent_messages:
                return {
                    "status": "no_history",
                    "message": "无对话历史"
                }
            
            # 分析对话模式
            analysis = {
                "total_messages": len(recent_messages),
                "user_messages": len([m for m in recent_messages if m.role == "user"]),
                "assistant_messages": len([m for m in recent_messages if m.role == "assistant"]),
                "error_messages": len([m for m in recent_messages if "error" in m.content.lower()]),
                "avg_response_length": sum(len(m.content) for m in recent_messages if m.role == "assistant") / max(1, len([m for m in recent_messages if m.role == "assistant"]))
            }
            
            # 检查异常模式
            issues = []
            if analysis["error_messages"] > analysis["total_messages"] * 0.1:
                issues.append("错误消息比例过高")
            
            if analysis["avg_response_length"] < 10:
                issues.append("响应内容过短")
            
            if analysis["user_messages"] > analysis["assistant_messages"] * 2:
                issues.append("响应不足，可能存在处理问题")
            
            return {
                "status": "analyzed",
                "analysis": analysis,
                "issues": issues,
                "message": f"分析了 {analysis['total_messages']} 条消息"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _analyze_token_usage(self, agent_id: str) -> Dict[str, Any]:
        """分析Token使用情况"""
        try:
            # 这里应该从日志或数据库中获取Token使用统计
            # 示例实现
            
            # 模拟Token使用数据
            token_stats = {
                "total_tokens_used": 15000,
                "avg_tokens_per_request": 500,
                "max_tokens_per_request": 2000,
                "requests_near_limit": 3
            }
            
            issues = []
            if token_stats["avg_tokens_per_request"] > 1000:
                issues.append("平均Token使用量较高")
            
            if token_stats["requests_near_limit"] > 0:
                issues.append(f"{token_stats['requests_near_limit']} 次请求接近Token限制")
            
            return {
                "status": "analyzed",
                "stats": token_stats,
                "issues": issues,
                "message": "Token使用分析完成"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _analyze_error_patterns(self, agent_id: str) -> Dict[str, Any]:
        """分析错误模式"""
        try:
            # 从日志中分析错误模式
            # 这里应该实现实际的日志分析逻辑
            
            error_patterns = {
                "timeout_errors": 2,
                "model_errors": 1,
                "memory_errors": 0,
                "format_errors": 3
            }
            
            total_errors = sum(error_patterns.values())
            
            if total_errors == 0:
                return {
                    "status": "no_errors",
                    "message": "未发现错误模式"
                }
            
            # 找出主要错误类型
            main_error = max(error_patterns.items(), key=lambda x: x[1])
            
            return {
                "status": "found_patterns",
                "patterns": error_patterns,
                "total_errors": total_errors,
                "main_error_type": main_error[0],
                "main_error_count": main_error[1],
                "message": f"发现 {total_errors} 个错误，主要类型: {main_error[0]}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _generate_chat_recommendations(self, diagnosis: Dict[str, Any]) -> List[str]:
        """生成对话建议"""
        recommendations = []
        
        # Agent状态问题
        agent_status = diagnosis["agent_status"]
        if agent_status["status"] == "not_found":
            recommendations.append("重新创建Agent或检查Agent ID")
        
        # 模型可用性问题
        model_availability = diagnosis["model_availability"]
        if model_availability["status"] == "rate_limited":
            recommendations.append("降低请求频率或升级API计划")
        elif model_availability["status"] == "auth_error":
            recommendations.append("检查OpenAI API密钥配置")
        elif model_availability["status"] == "error":
            recommendations.append("检查模型名称和API配置")
        
        # 记忆问题
        memory_integrity = diagnosis["memory_integrity"]
        if memory_integrity["status"] == "issues":
            for issue in memory_integrity.get("issues", []):
                recommendations.append(f"记忆问题: {issue}")
        
        # 对话历史问题
        conversation_history = diagnosis["conversation_history"]
        if conversation_history["status"] == "analyzed":
            for issue in conversation_history.get("issues", []):
                recommendations.append(f"对话问题: {issue}")
        
        # Token使用问题
        token_usage = diagnosis["token_usage"]
        if token_usage["status"] == "analyzed":
            for issue in token_usage.get("issues", []):
                recommendations.append(f"Token问题: {issue}")
        
        # 错误模式问题
        error_patterns = diagnosis["error_patterns"]
        if error_patterns["status"] == "found_patterns":
            main_error = error_patterns["main_error_type"]
            if main_error == "timeout_errors":
                recommendations.append("增加请求超时时间或优化响应速度")
            elif main_error == "model_errors":
                recommendations.append("检查模型配置和API状态")
            elif main_error == "format_errors":
                recommendations.append("检查响应格式处理逻辑")
        
        return recommendations
    
    def _print_chat_diagnosis(self, diagnosis: Dict[str, Any]):
        """打印对话诊断结果"""
        print("\n💬 对话系统诊断结果")
        print("=" * 50)
        
        checks = [
            ("Agent状态", "agent_status"),
            ("模型可用性", "model_availability"),
            ("记忆完整性", "memory_integrity"),
            ("对话历史", "conversation_history"),
            ("Token使用", "token_usage"),
            ("错误模式", "error_patterns")
        ]
        
        for name, key in checks:
            result = diagnosis[key]
            status = result["status"]
            
            if status in ["active", "available", "healthy", "no_errors", "no_history"]:
                emoji = "✅"
            elif status in ["analyzed", "found_patterns"]:
                emoji = "📊"
            else:
                emoji = "❌"
            
            print(f"{emoji} {name}: {result['message']}")
        
        # 建议
        if diagnosis["recommendations"]:
            print(f"\n💡 解决建议:")
            for rec in diagnosis["recommendations"]:
                print(f"  - {rec}")

# 使用示例
async def main():
    troubleshooter = ChatTroubleshooter()
    await troubleshooter.diagnose_chat_issues("agent_123")

if __name__ == "__main__":
    asyncio.run(main())
```

### 性能问题解决

#### 1. 响应慢问题
```python
# 性能优化建议

# 1. 数据库查询优化
def optimize_database_queries():
    """数据库查询优化"""
    optimizations = [
        "添加适当的数据库索引",
        "使用查询缓存",
        "优化复杂查询",
        "使用连接池",
        "实施读写分离"
    ]
    return optimizations

# 2. 缓存策略
def implement_caching():
    """实施缓存策略"""
    cache_strategies = [
        "Redis缓存热点数据",
        "内存缓存频繁访问的配置",
        "CDN缓存静态资源",
        "应用层缓存计算结果"
    ]
    return cache_strategies

# 3. 异步处理优化
def optimize_async_processing():
    """异步处理优化"""
    optimizations = [
        "使用异步数据库操作",
        "实施任务队列处理长时间操作",
        "优化并发处理",
        "使用连接池管理"
    ]
    return optimizations
```

#### 2. 内存泄漏检测
```python
# scripts/memory_leak_detector.py
import psutil
import time
import gc
import tracemalloc
from typing import Dict, List, Any
import matplotlib.pyplot as plt

class MemoryLeakDetector:
    """内存泄漏检测器"""
    
    def __init__(self):
        self.snapshots = []
        self.process = psutil.Process()
        tracemalloc.start()
    
    def start_monitoring(self, duration_minutes: int = 30, interval_seconds: int = 60):
        """开始内存监控"""
        print(f"🔍 开始内存泄漏检测，持续{duration_minutes}分钟")
        
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            self._take_snapshot()
            time.sleep(interval_seconds)
        
        self._analyze_memory_trend()
    
    def _take_snapshot(self):
        """获取内存快照"""
        # 系统内存信息
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        # Python内存跟踪
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        # 垃圾回收信息
        gc_stats = gc.get_stats()
        
        snapshot_data = {
            "timestamp": time.time(),
            "rss": memory_info.rss,  # 物理内存
            "vms": memory_info.vms,  # 虚拟内存
            "percent": memory_percent,
            "python_memory": sum(stat.size for stat in top_stats),
            "gc_collections": sum(gen['collections'] for gen in gc_stats),
            "top_memory_lines": [(stat.traceback.format()[-1], stat.size) for stat in top_stats[:10]]
        }
        
        self.snapshots.append(snapshot_data)
        
        print(f"📊 {time.strftime('%H:%M:%S')} - 内存: {memory_percent:.1f}%, RSS: {memory_info.rss / 1024 / 1024:.1f}MB")
    
    def _analyze_memory_trend(self):
        """分析内存趋势"""
        if len(self.snapshots) < 3:
            print("❌ 快照数量不足，无法分析趋势")
            return
        
        print("\n📈 内存泄漏分析结果")
        print("=" * 50)
        
        # 计算内存增长趋势
        first_snapshot = self.snapshots[0]
        last_snapshot = self.snapshots[-1]
        
        rss_growth = last_snapshot["rss"] - first_snapshot["rss"]
        python_memory_growth = last_snapshot["python_memory"] - first_snapshot["python_memory"]
        
        duration_hours = (last_snapshot["timestamp"] - first_snapshot["timestamp"]) / 3600
        
        print(f"📅 监控时长: {duration_hours:.1f} 小时")
        print(f"📊 RSS内存变化: {rss_growth / 1024 / 1024:.1f} MB")
        print(f"🐍 Python内存变化: {python_memory_growth / 1024 / 1024:.1f} MB")
        
        # 判断是否存在内存泄漏
        rss_growth_rate = rss_growth / duration_hours / 1024 / 1024  # MB/hour
        
        if rss_growth_rate > 10:  # 每小时增长超过10MB
            print(f"⚠️ 可能存在内存泄漏，增长率: {rss_growth_rate:.1f} MB/小时")
            self._identify_leak_sources()
        elif rss_growth_rate > 5:
            print(f"⚠️ 内存增长较快，需要关注，增长率: {rss_growth_rate:.1f} MB/小时")
        else:
            print(f"✅ 内存使用正常，增长率: {rss_growth_rate:.1f} MB/小时")
        
        # 生成图表
        self._create_memory_chart()
    
    def _identify_leak_sources(self):
        """识别泄漏源"""
        print("\n🔍 分析可能的泄漏源:")
        
        # 分析最后几个快照中的热点内存使用
        recent_snapshots = self.snapshots[-3:]
        
        # 统计频繁出现的内存热点
        line_frequency = {}
        for snapshot in recent_snapshots:
            for line, size in snapshot["top_memory_lines"]:
                if line not in line_frequency:
                    line_frequency[line] = []
                line_frequency[line].append(size)
        
        # 找出持续增长的内存使用点
        growing_lines = []
        for line, sizes in line_frequency.items():
            if len(sizes) >= 2 and sizes[-1] > sizes[0] * 1.2:  # 增长超过20%
                growing_lines.append((line, sizes[-1] - sizes[0]))
        
        if growing_lines:
            print("📍 可能的泄漏点:")
            for line, growth in sorted(growing_lines, key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {line}: +{growth / 1024:.1f} KB")
        else:
            print("🤔 未发现明显的泄漏点，可能是系统级别的内存增长")
    
    def _create_memory_chart(self):
        """创建内存使用图表"""
        try:
            timestamps = [s["timestamp"] for s in self.snapshots]
            rss_values = [s["rss"] / 1024 / 1024 for s in self.snapshots]  # MB
            python_memory = [s["python_memory"] / 1024 / 1024 for s in self.snapshots]  # MB
            
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            plt.plot(timestamps, rss_values, 'b-', label='RSS Memory')
            plt.xlabel('时间')
            plt.ylabel('内存使用 (MB)')
            plt.title('系统内存使用趋势')
            plt.legend()
            plt.grid(True)
            
            plt.subplot(1, 2, 2)
            plt.plot(timestamps, python_memory, 'r-', label='Python Memory')
            plt.xlabel('时间')
            plt.ylabel('内存使用 (MB)')
            plt.title('Python内存使用趋势')
            plt.legend()
            plt.grid(True)
            
            plt.tight_layout()
            
            chart_filename = f"memory_analysis_{int(time.time())}.png"
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            print(f"\n📊 内存分析图表已保存: {chart_filename}")
            
        except Exception as e:
            print(f"⚠️ 生成图表失败: {e}")

# 使用示例
def main():
    detector = MemoryLeakDetector()
    
    # 监控30分钟，每分钟检查一次
    detector.start_monitoring(duration_minutes=30, interval_seconds=60)

if __name__ == "__main__":
    main()
```

---

## 📚 常见问题快速索引

### 系统启动问题
| 问题症状 | 可能原因 | 快速解决 |
|---------|---------|---------|
| 端口被占用 | 其他进程占用8000端口 | `lsof -i :8000` 查看并终止进程 |
| 模块导入错误 | Python路径或依赖问题 | 重新安装依赖，检查PYTHONPATH |
| 数据库连接失败 | PostgreSQL未启动或配置错误 | 启动PostgreSQL，检查连接字符串 |
| 权限错误 | 文件或目录权限不足 | 修改文件权限或使用正确用户 |

### API服务问题
| 问题症状 | 可能原因 | 快速解决 |
|---------|---------|---------|
| 404错误 | 路由配置错误 | 检查路由定义和URL路径 |
| 500错误 | 服务器内部错误 | 查看错误日志，修复代码问题 |
| 超时错误 | 请求处理时间过长 | 优化查询，增加超时时间 |
| 认证失败 | API密钥或认证配置错误 | 检查认证中间件和密钥配置 |

### 智能体问题
| 问题症状 | 可能原因 | 快速解决 |
|---------|---------|---------|
| Agent创建失败 | 模型配置或权限问题 | 检查OpenAI API密钥和模型名称 |
| 对话无响应 | 模型调用失败或超时 | 检查API状态和网络连接 |
| 记忆丢失 | 数据库问题或索引异常 | 重建记忆索引，检查数据完整性 |
| 响应格式错误 | 模型输出解析失败 | 更新响应解析逻辑 |

### 性能问题
| 问题症状 | 可能原因 | 快速解决 |
|---------|---------|---------|
| 响应慢 | 数据库查询慢或资源不足 | 添加索引，优化查询，增加资源 |
| 内存占用高 | 内存泄漏或缓存过多 | 重启服务，检查内存使用 |
| CPU占用高 | 计算密集任务或死循环 | 分析CPU热点，优化算法 |
| 磁盘空间不足 | 日志文件过大或数据积累 | 清理日志，归档旧数据 |

---

## 🚨 紧急故障处理流程

### P0级别故障（系统完全不可用）
1. **立即响应**（5分钟内）
   - 确认故障范围和影响
   - 启动应急预案
   - 通知相关人员

2. **快速诊断**（15分钟内）
   - 运行健康检查脚本
   - 查看系统监控和日志
   - 确定根本原因

3. **紧急修复**（30分钟内）
   - 实施临时解决方案
   - 恢复核心功能
   - 验证修复效果

4. **后续处理**
   - 实施永久解决方案
   - 更新文档和预案
   - 进行故障复盘

### 应急命令清单
```bash
# 快速重启服务
sudo systemctl restart mirix-api
sudo systemctl restart postgresql
sudo systemctl restart redis

# 检查服务状态
sudo systemctl status mirix-api
sudo systemctl status postgresql
sudo systemctl status redis

# 查看实时日志
tail -f /var/log/mirix/api.log
tail -f /var/log/postgresql/postgresql.log

# 检查资源使用
htop
df -h
free -h

# 网络连接检查
netstat -tulpn | grep :8000
curl -I http://localhost:8000/health
```

---

## 📞 支持和联系

### 获取帮助
- **文档**: 查看完整的技术文档
- **日志**: 检查系统日志获取详细错误信息
- **监控**: 使用性能监控工具分析问题
- **社区**: 参与开源社区讨论

### 报告问题
提交问题时请包含：
- 问题详细描述和重现步骤
- 错误日志和堆栈跟踪
- 系统环境信息
- 已尝试的解决方案

---

**🎯 记住**: 大多数问题都有标准的解决方案。遇到问题时，首先查看本指南的快速索引，然后使用相应的诊断工具进行深入分析。保持冷静，系统性地排查问题，通常能够快速找到解决方案。
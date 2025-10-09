"""
MIRIX MCP Server - STDIO 传输实现

该模块实现基于标准输入输出的 MCP 传输协议。
提供与客户端通过 stdin/stdout 进行 JSON-RPC 通信的功能。

主要功能：
1. JSON-RPC 消息解析和序列化
2. 异步消息读取和写入
3. 错误处理和连接管理
4. 协议兼容性处理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional, AsyncIterator
from contextlib import asynccontextmanager

from ..exceptions import TransportError, ValidationError
from ..utils import performance_monitor

# 配置日志
logger = logging.getLogger(__name__)


class StdioTransport:
    """
    STDIO 传输实现
    
    提供基于标准输入输出的 MCP 传输功能。
    支持 JSON-RPC 协议的消息交换。
    """
    
    def __init__(self):
        """初始化 STDIO 传输"""
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self._closed = False
        
        logger.info("STDIO 传输初始化完成")
    
    async def initialize(self) -> None:
        """
        初始化传输连接
        
        设置标准输入输出流的异步读写器。
        
        Raises:
            TransportError: 初始化失败
        """
        try:
            # 创建标准输入的异步读取器
            self.reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(self.reader)
            
            # 连接到标准输入
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            
            # 创建标准输出的异步写入器
            transport, protocol = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin, sys.stdout
            )
            self.writer = asyncio.StreamWriter(transport, protocol, self.reader, loop)
            
            logger.info("STDIO 传输连接已建立")
            
        except Exception as e:
            logger.error(f"STDIO 传输初始化失败: {e}")
            raise TransportError(f"传输初始化失败: {e}")
    
    @performance_monitor
    async def read_message(self) -> Optional[Dict[str, Any]]:
        """
        读取消息
        
        从标准输入读取 JSON-RPC 消息。
        
        Returns:
            Optional[Dict[str, Any]]: 解析后的消息，连接关闭时返回 None
            
        Raises:
            TransportError: 消息读取或解析失败
        """
        if self._closed or not self.reader:
            return None
        
        try:
            # 读取一行数据
            line = await self.reader.readline()
            
            if not line:
                logger.info("连接已关闭")
                return None
            
            # 解码和解析 JSON
            message_text = line.decode('utf-8').strip()
            if not message_text:
                return await self.read_message()  # 跳过空行
            
            message = json.loads(message_text)
            logger.debug(f"收到消息: {message}")
            
            return message
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            raise ValidationError(f"消息格式错误: {e}")
        except Exception as e:
            logger.error(f"消息读取失败: {e}")
            raise TransportError(f"消息读取失败: {e}")
    
    @performance_monitor
    async def write_message(self, message: Dict[str, Any]) -> None:
        """
        写入消息
        
        将消息序列化为 JSON 并写入标准输出。
        
        Args:
            message: 要发送的消息
            
        Raises:
            TransportError: 消息写入失败
        """
        if self._closed or not self.writer:
            raise TransportError("传输连接已关闭")
        
        try:
            # 序列化消息
            message_text = json.dumps(message, ensure_ascii=False)
            message_bytes = (message_text + '\n').encode('utf-8')
            
            # 写入数据
            self.writer.write(message_bytes)
            await self.writer.drain()
            
            logger.debug(f"发送消息: {message}")
            
        except Exception as e:
            logger.error(f"消息写入失败: {e}")
            raise TransportError(f"消息写入失败: {e}")
    
    async def close(self) -> None:
        """关闭传输连接"""
        if self._closed:
            return
        
        try:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()
            
            self._closed = True
            logger.info("STDIO 传输连接已关闭")
            
        except Exception as e:
            logger.error(f"关闭传输连接失败: {e}")
    
    @property
    def is_closed(self) -> bool:
        """检查连接是否已关闭"""
        return self._closed
    
    @asynccontextmanager
    async def connection(self):
        """传输连接上下文管理器"""
        try:
            await self.initialize()
            yield self
        finally:
            await self.close()
    
    async def message_stream(self) -> AsyncIterator[Dict[str, Any]]:
        """
        消息流迭代器
        
        持续读取消息直到连接关闭。
        
        Yields:
            Dict[str, Any]: 接收到的消息
        """
        while not self._closed:
            try:
                message = await self.read_message()
                if message is None:
                    break
                yield message
            except Exception as e:
                logger.error(f"消息流读取错误: {e}")
                break


class StdioServer:
    """
    基于 STDIO 的 MCP 服务器
    
    使用 STDIO 传输实现完整的 MCP 服务器功能。
    """
    
    def __init__(self, message_handler):
        """
        初始化 STDIO 服务器
        
        Args:
            message_handler: 消息处理器函数
        """
        self.transport = StdioTransport()
        self.message_handler = message_handler
        self._running = False
        
        logger.info("STDIO 服务器初始化完成")
    
    async def start(self) -> None:
        """
        启动服务器
        
        开始监听和处理消息。
        
        Raises:
            TransportError: 服务器启动失败
        """
        if self._running:
            logger.warning("服务器已在运行")
            return
        
        try:
            logger.info("启动 STDIO MCP 服务器...")
            
            async with self.transport.connection():
                self._running = True
                
                # 处理消息流
                async for message in self.transport.message_stream():
                    try:
                        # 处理消息
                        response = await self.message_handler(message)
                        
                        # 发送响应
                        if response:
                            await self.transport.write_message(response)
                            
                    except Exception as e:
                        logger.error(f"消息处理失败: {e}")
                        
                        # 发送错误响应
                        error_response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "error": {
                                "code": -32603,
                                "message": "Internal error",
                                "data": str(e)
                            }
                        }
                        await self.transport.write_message(error_response)
            
            logger.info("STDIO 服务器已停止")
            
        except Exception as e:
            logger.error(f"STDIO 服务器运行失败: {e}")
            raise TransportError(f"服务器运行失败: {e}")
        finally:
            self._running = False
    
    async def stop(self) -> None:
        """停止服务器"""
        if not self._running:
            return
        
        logger.info("停止 STDIO 服务器...")
        await self.transport.close()
        self._running = False
    
    @property
    def is_running(self) -> bool:
        """检查服务器是否在运行"""
        return self._running


# 便捷函数
async def run_stdio_server(message_handler) -> None:
    """
    运行 STDIO 服务器的便捷函数
    
    Args:
        message_handler: 消息处理器函数
    """
    server = StdioServer(message_handler)
    await server.start()


@asynccontextmanager
async def stdio_transport():
    """STDIO 传输的上下文管理器"""
    transport = StdioTransport()
    async with transport.connection():
        yield transport
"""
MIRIX MCP Server - Resource Upload Tool

该模块实现资源上传功能，允许将文档和文件上传到 MIRIX 资源记忆系统。
支持多种文件格式，包括文本、Markdown、Excel、CSV 等。

主要功能：
1. 文档上传到资源记忆系统
2. 支持多种文件格式处理
3. Base64 编码内容处理
4. 文件类型验证和大小限制
5. 完整的参数验证和错误处理

作者：MIRIX MCP Server Team
版本：1.0.0
"""

import base64
import logging
import mimetypes
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..mirix_adapter import MIRIXAdapter
from ..exceptions import (
    MCPServerError,
    MIRIXClientError,
    MemoryToolError,
    ValidationError
)
from ..utils import truncate_string, sanitize_filename

# 配置日志记录器
logger = logging.getLogger(__name__)

# 支持的文件类型常量
SUPPORTED_FILE_TYPES = [
    "text/plain",           # .txt
    "text/markdown",        # .md
    "text/csv",             # .csv
    "application/vnd.ms-excel",  # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/json",     # .json
    "application/xml",      # .xml
    "text/html",           # .html
    "application/pdf",     # .pdf (如果后端支持)
]

# 文件扩展名到MIME类型的映射
FILE_EXTENSION_MAPPING = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".csv": "text/csv",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".json": "application/json",
    ".xml": "application/xml",
    ".html": "text/html",
    ".htm": "text/html",
    ".pdf": "application/pdf",
}

# 上传配置常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MIN_FILE_SIZE = 1                  # 1 byte
MAX_FILENAME_LENGTH = 255          # 最大文件名长度


class ResourceUploadTool:
    """
    资源上传工具类
    
    提供将文档和文件上传到 MIRIX 资源记忆系统的功能。
    支持多种文件格式和完整的验证机制。
    """
    
    def __init__(self, mirix_adapter: MIRIXAdapter):
        """
        初始化资源上传工具
        
        Args:
            mirix_adapter: MIRIX 后端适配器实例
        """
        self.mirix_adapter = mirix_adapter
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_parameters(
        self,
        file_name: str,
        file_content: str,
        file_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证上传参数
        
        Args:
            file_name: 文件名
            file_content: 文件内容（Base64编码或纯文本）
            file_type: 文件类型（可选，会自动检测）
            description: 文件描述（可选）
            
        Returns:
            Dict[str, Any]: 验证后的参数字典
            
        Raises:
            ValidationError: 参数验证失败时抛出
        """
        try:
            # 验证文件名
            if not file_name or not file_name.strip():
                raise ValidationError("文件名不能为空")
            
            # 清理文件名
            cleaned_filename = sanitize_filename(file_name.strip())
            if len(cleaned_filename) > MAX_FILENAME_LENGTH:
                raise ValidationError(f"文件名长度不能超过 {MAX_FILENAME_LENGTH} 字符")
            
            # 验证文件内容
            if not file_content:
                raise ValidationError("文件内容不能为空")
            
            # 检测文件类型
            detected_file_type = self._detect_file_type(cleaned_filename, file_type)
            
            # 验证文件类型是否支持
            if detected_file_type not in SUPPORTED_FILE_TYPES:
                raise ValidationError(
                    f"不支持的文件类型: {detected_file_type}。"
                    f"支持的类型: {', '.join(SUPPORTED_FILE_TYPES)}"
                )
            
            # 处理文件内容（检测是否为Base64编码）
            processed_content = self._process_file_content(file_content)
            
            # 验证文件大小
            content_size = len(processed_content.encode('utf-8'))
            if content_size < MIN_FILE_SIZE:
                raise ValidationError(f"文件内容太小，至少需要 {MIN_FILE_SIZE} 字节")
            
            if content_size > MAX_FILE_SIZE:
                raise ValidationError(
                    f"文件大小超过限制 {MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            
            # 验证描述（如果提供）
            validated_description = None
            if description:
                if len(description) > 1000:  # 限制描述长度
                    validated_description = description[:1000] + "..."
                else:
                    validated_description = description.strip()
            
            return {
                "file_name": cleaned_filename,
                "file_type": detected_file_type,
                "content": processed_content,
                "description": validated_description,
                "content_size": content_size
            }
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"参数验证失败: {str(e)}")
    
    def _detect_file_type(self, file_name: str, provided_type: Optional[str] = None) -> str:
        """
        检测文件类型
        
        Args:
            file_name: 文件名
            provided_type: 用户提供的文件类型
            
        Returns:
            str: 检测到的MIME类型
        """
        # 如果用户提供了类型且有效，使用用户提供的类型
        if provided_type and provided_type in SUPPORTED_FILE_TYPES:
            return provided_type
        
        # 从文件扩展名检测
        file_path = Path(file_name)
        extension = file_path.suffix.lower()
        
        if extension in FILE_EXTENSION_MAPPING:
            return FILE_EXTENSION_MAPPING[extension]
        
        # 使用 mimetypes 库检测
        detected_type, _ = mimetypes.guess_type(file_name)
        if detected_type and detected_type in SUPPORTED_FILE_TYPES:
            return detected_type
        
        # 默认为纯文本
        return "text/plain"
    
    def _process_file_content(self, content: str) -> str:
        """
        处理文件内容，检测并处理Base64编码
        
        Args:
            content: 原始文件内容
            
        Returns:
            str: 处理后的文件内容
        """
        # 检测是否为Base64编码
        if self._is_base64_encoded(content):
            try:
                # 解码Base64内容
                decoded_bytes = base64.b64decode(content)
                # 尝试解码为UTF-8文本
                decoded_content = decoded_bytes.decode('utf-8')
                self.logger.info("检测到Base64编码内容，已解码")
                return decoded_content
            except Exception as e:
                self.logger.warning(f"Base64解码失败，使用原始内容: {e}")
                return content
        else:
            # 直接使用原始内容
            return content
    
    def _is_base64_encoded(self, content: str) -> bool:
        """
        检测内容是否为Base64编码
        
        Args:
            content: 待检测的内容
            
        Returns:
            bool: 是否为Base64编码
        """
        try:
            # Base64字符串的基本特征检查
            if not content or len(content) < 4:
                return False
            
            # 检查是否只包含Base64字符
            import re
            base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
            if not base64_pattern.match(content.replace('\n', '').replace('\r', '')):
                return False
            
            # 尝试解码
            base64.b64decode(content, validate=True)
            
            # 如果内容看起来像普通文本，可能不是Base64
            if content.isprintable() and ' ' in content and len(content) < 1000:
                return False
            
            return True
        except Exception:
            return False
    
    def prepare_upload_request(
        self,
        validated_params: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        准备上传请求数据
        
        Args:
            validated_params: 验证后的参数
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 上传请求数据
        """
        # 需要将内容重新编码为Base64，因为后端API期望Base64格式
        content_bytes = validated_params["content"].encode('utf-8')
        base64_content = base64.b64encode(content_bytes).decode('utf-8')
        
        upload_data = {
            "file_name": validated_params["file_name"],
            "file_type": validated_params["file_type"],
            "content": base64_content,
            "user_id": user_id
        }
        
        # 添加描述（如果有）
        if validated_params["description"]:
            upload_data["description"] = validated_params["description"]
        
        return upload_data
    
    def format_upload_response(
        self,
        upload_result: Dict[str, Any],
        file_name: str,
        content_size: int
    ) -> Dict[str, Any]:
        """
        格式化上传响应
        
        Args:
            upload_result: MIRIX 后端返回的上传结果
            file_name: 文件名
            content_size: 内容大小
            
        Returns:
            Dict[str, Any]: 格式化后的响应
        """
        if upload_result.get("success"):
            return {
                "success": True,
                "message": f"文件 '{file_name}' 上传成功",
                "file_info": {
                    "file_name": file_name,
                    "content_size": content_size,
                    "document_id": upload_result.get("document_id"),
                    "processed_content": upload_result.get("processed_content")
                },
                "upload_metadata": {
                    "upload_time": upload_result.get("upload_time"),
                    "processing_status": "completed"
                }
            }
        else:
            return {
                "success": False,
                "error": upload_result.get("error", "上传失败"),
                "message": f"文件 '{file_name}' 上传失败",
                "file_info": {
                    "file_name": file_name,
                    "content_size": content_size
                }
            }
    
    async def upload_resource(
        self,
        file_name: str,
        file_content: str,
        file_type: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行资源上传
        
        Args:
            file_name: 文件名
            file_content: 文件内容（Base64编码或纯文本）
            file_type: 文件类型（可选，会自动检测）
            description: 文件描述（可选）
            user_id: 用户ID（可选，使用默认用户ID如果未提供）
            
        Returns:
            Dict[str, Any]: 上传结果
            
        Raises:
            MemoryToolError: 上传操作失败时抛出
        """
        try:
            # 验证参数
            validated_params = self.validate_parameters(
                file_name, file_content, file_type, description
            )
            
            # 获取用户ID
            if not user_id:
                user_id = "default_user"
            
            # 准备上传请求
            upload_data = self.prepare_upload_request(validated_params, user_id)
            
            self.logger.info(
                f"开始上传资源: file='{validated_params['file_name']}', "
                f"type={validated_params['file_type']}, "
                f"size={validated_params['content_size']} bytes"
            )
            
            # 调用 MIRIX 后端上传文档
            upload_result = await self.mirix_adapter.upload_document(upload_data)
            
            # 格式化响应
            response = self.format_upload_response(
                upload_result, 
                validated_params["file_name"],
                validated_params["content_size"]
            )
            
            if response["success"]:
                self.logger.info(f"资源上传成功: {validated_params['file_name']}")
            else:
                self.logger.error(f"资源上传失败: {response.get('error', '未知错误')}")
            
            return response
            
        except ValidationError as e:
            self.logger.error(f"上传参数验证失败: {e}")
            raise MemoryToolError(f"上传参数无效: {str(e)}")
        
        except MIRIXClientError as e:
            self.logger.error(f"MIRIX 客户端上传失败: {e}")
            raise MemoryToolError(f"资源上传失败: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"资源上传意外错误: {e}")
            raise MemoryToolError(f"资源上传失败: {str(e)}")


# 便捷函数接口
async def resource_upload(
    file_name: str,
    file_content: str,
    file_type: Optional[str] = None,
    description: Optional[str] = None,
    user_id: Optional[str] = None,
    mirix_adapter: Optional[MIRIXAdapter] = None
) -> Dict[str, Any]:
    """
    上传资源到 MIRIX 资源记忆系统
    
    这是一个便捷函数，提供简单的接口来上传文档和文件到资源记忆系统。
    支持多种文件格式和自动类型检测。
    
    使用场景：
    - 上传文档到知识库进行长期存储
    - 将重要文件添加到资源记忆中
    - 批量导入文档资料
    - 创建可搜索的文档库
    
    Args:
        file_name (str): 文件名
            - 必填参数，包含文件扩展名
            - 用于自动检测文件类型
            - 示例："document.md"、"data.csv"、"report.txt"
        
        file_content (str): 文件内容
            - 必填参数，可以是Base64编码或纯文本
            - 工具会自动检测编码格式并处理
            - 支持的格式：文本、Markdown、CSV、Excel等
        
        file_type (Optional[str]): 文件MIME类型
            - 可选参数，如果未提供会自动检测
            - 支持的类型：text/plain, text/markdown, text/csv等
            - 示例："text/markdown"、"text/csv"
        
        description (Optional[str]): 文件描述
            - 可选参数，用于描述文件内容和用途
            - 最大长度1000字符
            - 示例："项目需求文档"、"用户数据导出"
        
        user_id (Optional[str]): 用户ID
            - 可选参数，如果未提供将使用默认用户ID
            - 用于指定文件所属用户
        
        mirix_adapter (Optional[MIRIXAdapter]): MIRIX 适配器实例
            - 可选参数，如果未提供将创建新实例
            - 用于与 MIRIX 后端通信
    
    Returns:
        Dict[str, Any]: 上传结果字典，包含以下字段：
            - success (bool): 操作是否成功
            - message (str): 操作结果消息
            - file_info (Dict): 文件信息，包含：
              * file_name: 文件名
              * content_size: 文件大小（字节）
              * document_id: 文档ID（成功时）
              * processed_content: 处理后的内容信息（成功时）
            - upload_metadata (Dict): 上传元数据（成功时）
    
    Raises:
        MemoryToolError: 上传操作失败时抛出
        ValidationError: 参数验证失败时抛出
        MIRIXClientError: MIRIX 客户端通信失败时抛出
    
    Examples:
        # 上传文本文件
        result = await resource_upload(
            file_name="notes.txt",
            file_content="这是一些重要的笔记内容"
        )
        
        # 上传Markdown文档
        result = await resource_upload(
            file_name="readme.md",
            file_content="# 项目说明\n\n这是项目的详细说明...",
            description="项目说明文档"
        )
        
        # 上传Base64编码的文件
        result = await resource_upload(
            file_name="data.csv",
            file_content="bmFtZSxhZ2UKSm9obiwyNQpKYW5lLDMw",  # Base64编码的CSV
            file_type="text/csv"
        )
        
        # 检查上传结果
        if result["success"]:
            print(f"上传成功: {result['message']}")
            print(f"文档ID: {result['file_info']['document_id']}")
        else:
            print(f"上传失败: {result.get('error', '未知错误')}")
    """
    # 创建或使用提供的适配器
    if mirix_adapter is None:
        from ..config import get_config
        mirix_adapter = MIRIXAdapter(get_config())
    
    # 创建上传工具实例
    upload_tool = ResourceUploadTool(mirix_adapter)
    
    # 执行上传
    return await upload_tool.upload_resource(
        file_name, file_content, file_type, description, user_id
    )


# 工具元数据，用于 MCP 工具注册
TOOL_METADATA = {
    "name": "resource_upload",
    "description": "上传文档和文件到 MIRIX 资源记忆系统",
    "inputSchema": {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "文件名（包含扩展名）"
            },
            "file_content": {
                "type": "string",
                "description": "文件内容（Base64编码或纯文本）"
            },
            "file_type": {
                "type": "string",
                "description": "文件MIME类型（可选，会自动检测）"
            },
            "description": {
                "type": "string",
                "description": "文件描述（可选）"
            }
        },
        "required": ["file_name", "file_content"]
    },
    "returns": {
        "type": "object",
        "description": "上传结果，包含文件信息和处理状态"
    },
    "examples": [
        {
            "description": "上传文本文件",
            "parameters": {
                "file_name": "notes.txt",
                "file_content": "这是一些重要的笔记内容",
                "description": "个人笔记"
            }
        },
        {
            "description": "上传Markdown文档",
            "parameters": {
                "file_name": "project.md",
                "file_content": "# 项目说明\n\n详细的项目文档...",
                "file_type": "text/markdown"
            }
        }
    ]
}

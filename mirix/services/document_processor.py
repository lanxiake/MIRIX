"""
文档处理服务

支持多种文档格式的解析和内容提取，包括：
- Markdown (.md)
- 纯文本 (.txt)
- Excel (.xlsx, .xls)
- 其他常见文档格式
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import pandas as pd
import markdown
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """文档处理器，负责解析各种格式的文档"""
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {
        '.md': 'markdown',
        '.markdown': 'markdown', 
        '.txt': 'text',
        '.text': 'text',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.csv': 'csv'
    }
    
    def __init__(self):
        """初始化文档处理器"""
        self.logger = logging.getLogger(f"Mirix.DocumentProcessor")
        self.logger.setLevel(logging.INFO)
    
    def is_supported_format(self, file_path: Union[str, Path]) -> bool:
        """检查文件格式是否支持"""
        file_path = Path(file_path)
        return file_path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def get_file_type(self, file_path: Union[str, Path]) -> Optional[str]:
        """获取文件类型"""
        file_path = Path(file_path)
        return self.SUPPORTED_FORMATS.get(file_path.suffix.lower())
    
    def process_document(self, file_path: Union[str, Path], content: Optional[bytes] = None) -> Dict[str, Any]:
        """
        处理文档文件，提取内容和元数据
        
        Args:
            file_path: 文件路径或文件名
            content: 文件内容（字节）
            
        Returns:
            包含解析结果的字典
        """
        try:
            file_path = Path(file_path)
            file_type = self.get_file_type(file_path)
            
            if not file_type:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
            
            # 如果没有提供内容，尝试从文件路径读取
            if content is None and file_path.exists():
                with open(file_path, 'rb') as f:
                    content = f.read()
            
            if content is None:
                raise ValueError("无法获取文件内容")
            
            # 根据文件类型处理
            if file_type == 'markdown':
                return self._process_markdown(file_path, content)
            elif file_type == 'text':
                return self._process_text(file_path, content)
            elif file_type == 'excel':
                return self._process_excel(file_path, content)
            elif file_type == 'csv':
                return self._process_csv(file_path, content)
            else:
                raise ValueError(f"未实现的文件类型处理: {file_type}")
                
        except Exception as e:
            self.logger.error(f"处理文档失败 {file_path}: {e}")
            raise
    
    def _process_markdown(self, file_path: Path, content: bytes) -> Dict[str, Any]:
        """处理Markdown文件"""
        try:
            # 解码文本内容
            text_content = content.decode('utf-8')
            
            # 使用markdown库解析
            md = markdown.Markdown(extensions=['meta', 'toc', 'tables'])
            html_content = md.convert(text_content)
            
            # 提取元数据
            metadata = getattr(md, 'Meta', {})
            
            # 提取标题结构
            headers = self._extract_markdown_headers(text_content)
            
            return {
                'file_name': file_path.name,
                'file_type': 'markdown',
                'raw_content': text_content,
                'html_content': html_content,
                'metadata': metadata,
                'headers': headers,
                'word_count': len(text_content.split()),
                'char_count': len(text_content),
                'processed_at': datetime.now().isoformat(),
                'summary': self._generate_summary(text_content)
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法解码文件内容")
            
            return self._process_markdown(file_path, text_content.encode('utf-8'))
    
    def _process_text(self, file_path: Path, content: bytes) -> Dict[str, Any]:
        """处理纯文本文件"""
        try:
            # 解码文本内容
            text_content = content.decode('utf-8')
            
            # 分析文本结构
            lines = text_content.split('\n')
            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
            
            return {
                'file_name': file_path.name,
                'file_type': 'text',
                'raw_content': text_content,
                'lines': lines,
                'paragraphs': paragraphs,
                'line_count': len(lines),
                'paragraph_count': len(paragraphs),
                'word_count': len(text_content.split()),
                'char_count': len(text_content),
                'processed_at': datetime.now().isoformat(),
                'summary': self._generate_summary(text_content)
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法解码文件内容")
            
            return self._process_text(file_path, text_content.encode('utf-8'))
    
    def _process_excel(self, file_path: Path, content: bytes) -> Dict[str, Any]:
        """处理Excel文件"""
        try:
            import io
            
            # 使用pandas读取Excel
            excel_file = io.BytesIO(content)
            
            # 读取所有工作表
            sheets_data = {}
            with pd.ExcelFile(excel_file) as xls:
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet_name)
                    
                    # 转换为可序列化的格式
                    sheets_data[sheet_name] = {
                        'data': df.to_dict('records'),
                        'columns': df.columns.tolist(),
                        'shape': df.shape,
                        'summary': {
                            'rows': len(df),
                            'columns': len(df.columns),
                            'non_null_cells': df.count().sum(),
                            'data_types': df.dtypes.astype(str).to_dict()
                        }
                    }
            
            # 生成文本摘要
            text_summary = self._excel_to_text_summary(sheets_data)
            
            return {
                'file_name': file_path.name,
                'file_type': 'excel',
                'sheets': sheets_data,
                'sheet_names': list(sheets_data.keys()),
                'total_sheets': len(sheets_data),
                'processed_at': datetime.now().isoformat(),
                'text_summary': text_summary,
                'summary': self._generate_summary(text_summary)
            }
            
        except Exception as e:
            self.logger.error(f"处理Excel文件失败: {e}")
            raise ValueError(f"Excel文件处理失败: {str(e)}")
    
    def _process_csv(self, file_path: Path, content: bytes) -> Dict[str, Any]:
        """处理CSV文件"""
        try:
            import io
            
            # 解码内容
            text_content = content.decode('utf-8')
            csv_file = io.StringIO(text_content)
            
            # 使用pandas读取CSV
            df = pd.read_csv(csv_file)
            
            # 转换为可序列化的格式
            data = {
                'data': df.to_dict('records'),
                'columns': df.columns.tolist(),
                'shape': df.shape,
                'summary': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'non_null_cells': df.count().sum(),
                    'data_types': df.dtypes.astype(str).to_dict()
                }
            }
            
            # 生成文本摘要
            text_summary = f"CSV文件包含 {len(df)} 行数据，{len(df.columns)} 列：{', '.join(df.columns.tolist())}"
            
            return {
                'file_name': file_path.name,
                'file_type': 'csv',
                'data': data,
                'processed_at': datetime.now().isoformat(),
                'text_summary': text_summary,
                'summary': self._generate_summary(text_summary)
            }
            
        except UnicodeDecodeError:
            # 尝试其他编码
            for encoding in ['gbk', 'gb2312', 'latin1']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("无法解码CSV文件内容")
            
            return self._process_csv(file_path, text_content.encode('utf-8'))
    
    def _extract_markdown_headers(self, content: str) -> List[Dict[str, Any]]:
        """提取Markdown标题结构"""
        headers = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                # 计算标题级别
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break
                
                # 提取标题文本
                title = line[level:].strip()
                if title:
                    headers.append({
                        'level': level,
                        'title': title,
                        'line_number': i + 1
                    })
        
        return headers
    
    def _excel_to_text_summary(self, sheets_data: Dict[str, Any]) -> str:
        """将Excel数据转换为文本摘要"""
        summary_parts = []
        
        for sheet_name, sheet_info in sheets_data.items():
            summary = sheet_info['summary']
            summary_parts.append(
                f"工作表 '{sheet_name}': {summary['rows']} 行, {summary['columns']} 列"
            )
            
            # 添加列名
            columns = sheet_info['columns']
            if columns:
                summary_parts.append(f"列名: {', '.join(columns[:10])}")  # 只显示前10列
                if len(columns) > 10:
                    summary_parts.append(f"... 还有 {len(columns) - 10} 列")
        
        return '\n'.join(summary_parts)
    
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        if len(content) <= max_length:
            return content
        
        # 简单的摘要生成：取前面的内容
        summary = content[:max_length].strip()
        
        # 尝试在句号处截断
        last_period = summary.rfind('。')
        if last_period > max_length // 2:
            summary = summary[:last_period + 1]
        else:
            # 尝试在空格处截断
            last_space = summary.rfind(' ')
            if last_space > max_length // 2:
                summary = summary[:last_space]
            
        return summary + "..."
    
    def extract_text_content(self, processed_doc: Dict[str, Any]) -> str:
        """从处理后的文档中提取纯文本内容"""
        file_type = processed_doc.get('file_type')
        
        if file_type in ['markdown', 'text']:
            return processed_doc.get('raw_content', '')
        elif file_type == 'excel':
            return processed_doc.get('text_summary', '')
        elif file_type == 'csv':
            return processed_doc.get('text_summary', '')
        else:
            return processed_doc.get('summary', '')
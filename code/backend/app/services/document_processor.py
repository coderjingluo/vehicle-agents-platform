"""
文档处理服务

负责各种格式文档的文本提取和处理
"""

import os
import re
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import StringIO

import pypdf
import docx
from bs4 import BeautifulSoup
import markdown
import json
import xml.etree.ElementTree as ET

from app.models.knowledge_base import DocumentType
from loguru import logger


class DocumentProcessor:
    """文档处理器"""
    
    def __init__(self):
        self.chunk_separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", " "]
    
    async def extract_text(self, file_path: str, doc_type: DocumentType) -> str:
        """从文档中提取文本内容"""
        try:
            if doc_type == DocumentType.PDF:
                return await self._extract_pdf_text(file_path)
            elif doc_type == DocumentType.DOCX:
                return await self._extract_docx_text(file_path)
            elif doc_type == DocumentType.TXT:
                return await self._extract_txt_text(file_path)
            elif doc_type == DocumentType.MD:
                return await self._extract_md_text(file_path)
            elif doc_type == DocumentType.HTML:
                return await self._extract_html_text(file_path)
            elif doc_type == DocumentType.JSON:
                return await self._extract_json_text(file_path)
            elif doc_type == DocumentType.XML:
                return await self._extract_xml_text(file_path)
            else:
                raise ValueError(f"不支持的文档类型: {doc_type}")
                
        except Exception as e:
            logger.error(f"提取文档文本失败 {file_path}: {e}")
            raise
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """提取PDF文本"""
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(f"--- 第 {page_num + 1} 页 ---\n{page_text}")
                    except Exception as e:
                        logger.warning(f"提取PDF第{page_num + 1}页失败: {e}")
                        continue
            
            if not text_content:
                raise ValueError("PDF文档为空或无法提取文本")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"PDF文本提取失败: {e}")
            raise
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """提取DOCX文本"""
        try:
            doc = docx.Document(file_path)
            text_content = []
            
            # 提取段落文本
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            # 提取表格文本
            for table in doc.tables:
                table_text = []
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        table_text.append(" | ".join(row_text))
                
                if table_text:
                    text_content.append("\n--- 表格 ---\n" + "\n".join(table_text) + "\n--- 表格结束 ---")
            
            if not text_content:
                raise ValueError("DOCX文档为空")
            
            return "\n\n".join(text_content)
            
        except Exception as e:
            logger.error(f"DOCX文本提取失败: {e}")
            raise
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """提取TXT文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
            
            if not content.strip():
                raise ValueError("TXT文档为空")
            
            return content
            
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                async with aiofiles.open(file_path, 'r', encoding='gbk') as file:
                    content = await file.read()
                return content
            except Exception:
                async with aiofiles.open(file_path, 'r', encoding='latin-1') as file:
                    content = await file.read()
                return content
        except Exception as e:
            logger.error(f"TXT文本提取失败: {e}")
            raise
    
    async def _extract_md_text(self, file_path: str) -> str:
        """提取Markdown文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                md_content = await file.read()
            
            if not md_content.strip():
                raise ValueError("Markdown文档为空")
            
            # 转换为HTML再提取纯文本
            html = markdown.markdown(md_content)
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # 清理多余的空白
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Markdown文本提取失败: {e}")
            raise
    
    async def _extract_html_text(self, file_path: str) -> str:
        """提取HTML文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                html_content = await file.read()
            
            if not html_content.strip():
                raise ValueError("HTML文档为空")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本
            text = soup.get_text()
            
            # 清理多余的空白
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"HTML文本提取失败: {e}")
            raise
    
    async def _extract_json_text(self, file_path: str) -> str:
        """提取JSON文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                json_content = await file.read()
            
            if not json_content.strip():
                raise ValueError("JSON文档为空")
            
            # 解析JSON
            data = json.loads(json_content)
            
            # 递归提取所有文本值
            text_values = []
            self._extract_json_values(data, text_values)
            
            return "\n".join(text_values)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise ValueError("无效的JSON格式")
        except Exception as e:
            logger.error(f"JSON文本提取失败: {e}")
            raise
    
    def _extract_json_values(self, data, text_values: List[str]):
        """递归提取JSON中的文本值"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and value.strip():
                    text_values.append(f"{key}: {value}")
                elif isinstance(value, (dict, list)):
                    self._extract_json_values(value, text_values)
                elif value is not None:
                    text_values.append(f"{key}: {str(value)}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str) and item.strip():
                    text_values.append(item)
                elif isinstance(item, (dict, list)):
                    self._extract_json_values(item, text_values)
                elif item is not None:
                    text_values.append(str(item))
    
    async def _extract_xml_text(self, file_path: str) -> str:
        """提取XML文本"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                xml_content = await file.read()
            
            if not xml_content.strip():
                raise ValueError("XML文档为空")
            
            # 解析XML
            root = ET.fromstring(xml_content)
            
            # 递归提取所有文本内容
            text_values = []
            self._extract_xml_text_recursive(root, text_values)
            
            return "\n".join(text_values)
            
        except ET.ParseError as e:
            logger.error(f"XML解析失败: {e}")
            raise ValueError("无效的XML格式")
        except Exception as e:
            logger.error(f"XML文本提取失败: {e}")
            raise
    
    def _extract_xml_text_recursive(self, element, text_values: List[str]):
        """递归提取XML元素的文本"""
        # 添加元素文本
        if element.text and element.text.strip():
            text_values.append(element.text.strip())
        
        # 添加属性值
        for attr_name, attr_value in element.attrib.items():
            if attr_value.strip():
                text_values.append(f"{attr_name}: {attr_value}")
        
        # 递归处理子元素
        for child in element:
            self._extract_xml_text_recursive(child, text_values)
            
            # 添加尾部文本
            if child.tail and child.tail.strip():
                text_values.append(child.tail.strip())
    
    async def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """将文本分块"""
        try:
            if not text.strip():
                return []
            
            # 清理文本
            text = self._clean_text(text)
            
            if len(text) <= chunk_size:
                return [text]
            
            chunks = []
            start = 0
            
            while start < len(text):
                # 确定结束位置
                end = start + chunk_size
                
                if end >= len(text):
                    # 最后一块
                    chunk = text[start:].strip()
                    if chunk:
                        chunks.append(chunk)
                    break
                
                # 寻找合适的分割点
                chunk_end = self._find_split_point(text, start, end)
                chunk = text[start:chunk_end].strip()
                
                if chunk:
                    chunks.append(chunk)
                
                # 计算下一块的开始位置（考虑重叠）
                start = max(start + 1, chunk_end - chunk_overlap)
            
            return chunks
            
        except Exception as e:
            logger.error(f"文本分块失败: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除多余的换行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:(){}[\]"\'-]', ' ', text)
        
        return text.strip()
    
    def _find_split_point(self, text: str, start: int, preferred_end: int) -> int:
        """寻找合适的文本分割点"""
        # 从首选结束位置向前查找分隔符
        search_start = max(start, preferred_end - 200)  # 向前最多搜索200个字符
        
        for separator in self.chunk_separators:
            # 从后向前查找分隔符
            split_pos = text.rfind(separator, search_start, preferred_end)
            if split_pos != -1 and split_pos > start:
                return split_pos + len(separator)
        
        # 如果找不到合适的分隔符，在单词边界分割
        for i in range(preferred_end - 1, search_start - 1, -1):
            if text[i].isspace():
                return i
        
        # 最后手段：强制分割
        return preferred_end
    
    async def extract_metadata(self, file_path: str, doc_type: DocumentType) -> Dict[str, Any]:
        """提取文档元数据"""
        try:
            file_stat = os.stat(file_path)
            
            metadata = {
                "file_size": file_stat.st_size,
                "created_time": file_stat.st_ctime,
                "modified_time": file_stat.st_mtime,
                "file_type": doc_type.value
            }
            
            if doc_type == DocumentType.PDF:
                metadata.update(await self._extract_pdf_metadata(file_path))
            elif doc_type == DocumentType.DOCX:
                metadata.update(await self._extract_docx_metadata(file_path))
            
            return metadata
            
        except Exception as e:
            logger.error(f"提取元数据失败 {file_path}: {e}")
            return {}
    
    async def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取PDF元数据"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                
                metadata = {
                    "page_count": len(pdf_reader.pages),
                    "title": "",
                    "author": "",
                    "subject": "",
                    "creator": ""
                }
                
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", "")
                    })
                
                return metadata
                
        except Exception as e:
            logger.warning(f"提取PDF元数据失败: {e}")
            return {}
    
    async def _extract_docx_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取DOCX元数据"""
        try:
            doc = docx.Document(file_path)
            
            metadata = {
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
                "title": "",
                "author": "",
                "subject": "",
                "category": ""
            }
            
            if doc.core_properties:
                metadata.update({
                    "title": doc.core_properties.title or "",
                    "author": doc.core_properties.author or "",
                    "subject": doc.core_properties.subject or "",
                    "category": doc.core_properties.category or "",
                    "created": doc.core_properties.created,
                    "modified": doc.core_properties.modified
                })
            
            return metadata
            
        except Exception as e:
            logger.warning(f"提取DOCX元数据失败: {e}")
            return {} 
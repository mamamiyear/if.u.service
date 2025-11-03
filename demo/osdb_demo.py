# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-03
# OpenSearch/Elasticsearch 数据库工具类
"""
OpenSearch/Elasticsearch 数据库工具类
支持 OpenSearch 和 Elasticsearch 的连接、索引管理、文档操作和搜索功能
"""

import logging
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse
import json

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, NotFoundError, RequestError
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False

try:
    from opensearchpy import OpenSearch
    from opensearchpy.exceptions import ConnectionError as OSConnectionError, NotFoundError as OSNotFoundError, RequestError as OSRequestError
    OS_AVAILABLE = True
except ImportError:
    OS_AVAILABLE = False

from .config import get_instance as get_config
from .logger import get_logger


class OpenSearchDB:
    """OpenSearch/Elasticsearch 数据库操作类"""
    
    def __init__(self, config_section: str = "opensearch"):
        """
        初始化 OpenSearch/Elasticsearch 连接
        
        Args:
            config_section: 配置文件中的节名称，默认为 "opensearch"
        """
        self.logger = get_logger(__name__)
        self.config_section = config_section
        self.client = None
        self.client_type = None  # 'elasticsearch' 或 'opensearch'
        
        # 从配置文件加载配置
        self._load_config()
        
        # 初始化客户端连接
        self._init_client()
    
    def _load_config(self):
        """从配置文件加载 OpenSearch/Elasticsearch 配置"""
        try:
            config = get_config()
            if not config or not config.has_section(self.config_section):
                raise ValueError(f"配置文件中未找到 [{self.config_section}] 节")
            
            # 基础连接配置
            self.host = config.get(self.config_section, "host", fallback="localhost")
            self.port = config.getint(self.config_section, "port", fallback=9200)
            self.scheme = config.get(self.config_section, "scheme", fallback="http")
            
            # 认证配置
            self.username = config.get(self.config_section, "username", fallback=None)
            self.password = config.get(self.config_section, "password", fallback=None)
            self.api_key = config.get(self.config_section, "api_key", fallback=None)
            
            # 连接配置
            self.timeout = config.getint(self.config_section, "timeout", fallback=30)
            self.max_retries = config.getint(self.config_section, "max_retries", fallback=3)
            self.verify_certs = config.getboolean(self.config_section, "verify_certs", fallback=True)
            
            # 客户端类型偏好 ('auto', 'elasticsearch', 'opensearch')
            self.client_preference = config.get(self.config_section, "client_type", fallback="auto")
            
            self.logger.info(f"已加载 {self.config_section} 配置: {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            raise
    
    def _init_client(self):
        """初始化客户端连接"""
        try:
            # 构建连接URL
            url = f"{self.scheme}://{self.host}:{self.port}"
            
            # 根据偏好和可用性选择客户端
            if self.client_preference == "elasticsearch" or (self.client_preference == "auto" and ES_AVAILABLE):
                self._init_elasticsearch_client(url)
            elif self.client_preference == "opensearch" or (self.client_preference == "auto" and OS_AVAILABLE):
                self._init_opensearch_client(url)
            else:
                raise ImportError("未安装 elasticsearch 或 opensearch-py 客户端库")
            
            # 测试连接
            self._test_connection()
            
        except Exception as e:
            self.logger.error(f"初始化客户端失败: {e}")
            raise
    
    def _init_elasticsearch_client(self, url: str):
        """初始化 Elasticsearch 客户端"""
        if not ES_AVAILABLE:
            raise ImportError("elasticsearch 库未安装，请运行: pip install elasticsearch")
        
        # 构建连接参数
        client_params = {
            "hosts": [url],
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "verify_certs": self.verify_certs,
        }
        
        # 添加认证信息
        if self.username and self.password:
            client_params["basic_auth"] = (self.username, self.password)
        elif self.api_key:
            client_params["api_key"] = self.api_key
        
        self.client = Elasticsearch(**client_params)
        self.client_type = "elasticsearch"
        self.logger.info("已初始化 Elasticsearch 客户端")
    
    def _init_opensearch_client(self, url: str):
        """初始化 OpenSearch 客户端"""
        if not OS_AVAILABLE:
            raise ImportError("opensearch-py 库未安装，请运行: pip install opensearch-py")
        
        # 构建连接参数
        client_params = {
            "hosts": [{"host": self.host, "port": self.port}],
            "http_compress": True,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "verify_certs": self.verify_certs,
        }
        
        # 添加认证信息
        if self.username and self.password:
            client_params["http_auth"] = (self.username, self.password)
        
        # OpenSearch 使用 https 时的额外配置
        if self.scheme == "https":
            client_params["use_ssl"] = True
        
        self.client = OpenSearch(**client_params)
        self.client_type = "opensearch"
        self.logger.info("已初始化 OpenSearch 客户端")
    
    def _test_connection(self):
        """测试数据库连接"""
        try:
            info = self.client.info()
            version = info.get("version", {}).get("number", "未知")
            self.logger.info(f"连接成功，{self.client_type} 版本: {version}")
            return True
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            raise ConnectionError(f"无法连接到 {self.client_type}: {e}")
    
    def get_client(self):
        """获取客户端实例"""
        return self.client
    
    def get_client_type(self) -> str:
        """获取客户端类型"""
        return self.client_type
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        try:
            return self.client.ping() if self.client else False
        except:
            return False
    
    # ==================== 索引管理方法 ====================
    
    def create_index(self, index_name: str, mapping: Optional[Dict] = None, settings: Optional[Dict] = None) -> bool:
        """
        创建索引
        
        Args:
            index_name: 索引名称
            mapping: 字段映射配置
            settings: 索引设置
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if self.index_exists(index_name):
                self.logger.warning(f"索引 {index_name} 已存在")
                return True
            
            body = {}
            if mapping:
                body["mappings"] = mapping
            if settings:
                body["settings"] = settings
            
            response = self.client.indices.create(index=index_name, body=body if body else None)
            self.logger.info(f"成功创建索引: {index_name}")
            return response.get("acknowledged", False)
            
        except Exception as e:
            self.logger.error(f"创建索引 {index_name} 失败: {e}")
            return False
    
    def delete_index(self, index_name: str) -> bool:
        """
        删除索引
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if not self.index_exists(index_name):
                self.logger.warning(f"索引 {index_name} 不存在")
                return True
            
            response = self.client.indices.delete(index=index_name)
            self.logger.info(f"成功删除索引: {index_name}")
            return response.get("acknowledged", False)
            
        except Exception as e:
            self.logger.error(f"删除索引 {index_name} 失败: {e}")
            return False
    
    def index_exists(self, index_name: str) -> bool:
        """
        检查索引是否存在
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 索引是否存在
        """
        try:
            return self.client.indices.exists(index=index_name)
        except Exception as e:
            self.logger.error(f"检查索引 {index_name} 是否存在失败: {e}")
            return False
    
    def get_index_mapping(self, index_name: str) -> Optional[Dict]:
        """
        获取索引映射
        
        Args:
            index_name: 索引名称
            
        Returns:
            Dict: 索引映射配置
        """
        try:
            response = self.client.indices.get_mapping(index=index_name)
            return response.get(index_name, {}).get("mappings", {})
        except Exception as e:
            self.logger.error(f"获取索引 {index_name} 映射失败: {e}")
            return None
    
    def update_index_mapping(self, index_name: str, mapping: Dict) -> bool:
        """
        更新索引映射
        
        Args:
            index_name: 索引名称
            mapping: 新的映射配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            response = self.client.indices.put_mapping(index=index_name, body=mapping)
            self.logger.info(f"成功更新索引 {index_name} 映射")
            return response.get("acknowledged", False)
        except Exception as e:
            self.logger.error(f"更新索引 {index_name} 映射失败: {e}")
            return False
    
    def get_index_settings(self, index_name: str) -> Optional[Dict]:
        """
        获取索引设置
        
        Args:
            index_name: 索引名称
            
        Returns:
            Dict: 索引设置
        """
        try:
            response = self.client.indices.get_settings(index=index_name)
            return response.get(index_name, {}).get("settings", {})
        except Exception as e:
            self.logger.error(f"获取索引 {index_name} 设置失败: {e}")
            return None
    
    def list_indices(self, pattern: str = "*") -> List[str]:
        """
        列出所有索引
        
        Args:
            pattern: 索引名称模式，默认为 "*" (所有索引)
            
        Returns:
            List[str]: 索引名称列表
        """
        try:
            response = self.client.cat.indices(index=pattern, format="json")
            return [index["index"] for index in response]
        except Exception as e:
            self.logger.error(f"列出索引失败: {e}")
            return []
    
    def refresh_index(self, index_name: str) -> bool:
        """
        刷新索引，使最新的文档可搜索
        
        Args:
            index_name: 索引名称
            
        Returns:
            bool: 刷新是否成功
        """
        try:
            response = self.client.indices.refresh(index=index_name)
            return response.get("_shards", {}).get("failed", 0) == 0
        except Exception as e:
            self.logger.error(f"刷新索引 {index_name} 失败: {e}")
            return False
    
    # ==================== 文档操作方法 ====================
    
    def index_document(self, index_name: str, document: Dict, doc_id: Optional[str] = None) -> Optional[str]:
        """
        索引文档（创建或更新）
        
        Args:
            index_name: 索引名称
            document: 文档内容
            doc_id: 文档ID，如果不提供则自动生成
            
        Returns:
            str: 文档ID，失败返回None
        """
        try:
            if doc_id:
                response = self.client.index(index=index_name, id=doc_id, body=document)
            else:
                response = self.client.index(index=index_name, body=document)
            
            doc_id = response.get("_id")
            self.logger.info(f"成功索引文档到 {index_name}，ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"索引文档到 {index_name} 失败: {e}")
            return None
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict]:
        """
        获取文档
        
        Args:
            index_name: 索引名称
            doc_id: 文档ID
            
        Returns:
            Dict: 文档内容，不存在返回None
        """
        try:
            response = self.client.get(index=index_name, id=doc_id)
            return response.get("_source")
        except (NotFoundError, OSNotFoundError):
            self.logger.warning(f"文档 {doc_id} 在索引 {index_name} 中不存在")
            return None
        except Exception as e:
            self.logger.error(f"获取文档 {doc_id} 从索引 {index_name} 失败: {e}")
            return None
    
    def update_document(self, index_name: str, doc_id: str, document: Dict, upsert: bool = False) -> bool:
        """
        更新文档
        
        Args:
            index_name: 索引名称
            doc_id: 文档ID
            document: 更新的文档内容
            upsert: 如果文档不存在是否创建
            
        Returns:
            bool: 更新是否成功
        """
        try:
            body = {"doc": document}
            if upsert:
                body["doc_as_upsert"] = True
            
            response = self.client.update(index=index_name, id=doc_id, body=body)
            self.logger.info(f"成功更新文档 {doc_id} 在索引 {index_name}")
            return response.get("result") in ["updated", "created"]
            
        except Exception as e:
            self.logger.error(f"更新文档 {doc_id} 在索引 {index_name} 失败: {e}")
            return False
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            index_name: 索引名称
            doc_id: 文档ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            response = self.client.delete(index=index_name, id=doc_id)
            self.logger.info(f"成功删除文档 {doc_id} 从索引 {index_name}")
            return response.get("result") == "deleted"
            
        except (NotFoundError, OSNotFoundError):
            self.logger.warning(f"文档 {doc_id} 在索引 {index_name} 中不存在")
            return True
        except Exception as e:
            self.logger.error(f"删除文档 {doc_id} 从索引 {index_name} 失败: {e}")
            return False
    
    def bulk_index(self, index_name: str, documents: List[Dict], doc_ids: Optional[List[str]] = None) -> Dict:
        """
        批量索引文档
        
        Args:
            index_name: 索引名称
            documents: 文档列表
            doc_ids: 文档ID列表，可选
            
        Returns:
            Dict: 批量操作结果统计
        """
        try:
            actions = []
            for i, doc in enumerate(documents):
                action = {
                    "_index": index_name,
                    "_source": doc
                }
                if doc_ids and i < len(doc_ids):
                    action["_id"] = doc_ids[i]
                actions.append(action)
            
            from elasticsearch.helpers import bulk
            success_count, failed_items = bulk(self.client, actions, stats_only=False)
            
            result = {
                "success_count": success_count,
                "failed_count": len(failed_items),
                "failed_items": failed_items
            }
            
            self.logger.info(f"批量索引完成: 成功 {success_count}, 失败 {len(failed_items)}")
            return result
            
        except Exception as e:
            self.logger.error(f"批量索引到 {index_name} 失败: {e}")
            return {"success_count": 0, "failed_count": len(documents), "failed_items": []}
    
    def document_exists(self, index_name: str, doc_id: str) -> bool:
        """
        检查文档是否存在
        
        Args:
            index_name: 索引名称
            doc_id: 文档ID
            
        Returns:
            bool: 文档是否存在
        """
        try:
            return self.client.exists(index=index_name, id=doc_id)
        except Exception as e:
            self.logger.error(f"检查文档 {doc_id} 在索引 {index_name} 是否存在失败: {e}")
            return False
    
    # ==================== 搜索和查询方法 ====================
    
    def search(self, index_name: str, query: Dict, size: int = 10, from_: int = 0, sort: Optional[List] = None) -> Dict:
        """
        执行搜索查询
        
        Args:
            index_name: 索引名称
            query: 查询DSL
            size: 返回结果数量
            from_: 起始位置
            sort: 排序规则
            
        Returns:
            Dict: 搜索结果
        """
        try:
            body = {
                "query": query,
                "size": size,
                "from": from_
            }
            if sort:
                body["sort"] = sort
            
            response = self.client.search(index=index_name, body=body)
            
            # 格式化返回结果
            result = {
                "total": response["hits"]["total"]["value"] if isinstance(response["hits"]["total"], dict) else response["hits"]["total"],
                "hits": [hit["_source"] for hit in response["hits"]["hits"]],
                "raw_hits": response["hits"]["hits"],  # 包含元数据的原始结果
                "took": response.get("took", 0)
            }
            
            self.logger.info(f"搜索完成，找到 {result['total']} 个结果")
            return result
            
        except Exception as e:
            self.logger.error(f"搜索索引 {index_name} 失败: {e}")
            return {"total": 0, "hits": [], "raw_hits": [], "took": 0}
    
    def match_query(self, index_name: str, field: str, text: str, **kwargs) -> Dict:
        """
        执行匹配查询
        
        Args:
            index_name: 索引名称
            field: 搜索字段
            text: 搜索文本
            **kwargs: 其他搜索参数
            
        Returns:
            Dict: 搜索结果
        """
        query = {
            "match": {
                field: text
            }
        }
        return self.search(index_name, query, **kwargs)
    
    def multi_match_query(self, index_name: str, fields: List[str], text: str, **kwargs) -> Dict:
        """
        执行多字段匹配查询
        
        Args:
            index_name: 索引名称
            fields: 搜索字段列表
            text: 搜索文本
            **kwargs: 其他搜索参数
            
        Returns:
            Dict: 搜索结果
        """
        query = {
            "multi_match": {
                "query": text,
                "fields": fields
            }
        }
        return self.search(index_name, query, **kwargs)
    
    def term_query(self, index_name: str, field: str, value: Any, **kwargs) -> Dict:
        """
        执行精确匹配查询
        
        Args:
            index_name: 索引名称
            field: 搜索字段
            value: 搜索值
            **kwargs: 其他搜索参数
            
        Returns:
            Dict: 搜索结果
        """
        query = {
            "term": {
                field: value
            }
        }
        return self.search(index_name, query, **kwargs)
    
    def range_query(self, index_name: str, field: str, gte=None, lte=None, gt=None, lt=None, **kwargs) -> Dict:
        """
        执行范围查询
        
        Args:
            index_name: 索引名称
            field: 搜索字段
            gte: 大于等于
            lte: 小于等于
            gt: 大于
            lt: 小于
            **kwargs: 其他搜索参数
            
        Returns:
            Dict: 搜索结果
        """
        range_params = {}
        if gte is not None:
            range_params["gte"] = gte
        if lte is not None:
            range_params["lte"] = lte
        if gt is not None:
            range_params["gt"] = gt
        if lt is not None:
            range_params["lt"] = lt
        
        query = {
            "range": {
                field: range_params
            }
        }
        return self.search(index_name, query, **kwargs)
    
    def bool_query(self, index_name: str, must: List = None, should: List = None, 
                   must_not: List = None, filter_: List = None, **kwargs) -> Dict:
        """
        执行布尔查询
        
        Args:
            index_name: 索引名称
            must: 必须匹配的查询列表
            should: 应该匹配的查询列表
            must_not: 必须不匹配的查询列表
            filter_: 过滤查询列表
            **kwargs: 其他搜索参数
            
        Returns:
            Dict: 搜索结果
        """
        bool_query = {}
        if must:
            bool_query["must"] = must
        if should:
            bool_query["should"] = should
        if must_not:
            bool_query["must_not"] = must_not
        if filter_:
            bool_query["filter"] = filter_
        
        query = {"bool": bool_query}
        return self.search(index_name, query, **kwargs)
    
    def aggregate(self, index_name: str, aggs: Dict, query: Optional[Dict] = None) -> Dict:
        """
        执行聚合查询
        
        Args:
            index_name: 索引名称
            aggs: 聚合配置
            query: 查询条件，可选
            
        Returns:
            Dict: 聚合结果
        """
        try:
            body = {
                "aggs": aggs,
                "size": 0  # 不返回文档，只返回聚合结果
            }
            if query:
                body["query"] = query
            
            response = self.client.search(index=index_name, body=body)
            return response.get("aggregations", {})
            
        except Exception as e:
            self.logger.error(f"聚合查询索引 {index_name} 失败: {e}")
            return {}
    
    def scroll_search(self, index_name: str, query: Dict, scroll_size: int = 1000, scroll_timeout: str = "1m") -> List[Dict]:
        """
        执行滚动搜索，用于大量数据的分页查询
        
        Args:
            index_name: 索引名称
            query: 查询DSL
            scroll_size: 每次滚动的文档数量
            scroll_timeout: 滚动超时时间
            
        Returns:
            List[Dict]: 所有搜索结果
        """
        try:
            # 初始搜索
            response = self.client.search(
                index=index_name,
                body={"query": query},
                scroll=scroll_timeout,
                size=scroll_size
            )
            
            scroll_id = response["_scroll_id"]
            hits = response["hits"]["hits"]
            all_results = [hit["_source"] for hit in hits]
            
            # 继续滚动获取剩余数据
            while len(hits) > 0:
                response = self.client.scroll(scroll_id=scroll_id, scroll=scroll_timeout)
                scroll_id = response["_scroll_id"]
                hits = response["hits"]["hits"]
                all_results.extend([hit["_source"] for hit in hits])
            
            # 清理滚动上下文
            self.client.clear_scroll(scroll_id=scroll_id)
            
            self.logger.info(f"滚动搜索完成，共获取 {len(all_results)} 个文档")
            return all_results
            
        except Exception as e:
            self.logger.error(f"滚动搜索索引 {index_name} 失败: {e}")
            return []


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""
    try:
        # 初始化连接
        osdb = OpenSearchDB()
        
        # 创建索引
        mapping = {
            "properties": {
                "title": {"type": "text", "analyzer": "standard"},
                "content": {"type": "text", "analyzer": "standard"},
                "author": {"type": "keyword"},
                "created_at": {"type": "date"},
                "tags": {"type": "keyword"}
            }
        }
        osdb.create_index("articles", mapping=mapping)
        
        # 索引文档
        doc = {
            "title": "OpenSearch 使用指南",
            "content": "这是一篇关于如何使用 OpenSearch 的文章",
            "author": "张三",
            "created_at": "2024-01-01T00:00:00",
            "tags": ["搜索", "教程"]
        }
        doc_id = osdb.index_document("articles", doc)
        
        # 搜索文档
        results = osdb.match_query("articles", "content", "OpenSearch")
        print(f"搜索结果: {results}")
        
        # 聚合查询
        aggs = {
            "authors": {
                "terms": {"field": "author"}
            }
        }
        agg_results = osdb.aggregate("articles", aggs)
        print(f"聚合结果: {agg_results}")
        
    except Exception as e:
        print(f"示例执行失败: {e}")


if __name__ == "__main__":
    example_usage()
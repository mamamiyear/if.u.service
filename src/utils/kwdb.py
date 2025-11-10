# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-03
# Keyword Searching Database

from abc import abstractmethod
import logging
import os
import datetime
import uuid
import jieba
from typing import List, Dict, Any, Protocol, Tuple
from whoosh import index
from whoosh.analysis import Token, Tokenizer
from whoosh.fields import Schema, KEYWORD, TEXT, ID, DATETIME
from whoosh.scoring import BM25F
from whoosh.qparser import MultifieldParser, QueryParser
from .config import get_instance as get_config


class KWDBBaseModel:
    __indexname__ = ""
    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    
    def __init__(self) -> None:
        self.id = str(uuid.uuid4().hex)
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
    
    @abstractmethod
    def content(self) -> str:
        """
        获取文档内容
        
        Returns:
            str: 文档内容
        """
        ...

    @abstractmethod
    def tags(self) -> List[str]:
        """
        获取标签列表
        
        Returns:
            List[str]: 标签列表
        """
        ...
    
    def __docs__(self) -> dict:
        """
        获取模型的文档字符串
        
        Returns:
            dict: 包含模型字段的文档字符串字典
        """
        return {
            "id": self.id,
            "content": self.content(),
            "tags": self.tags(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class KeywordDB(Protocol):

    def insert(self, data: KWDBBaseModel) -> str:
        """
        插入文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            str: 插入的文档ID
        """
        ...
    
    def update(self, data: KWDBBaseModel) -> str:
        """
        更新文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            str: 更新的文档ID
        """
        ...
    
    def upsert(self, data: KWDBBaseModel) -> str:
        """
        插入或更新文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            str: 插入或更新的文档ID
        """
        ...

    def delete(self, data: KWDBBaseModel) -> bool:
        """
        删除文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            bool: 是否删除成功
        """
        ...
    
    def get(self, model:  type[KWDBBaseModel], id: str) -> KWDBBaseModel:
        """
        获取文档
        
        Args:
            model: 模型类
            id: 文档ID
        
        Returns:
            KWDBBaseModel: 包含文档字段的模型实例
        """
        ...
    
    def query(self,
              model:  type[KWDBBaseModel],
              top_k: int = 10,
              **filters,
              ) -> list[KWDBBaseModel]:
        """
        查询文档
        
        Args:
            model: 模型类
            top_k: 返回的文档数量
            **filters: 查询过滤条件
        
        Returns:
            list[KWDBBaseModel]: 包含文档字段的模型实例列表
        """
        ...

class WhooshDB:

    def __init__(self, data_dir: str = None) -> None:
        """
        初始化 Whoosh 数据库
        """
        config = get_config()
        self.data_dir = data_dir or config.get("whoosh_kwdb", "data_dir", fallback="./whoosh_data")
        self.analyzer = self.JiebaAnalyzer()
        self.schema = Schema(
            id=ID(stored=True, unique=True),
            content=TEXT(stored=False, analyzer=self.analyzer),
            tags=KEYWORD(stored=False, analyzer=self.analyzer),
            created_at=DATETIME(stored=True),
            updated_at=DATETIME(stored=True),
        )
        pass

    class JiebaAnalyzer(Tokenizer):
        """
        Whoosh 的 Jieba 分词分析器
        """

        def __call__(self,
                     value, positions=False,
                     chars=False,
                     keeporiginal=False,
                     removestops=True,
                     mode='default',
                     **kargs
                     ):
            # value 是传入的原始文本
            tokens = jieba.cut_for_search(value)  # 使用搜索引擎模式
            token = Token()
            for t in tokens:
                token.original = t
                token.text = t
                token.stopped = False
                token.pos = -1
                token.boost = 1.0
                if positions:
                    token.startchar = -1
                    token.endchar = -1
                yield token

    def _get_index(self, cls: type[KWDBBaseModel]) -> index.Index:
        """
        获取索引
        """
        index_name = cls.__indexname__
        index_dir = os.path.join(self.data_dir, index_name)
        print(f"Index dir: {index_dir}")
        if index.exists_in(index_dir):
            print(f"Index {index_name} already exists in {index_dir}")
            return index.open_dir(index_dir)
        print(f"Index {index_name} does not exist in {index_dir}, create it")
        os.makedirs(index_dir, exist_ok=True)
        return index.create_in(index_dir, self.schema)

    def insert(self, data: KWDBBaseModel) -> str:
        """
        插入文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            str: 插入的文档ID
        """
        res = self.get(data.__class__, data.id)
        if res:
            logging.warning(f"Document {data.id} already exists, skip insert")
            return ""
        return self.upsert(data)

    def update(self, data: KWDBBaseModel) -> str:
        """
        更新文档
        """
        res = self.get(data.id)
        if not res:
            logging.warning(f"Document {data.id} does not exist, skip update")
            return ""
        return self.upsert(data)
    
    def upsert(self, data: KWDBBaseModel) -> str:
        """
        插入或更新文档
        """
        index = self._get_index(data)
        writer = index.writer()
        data.created_at = datetime.datetime.now()
        data.updated_at = datetime.datetime.now()
        docs = data.__docs__()
        print(f"Document {docs['id']} does not exist, adding with {docs}")
        writer.update_document(**docs)
        writer.commit()
        res = self.get(data.__class__, data.id)
        print(f"Document {data.id} after upsert: {res}")
        return res.id

    def delete(self, data: KWDBBaseModel) -> bool:
        """
        删除文档
        
        Args:
            data: 包含文档字段的模型实例
        
        Returns:
            bool: 是否删除成功
        """
        index = self._get_index(data.__class__)
        writer = index.writer()
        writer.delete_by_term("id", data.id)
        writer.commit()
        return True

    def get(self, model: type[KWDBBaseModel], id: str) -> KWDBBaseModel:
        """
        获取文档
        
        Args:
            model: 文档模型类
            id: 文档ID
        
        Returns:
            KWDBBaseModel: 包含文档字段的模型实例
        """
        index = self._get_index(model)
        with index.searcher() as searcher:
            res = searcher.document(id=id)
            print(f"Get document {id}: {res}")
            if res:
                data = model()
                data.id = res["id"]
                data.created_at = res["created_at"]
                data.updated_at = res["updated_at"]
                logging.debug(f"Document {id} found: {data}")
                return data
            else:
                logging.debug(f"Document {id} not found")
                return None

    def query(self, model: type[KWDBBaseModel], query: str, tags: List[str] = None) -> List[KWDBBaseModel]:
        """
        查询文档
        
        Args:
            model: 文档模型类
            query: 搜索查询字符串
            tags: 要搜索的标签列表
        
        Returns:
            List[KWDBBaseModel]: 包含文档字段的模型实例列表
        """
        kw_results = []
        query_parser = QueryParser("content", schema=self.schema)
        query = f"content:({query})"
        query = query_parser.parse(query)
        with self._get_index(model).searcher(weighting=BM25F()) as searcher:
            results = searcher.search(query)
            logging.debug(f"Search query: {query}, results: {results}")
            for res in results:
                data = model()
                data.id = res["id"]
                data.created_at = res["created_at"]
                data.updated_at = res["updated_at"]
                kw_results.append(data)
            return kw_results
        
        """
        列出所有文档ID
        """
        with self.index.searcher() as searcher:
            return [hit['id'] for hit in searcher.documents()]

_kwdb_instance: KeywordDB = None

def init():
    global _kwdb_instance
    _kwdb_instance = WhooshDB()

def get_instance() -> KeywordDB:
    global _kwdb_instance
    return _kwdb_instance

if __name__ == "__main__":

    class TestModel(KWDBBaseModel):
        __indexname__ = "test_model"
        name: str = ''
        conf: str = ''
        
        def __init__(self, name: str = "", conf: str = "", tags: List[str] = []):
            super().__init__()
            self.name = name
            self.conf = conf
            self._tags = tags
        
        def __str__(self) -> str:
            return f"TestModel(id={self.id}, name={self.name}, conf={self.conf})"
        
        def content(self) -> str:
            return f"{self.name}: {self.conf}"
        
        def tags(self) -> List[str]:
            return self._tags

        def set_content(self, content: str):
            self._content = content
        
        def set_tags(self, tags: List[str]):
            self._tags = tags

    db = WhooshDB(data_dir="./demo_storage/kwdb")
    test_data = TestModel(name="测试配置文件", conf="我是一个测试的配置文件", tags=["测试", "配置"])
    print(f"test_data: {test_data}")
    test_data_id = db.upsert(test_data)
    test_data_id = test_data.id
    print(f"test_data_id: {test_data_id}")
    
    test_data = db.get(TestModel, test_data_id)
    print(test_data)
    
    test_results = db.query(TestModel, "测试配置文件")
    for test_data in test_results:
        print(test_data)
        ret = db.delete(test_data)
        print(f"Delete test_data {test_data.id} success: {ret}")

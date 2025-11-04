# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-03
# Keyword Searching Database

import logging
import os
import datetime
import jieba
from typing import List, Dict, Any, Protocol
from whoosh import index
from whoosh.analysis import Token, Tokenizer
from whoosh.fields import KEYWORD, Schema, TEXT, ID, DATETIME
from whoosh.scoring import BM25F
from whoosh.qparser import MultifieldParser, QueryParser
from .config import get_instance as get_config


class KeywordDB(Protocol):

    def upsert(self, doc: Dict[str, Any]) -> str:
        """
        插入或更新文档
        """
        ...

    def delete(self, id: str) -> bool:
        """
        删除文档
        """
        ...
    
    def get(self, id: str) -> Dict[str, Any]:
        """
        获取文档
        
        Args:
            id: 文档ID
        
        Returns:
            Dict[str, Any]: 包含文档ID、描述、需求、标签、创建时间的字典
        """
        ...

    def search(self, query: str, tags: List[str] = None) -> List[str]:
        """
        搜索文档
        
        Args:
            query: 搜索查询字符串
            tags: 要搜索的标签列表
        
        Returns:
            List[str]: 包含排名和文档ID的元组列表
        """
        ...
    
    def list(self) -> List[str]:
        """
        获取所有文档
        
        Returns:
            List[str]: 包含所有文档ID的列表
        """
        ...


class WhooshDB:

    def __init__(self) -> None:
        """
        初始化 Whoosh 数据库
        """
        config = get_config()
        self.data_dir = config.get("whoosh_kwdb", "data_dir", fallback="./whoosh_data")
        self.index_name = config.get("whoosh_kwdb", "index_name", fallback="peoples")
        self.index_dir = os.path.join(self.data_dir, self.index_name)
        self.analyzer = self.JiebaAnalyzer()
        self.index = self._get_index()
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

    def _people_schema(self) -> Schema:
        """
        定义People文档的Schema
        """
        return Schema(
            id=ID(stored=True, unique=True),
            description=TEXT(stored=False, analyzer=self.analyzer),
            requirement=TEXT(stored=False, analyzer=self.analyzer),
            tags=KEYWORD(stored=True, commas=True, lowercase=True),
            created_at=DATETIME(stored=True),
        )

    def _get_index(self):
        os.makedirs(self.index_dir, exist_ok=True)
        if index.exists_in(self.index_dir):
            return index.open_dir(self.index_dir)
        return index.create_in(self.index_dir, self._people_schema(), self.index_name)

    def upsert(self, doc: Dict[str, Any]) -> str:
        """
        插入或更新文档
        """
        if "created_at" not in doc:
            doc["created_at"] = datetime.datetime.now()
        writer = self.index.writer()
        if doc.get("id") and self.get(doc["id"]):
            logging.debug(f"Document {doc['id']} already exists, updating with {doc}")
            writer.update_document(**doc)
        else:
            logging.debug(f"Document {doc['id']} does not exist, adding with {doc}")
            writer.add_document(**doc)
        writer.commit()
        res = self.get(doc["id"])
        logging.debug(f"Document {doc['id']} after upsert: {res}")
        return res["id"]

    def delete(self, id: str) -> bool:
        """
        删除文档
        """
        writer = self.index.writer()
        writer.delete_by_term("id", id)
        writer.commit()
        return True

    def get(self, id: str) -> Dict[str, Any]:
        """
        获取文档
        
        Args:
            id: 文档ID
        
        Returns:
            Dict[str, Any]: 包含文档字段的字典
        """
        with self.index.searcher() as searcher:
            return searcher.document(id=id)

    def search(self, query: str, tags: List[str] = None) -> List[str]:
        """
        搜索文档
        
        Args:
            query: 搜索查询字符串
            tags: 要搜索的标签列表
        
        Returns:
            List[str]: 包含排名和文档ID的元组列表
        """
        kw_results = []
        query_parser = MultifieldParser(["description", "tags"], schema=self.index.schema)
        if tags:
            query = f"description:({query})"
            query += f" AND tags:({','.join(tags)})"
        query = query_parser.parse(query)
        with self.index.searcher(weighting=BM25F()) as searcher:
            results = searcher.search(query)
            logging.debug(f"Search query: {query}, results: {results}")
            for rank, hit in enumerate(results):
                kw_results.append((rank, hit['id']))
            return kw_results

    def list(self) -> List[str]:
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
    from .config import init as init_config
    config_file = os.path.join(os.path.dirname(__file__), "../../configuration/test_conf.ini")
    init_config(config_file)

    from .logger import init as init_logger
    init_logger()
    
    init()
    kwdb = get_instance()
    docs = [
        {
            "id": "qianqian-id",
            "description": "茜茜，女性，29岁，身高161厘米，未婚。籍贯成都金堂，民族汉，星座射手座，体重49kg，学历硕士，毕业学校重庆理工大学，工作股份制银行运营，收入20万/年，房车有房(高新区)，家庭背景一家四口，姐姐已婚已育，普通工人家庭，妈妈已经退休，爸爸在车间负责车间生产管理，从小父母身边长大，感情很好，家庭温馨，情感经历有2次的情感经历；最近的一段是异地分开的，对方去外地发展了，性格性格很有趣，身材皮肤身材好，皮肤白皙，习惯有健身的习惯，爱好喜欢跳舞，徒步，桌游，工作地点上班在高新区，休息情况双休，平时偶尔会有加班的情况。",
            "tags": "女,女生,女性,女士,未婚,无婚史",
        },
        {
            "id": "xiangxiansheng-id",
            "description": "向先生，男性，35岁，身高169厘米，离异未育。学历宾夕法尼亚大学博士，祖籍成都，职业中国科学院副教授，收入70W+，房产多套房产公寓商铺（有别墅），车辆有多辆，兴趣爱好看书、阅读、旅行、健身、户外运动，家庭背景父亲曾是房地产开发商，现已退居二线；母亲是公务员，A9家庭，个人资产个人名下有几千万资产，个人性格温文尔雅，谈吐认知都很高。",
            "tags": "男,男生,男性,男士,离异,未育,有婚史",
        },
    ]
    for doc in docs:
        kwdb.upsert(doc)
    results = kwdb.list()
    print(results)
    results = kwdb.search("成都未婚女士")
    print(results)
    results = kwdb.search("成都未婚女士,身高160以上", ["女", "无婚史"])
    print(results)
    for doc in docs:
        kwdb.delete(doc["id"])

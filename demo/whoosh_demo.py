"""
Whoosh 中文全文检索 Demo（使用 jieba 分词）

功能：
- 初始化/创建索引目录与 Schema
- 文档写入、更新、删除
- 多字段搜索、分页、排序与高亮

运行：
- 直接运行此文件：python -m src.utils.whoosh
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD, ID, DATETIME
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.highlight import HtmlFormatter
from whoosh.sorting import FieldFacet
from whoosh.analysis import StandardAnalyzer

# 优先使用 jieba 的 ChineseAnalyzer；不可用时回退到 StandardAnalyzer
try:
    from jieba.analyse import ChineseAnalyzer  # type: ignore
    CHINESE_ANALYZER = ChineseAnalyzer()
except Exception:
    CHINESE_ANALYZER = StandardAnalyzer()


def default_index_dir() -> str:
    """默认索引目录：<repo>/data/whoosh_index"""
    repo_root = Path(__file__).resolve().parents[0]
    idx = repo_root / "whoosh_data" / "whoosh_index"
    return str(idx)


class WhooshIndex:
    def __init__(self, index_dir: Optional[str] = None):
        self.index_dir = index_dir or default_index_dir()
        os.makedirs(self.index_dir, exist_ok=True)
        self.schema = self._get_schema()
        self.ix = self._open_or_create()

    def _get_schema(self) -> Schema:
        return Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=CHINESE_ANALYZER),
            content=TEXT(stored=True, analyzer=CHINESE_ANALYZER),
            tags=KEYWORD(stored=True, commas=True, lowercase=True),
            created_at=DATETIME(stored=True),
        )

    def _open_or_create(self):
        if index.exists_in(self.index_dir):
            return index.open_dir(self.index_dir)
        return index.create_in(self.index_dir, self.schema)

    # ---------------- 文档操作 ----------------
    def add_or_update(self, doc: Dict[str, Any]) -> None:
        """写入或更新文档（以 id 为主键）"""
        # 默认 created_at
        doc = dict(doc)
        if "created_at" not in doc:
            doc["created_at"] = datetime.now()

        writer = self.ix.writer()
        writer.update_document(
            id=str(doc.get("id")),
            title=str(doc.get("title", "")),
            content=str(doc.get("content", "")),
            tags=str(doc.get("tags", "")),
            created_at=doc.get("created_at"),
        )
        writer.commit()

    def delete_by_id(self, doc_id: str) -> int:
        """按 id 删除文档，返回删除条数"""
        writer = self.ix.writer()
        num = writer.delete_by_term("id", str(doc_id))
        writer.commit()
        return num

    # ---------------- 搜索 ----------------
    def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 10,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        多字段搜索 + 分页 + 可选排序 + 高亮。

        Args:
            query: 查询字符串
            page: 页码（1 开始）
            page_size: 每页数量
            fields: 搜索字段，默认 ["title", "content"]
            sort_by: 可选排序字段（例如 "created_at"）
        Returns:
            {total, page, page_size, hits: [{id, title, score, highlight}]}
        """
        fields = fields or ["title", "content"]
        parser = MultifieldParser(fields, schema=self.schema, group=OrGroup)
        q = parser.parse(query)

        facet = FieldFacet(sort_by) if sort_by else None
        with self.ix.searcher() as searcher:
            results = searcher.search_page(
                q, page, pagelen=page_size, sortedby=facet, terms=True
            )
            results.formatter = HtmlFormatter(tagname="em", classname="hit")

            hits = []
            for r in results:
                title_hl = r.highlights("title") or r.get("title", "")
                content_hl = r.highlights("content") or r.get("content", "")
                hits.append(
                    {
                        "id": r["id"],
                        "title": r.get("title"),
                        "score": r.score,
                        "highlight": {
                            "title": title_hl,
                            "content": content_hl,
                        },
                    }
                )

            return {
                "total": results.total,
                "page": page,
                "page_size": page_size,
                "hits": hits,
            }


def example() -> None:
    """构建索引、写入样例数据并执行搜索演示"""
    idx = WhooshIndex()

    # 样例数据
    docs = [
        {
            "id": "1",
            "title": "北京的机器学习工程师",
            "content": "我们正在招聘具备深度学习经验的数据工程师，地点北京。",
            "tags": "ml,python,beijing",
        },
        {
            "id": "2",
            "title": "上海数据分析师岗位",
            "content": "需要熟悉统计学与可视化工具，欢迎投递。",
            "tags": "data,shanghai",
        },
        {
            "id": "3",
            "title": "Python 开发者社区活动",
            "content": "本周末举办 Python 社区技术交流，主题为搜索与索引。",
            "tags": "python,community",
        },
    ]

    for d in docs:
        idx.add_or_update(d)

    # 查询 1：关键词
    r1 = idx.search("北京 数据工程师", page=1, page_size=5)
    print("\n== 查询1：北京 数据工程师 ==")
    print(r1)

    # 查询 2：短语（用引号）
    r2 = idx.search('"机器 学习"', page=1, page_size=5)
    print("\n== 查询2：\"机器 学习\" ==")
    print(r2)

    # 查询 3：按时间排序
    r3 = idx.search("Python 社区", page=1, page_size=5, sort_by="created_at")
    print("\n== 查询3：Python 社区（按时间排序） ==")
    print(r3)


if __name__ == "__main__":
    example()
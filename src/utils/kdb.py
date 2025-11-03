# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-03
# Keyword Searching Database

from typing import List, Optional, Dict, Any  


class BaseIndex:
    __index_name__ = ''
    

class KeywordDB(Protocol):
    
    def upsert(self, doc: BaseIndex) -> bool:
        """
        插入或更新文档
        """
        ...
    
    def delete(self, doc: BaseIndex) -> bool:
        """
        删除文档
        """
        ...
    
    def search(self,
        query: str,
        page: int = 1,
        page_size: int = 10,
        fields: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        ) -> Dict[str, Any]:
        """
        搜索文档
        """
        ...
    
    
    pass
        
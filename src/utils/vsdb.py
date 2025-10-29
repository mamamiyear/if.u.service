import uuid
import chromadb
import logging
from typing import Protocol
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from .config import get_instance as get_config

class VectorDB(Protocol):
    
    def insert(self, metadatas: list[dict], documents: list[str], ids: list[str] = None) -> list[str]:
        """
        插入向量到数据库
        
        Args:
            vector (list[float]): 向量
            metadata (dict): 元数据
        
        Returns:
            bool: 是否插入成功
        """
        ...

    def delete(self, ids: list[str]) -> bool:
        """
        Delete documents from a collection.
        
        Args:
            ids: List of IDs to delete
        
        Returns:
            bool: Whether deletion was successful
        """
        ...

    def query(self, metadatas: dict, ids: list[str], top_k: int = 5) -> list[dict]:
        """
        查询向量数据库
        
        Args:
            query_vector (list[float]): 查询向量
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        ...
    
    def search(self, document: str, metadatas: dict, ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        搜索向量数据库
        
        Args:
            document: Document to search
            metadatas: Metadata to filter by
            ids: List of IDs to filter by
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        ...
        
class ChromaDB:
    def __init__(self, **kwargs):
        """
        Initialize the ChromaDB instance.
        """
        config = get_config()
        self.embedding_functions = embedding_functions.OpenAIEmbeddingFunction(
            api_base=config.get("voc-engine_embedding", "api_url"),
            api_key=config.get("voc-engine_embedding", "api_key"),
            model_name=config.get("voc-engine_embedding", "endpoint"),
        )
        persist_directory = config.get("chroma_vsdb", "database_dir", fallback=None)
        logging.debug(f"persist_directory: {persist_directory}")
        if persist_directory:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.client = chromadb.Client(
                settings=Settings(anonymized_telemetry=False),
            )
        self.collection_name = config.get("chroma_vsdb", "collection_name", fallback="peoples")
        metadata: dict = kwargs.get('collection_metadata', {'hnsw:space': 'cosine'})
        metadata['hnsw:space'] = metadata.get('hnsw:space', 'cosine')
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_functions,
            metadata=metadata,
        )
        
    def insert(self, metadatas: list[dict], documents: list[str], ids: list[str] = None) -> list[str]:
        """
        Insert documents into a collection.
        
        Args:
            metadatas: List of metadata corresponding to each document
            documents: List of documents to insert
            ids: Optional list of unique IDs for each document. If None, IDs will be generated.
        
        Returns:
            list[str]: List of inserted IDs
        """
        
        if not ids:
            # Generate unique IDs if not provided
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return ids
    
    def delete(self, ids: list[str]) -> bool:
        """
        Delete documents from a collection.
        
        Args:
            ids: List of IDs to delete
        
        Returns:
            bool: Whether deletion was successful
        """
        try:
            self.collection.delete(ids)
            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def query(self, metadatas: dict, ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        查询向量数据库
        
        Args:
            metadatas: Metadata to filter by
            ids: List of IDs to query
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        results = self.collection.query(
            query_embeddings=None,
            query_texts=None,
            n_results=top_k,
            where=metadatas,
            ids=ids,
            include=["documents", "metadatas", "distances"],
        )
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                'id': results['ids'][0][i],
                'distance': results['distances'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                'document': results['documents'][0][i] if results['documents'][0] else ''
            }
            formatted_results.append(result)
        return formatted_results
    
    def search(self, document: str, metadatas: dict, ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        搜索向量数据库
        
        Args:
            document: Document to search
            metadatas: Metadata to filter by
            ids: List of IDs to filter by
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        results = self.collection.query(
            query_embeddings=None,
            query_texts=[document],
            n_results=top_k,
            where=metadatas if metadatas else None,
            ids=ids,
            include=["documents", "metadatas", "distances"],
        )
        formatted_results = []
        for i in range(len(results['ids'][0])):
            logging.info(f"result id: {results['ids'][0][i]}, distance: {results['distances'][0][i]}")
            result = {
                'id': results['ids'][0][i],
                'distance': results['distances'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                'document': results['documents'][0][i] if results['documents'][0] else ''
            }
            formatted_results.append(result)
        return formatted_results
    pass

_vsdb_instance: VectorDB = None

def init():
    global _vsdb_instance
    _vsdb_instance = ChromaDB()

def get_instance() -> VectorDB:
    global _vsdb_instance
    return _vsdb_instance


if __name__ == "__main__":
    import os
    
    from logger import init as init_logger
    init_logger(log_dir="logs", log_file="test", log_level=logging.INFO, console_log_level=logging.DEBUG)
    
    from config import init as init_config
    config_file = os.path.join(os.path.dirname(__file__), "../../configuration/test_conf.ini")
    init_config(config_file)
    
    init()
    vsdb = get_instance()
    metadatas = [
        {'name': '丽丽'},
        {'name': '志刚'},
        {'name': '张三'},
        {'name': '李四'},
    ]
    documents = [
        '姓名: 丽丽, 性别: 女, 年龄: 23, 爱好: 爬山、骑行、攀岩、跳伞、蹦极',
        "姓名: 志刚, 性别: 男, 年龄: 25, 爱好: 读书、游戏",
        "姓名: 张三, 性别: 男, 年龄: 30, 爱好: 画画、写作、阅读、逛展、旅行",
        "姓名: 李四, 性别: 男, 年龄: 35, 爱好: 做饭、美食、旅游"
    ]
    search_text = '25岁以下的'
    ids = vsdb.insert(metadatas, documents)
    results = vsdb.search(search_text, None, None, top_k=4)
    for result in results:
        print(result['document'], ' ', result['distance'])

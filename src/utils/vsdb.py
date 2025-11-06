# -*- coding: utf-8 -*-
# created by mmmy on 2025-11-03
# Vector Searching Database

from abc import abstractmethod
import time
import uuid
import chromadb
import logging
from typing import Protocol
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from overrides import override
from .config import get_instance as get_config

class VSDBBaseModel:
    __collection__: str = None
    id: str = None
    created_at: float = None
    updated_at: float = None
    
    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())
        self.created_at = time.time()
        self.updated_at = time.time()
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def __meta__(self) -> dict:
        fields = [field for field in self.__dict__ if not field.startswith('_')]
        fields.remove("id") if "id" in fields else None
        fields.remove("created_at") if "created_at" in fields else None
        fields.remove("updated_at") if "updated_at" in fields else None
        metadata = {f: getattr(self, f) for f in fields}
        return metadata
    
    def __docs__(self) -> str:
        field_values = [f"{field}={getattr(self, field)}" for field in self.__meta__()]
        return "; ".join(field_values)
    
    @abstractmethod
    def set_document(self, document: str):
        ...
    
    @abstractmethod
    def set_metadata(self, metadata: dict):
        ...
    
    @abstractmethod
    def set_distance(self, distance: float):
        ...

class VectorDB(Protocol):

    def insert(self, data: VSDBBaseModel) -> str:
        ...
    
    def update(self, data: VSDBBaseModel) -> str:
        ...
    
    def upsert(self, data: VSDBBaseModel) -> str:
        ...
    
    def delete(self, data: VSDBBaseModel) -> str:
        ...
    
    def get(self,
            model:  type[VSDBBaseModel],
            id: str,
            ) -> VSDBBaseModel:
        ...
    
    def query(self,
              model:  type[VSDBBaseModel],
              top_k: int = 10,
              **filters,
              ) -> list[VSDBBaseModel]:
        ...

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

    def query(self, metadatas: dict = {}, ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        查询向量数据库
        
        Args:
            query_vector (list[float]): 查询向量
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        ...
    
    def get(self, ids: list[str] = None) -> list[dict]:
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
    def __init__(self, api_url: str = None, api_key: str = None, endpoint: str = None, database_dir: str = None, **kwargs):
        """
        Initialize the ChromaDB instance.
        """
        config = get_config()
        embedding_api_url = api_url if api_url else config.get("voc-engine_embedding", "api_url")
        embedding_api_key = api_key if api_key else config.get("voc-engine_embedding", "api_key")
        embedding_endpoint = endpoint if endpoint else config.get("voc-engine_embedding", "endpoint")
        persist_directory = database_dir if database_dir else config.get("chroma_vsdb", "database_dir", fallback=None)
        
        logging.info(f"chroma db init with api_url     : {embedding_api_url}")
        logging.info(f"chroma db init with api_key     : {embedding_api_key}")
        logging.info(f"chroma db init with endpoint    : {embedding_endpoint}")
        logging.info(f"chroma db init with database_dir: {persist_directory}")
        
        self.embedding_functions = embedding_functions.OpenAIEmbeddingFunction(
            api_base=embedding_api_url,
            api_key=embedding_api_key,
            model_name=embedding_endpoint,
        )
        self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            ) if persist_directory else chromadb.Client(
                settings=Settings(anonymized_telemetry=False),
            )
            
        # self.collection_name = config.get("chroma_vsdb", "collection_name", fallback="peoples")
        # metadata: dict = kwargs.get('collection_metadata', {'hnsw:space': 'cosine'})
        # metadata['hnsw:space'] = metadata.get('hnsw:space', 'cosine')
        # self.collection = self.client.get_or_create_collection(
            # name=self.collection_name,
            # embedding_function=self.embedding_functions,
            # metadata=metadata,
        # )

        self.collections: Dict[str, chromadb.Collection] = {}
        
    def get_collection(self, collection_name: str = None, metadata: dict = None) -> chromadb.Collection:
        """
        Get a collection by name.
        
        Args:
            collection_name: Name of the collection to retrieve. Defaults to the instance's collection.
        
        Returns:
            chromadb.Collection: The requested collection object.
        """
        if collection_name not in self.collections:
            metadata = metadata or {}
            metadata['hnsw:space'] = metadata.get('hnsw:space', 'cosine')
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_functions,
                metadata=metadata,
            )
        return self.collections[collection_name]

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
    
    def query(self, metadatas: dict= {}, ids: list[str] = None, top_k: int = 5) -> list[dict]:
        """
        查询向量数据库
        
        Args:
            metadatas: Metadata to filter by
            ids: List of IDs to query
            top_k (int, optional): 返回Top K结果. Defaults to 5.
        
        Returns:
            list[dict]: 查询结果列表
        """
        logging.info(f"query metadatas: {metadatas}, ids: {ids}, top_k: {top_k}")
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
    
    def get(self, ids: list[str] = None) -> list[dict]:
        results = self.collection.get(ids=ids, include=["documents", "metadatas"])
        logging.info(f"results: {results}")
        formatted_results = []
        for i in range(len(results['ids'])):
            result = {
                'id': results['ids'][i],
                'metadata': results['metadatas'][i] if results['metadatas'][i] else {},
                'document': results['documents'][i] if results['documents'][i] else ''
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
    # >>>>>>> new methods >>>>>>>
    def insert(self, data: VSDBBaseModel) -> str:
        collection = self.get_collection(data.__collection__)
        collection.add(
            ids=[data.id],
            documents=[data.__docs__()],
            metadatas=[data.__meta__()],
        )
        return data.id

    def update(self, data: VSDBBaseModel) -> str:
        collection = self.get_collection(data.__collection__)
        collection.update(
            ids=[data.id],
            documents=[data.__docs__()],
            metadatas=[data.__meta__()],
        )
        return data.id
    
    def upsert(self, data: VSDBBaseModel) -> str:
        collection = self.get_collection(data.__collection__)
        collection.upsert(
            ids=[data.id],
            documents=[data.__docs__()],
            metadatas=[data.__meta__()],
        )
        return data.id
    
    def delete(self, data: VSDBBaseModel) -> str:
        collection = self.get_collection(data.__collection__)
        collection.delete(ids=[data.id])
        return data.id
    
    def get(self,
            model: type[VSDBBaseModel],
            id: str,
            ) -> VSDBBaseModel:
        data = model()
        collection = self.get_collection(model.__collection__)
        results = collection.get(ids=[id], include=["documents", "metadatas"])
        if results['ids']:
            data.id = results['ids'][0]
            data.set_document(results['documents'][0])
            data.set_metadata(results['metadatas'][0])
            return data
        return None
    
    def query(self,
              model: type[VSDBBaseModel],
              query: str,
              top_k: int = 10,
              **filters,
              ) -> list[VSDBBaseModel]:
        collection = self.get_collection(model.__collection__)
        results = collection.query(
            query_texts=[query] if query else None,
            n_results=top_k,
            where=filters if filters else None,
            include=["documents", "metadatas", "distances"],
        )
        formatted_results = []
        for i in range(len(results['ids'][0])):
            logging.info(f"result id: {results['ids'][0][i]}, distance: {results['distances'][0][i]}")
            data = model()
            data.id = results['ids'][0][i]
            data.set_document(results['documents'][0][i])
            data.set_metadata(results['metadatas'][0][i])
            data.set_distance(results['distances'][0][i])
            formatted_results.append(data)
        return formatted_results

_vsdb_instance: VectorDB = None

def init(api_url: str = None, api_key: str = None, endpoint: str = None, persist_directory: str = None):
    global _vsdb_instance
    _vsdb_instance = ChromaDB(api_url, api_key, endpoint, persist_directory)

def get_instance() -> VectorDB:
    global _vsdb_instance
    return _vsdb_instance


if __name__ == "__main__":

    class TestModel(VSDBBaseModel):
        __collection__ = 'test'
        name: str = ''
        conf: str = ''
        document: str = ''
        metadata: dict = {}
        distance: float = 0.0
        @override
        def __meta__(self) -> dict:
            fields = [field for field in self.__dict__ if not field.startswith('_')]
            metadata = {f: getattr(self, f) for f in fields}
            return metadata
        @override
        def __docs__(self) -> str:
            return f"这个配置项的名字是: {self.name}; 配置的内容是: {self.conf}"
        @override
        def set_document(self, document: str):
            self.document = document
        @override
        def set_metadata(self, metadata: dict):
            self.metadata = metadata
        @override
        def set_distance(self, distance: float):
            self.distance = distance
        def __str__(self) -> str:
            return f"TestModel(id={self.id}, name={self.name}, conf={self.conf}, document={self.document}, metadata={self.metadata}, distance={self.distance})"
    
    init(api_url = "https://ark.cn-beijing.volces.com/api/v3",
         api_key = "fff0b009-78a5-4d58-ad0e-a5ca284df7b5",
         endpoint = "ep-20250928142122-twlqb",
         persist_directory = "./localstore/testdb")
    db = get_instance()
    
    test_data = TestModel(name='test', conf='test')
    test_data_id = db.insert(test_data)
    print(test_data_id)
    
    get_test_data = db.get(TestModel, test_data_id)
    print(get_test_data)
    
    query_test_datas = db.query(TestModel, query='test')
    for query_data in query_test_datas:
        print(query_data)
        del_test_data_id = db.delete(query_data)
        print(del_test_data_id)

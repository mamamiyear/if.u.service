import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.config import get_instance as get_config
from utils.vsdb import VectorDB, get_instance as get_vsdb
from utils.obs import OBS, get_instance as get_obs

from models.people import People

people_store = None
Base = declarative_base()
class PeopleORM(Base):
    __tablename__ = 'peoples'
    id = Column(String(36), primary_key=True)
    name = Column(String(255), index=True)
    contact = Column(String(255), index=True)
    gender = Column(String(10))
    age = Column(Integer)
    height = Column(Integer)
    marital_status = Column(String(20))
    match_requirement = Column(Text)
    introduction = Column(Text)
    comments = Column(Text)
    cover = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    def parse_from_people(self, people: People):
        self.id = people.id
        self.name = people.name
        self.contact = people.contact
        self.gender = people.gender
        self.age = people.age
        self.height = people.height
        self.marital_status = people.marital_status
        self.match_requirement = people.match_requirement
        # 将字典类型字段序列化为JSON字符串存储
        self.introduction = json.dumps(people.introduction, ensure_ascii=False)
        self.comments = json.dumps(people.comments, ensure_ascii=False)
        self.cover = people.cover
    
    def to_people(self) -> People:
        people = People()
        people.id = self.id
        people.name = self.name
        people.contact = self.contact
        people.gender = self.gender
        people.age = self.age
        people.height = self.height
        people.marital_status = self.marital_status
        people.match_requirement = self.match_requirement
        # 将JSON字符串反序列化为字典类型字段
        try:
            people.introduction = json.loads(self.introduction) if self.introduction else {}
        except (json.JSONDecodeError, TypeError):
            people.introduction = {}
        
        try:
            people.comments = json.loads(self.comments) if self.comments else {}
        except (json.JSONDecodeError, TypeError):
            people.comments = {}

        people.cover = self.cover
        return people

class PeopleStore:
    def __init__(self):
        config = get_config()
        self.sqldb_engine = create_engine(config.get("sqlalchemy", "database_dsn"))
        Base.metadata.create_all(self.sqldb_engine)
        self.session_maker = sessionmaker(bind=self.sqldb_engine)
        self.vsdb: VectorDB = get_vsdb()
        self.obs: OBS = get_obs()
    
    def save(self, people: People) -> str:
        """
        保存人物到数据库和向量数据库
        
        :param people: 人物对象
        :return: 人物ID
        """
        # 0. 生成 people id
        people.id = people.id if people.id else uuid.uuid4().hex
        
        # 1. 转换模型，并保存到 SQL 数据库
        people_orm = PeopleORM()
        people_orm.parse_from_people(people)
        with self.session_maker() as session:
            session.add(people_orm)
            session.commit()
        
        # 2. 保存到向量数据库
        people_metadata = people.to_vs_meta()
        people_document = people.to_vs_text()
        logging.info(f"people: {people}")
        logging.info(f"people_metadata: {people_metadata}")
        logging.info(f"people_document: {people_document}")
        results = self.vsdb.insert(metadatas=[people_metadata], documents=[people_document], ids=[people.id])
        logging.info(f"results: {results}")
        if len(results) == 0:
            raise Exception("insert failed")
        
        # 3. 保存到 OBS 存储
        people_dict = people.to_dict()
        people_json = json.dumps(people_dict, ensure_ascii=False)
        obs_url = self.obs.Put(f"peoples/{people.id}/detail.json", people_json.encode('utf-8'))
        logging.info(f"obs_url: {obs_url}")
        
        return people.id
    
    def update(self, people: People) -> None:
        raise Exception("update not implemented")
        return None
    
    def find(self, people_id: str) -> People:
        """
        根据人物ID查询人物
        
        :param people_id: 人物ID
        :return: 人物对象
        """
        with self.session_maker() as session:
            people_orm = session.query(PeopleORM).filter(
                PeopleORM.id == people_id,
                PeopleORM.deleted_at.is_(None)
            ).first()
            if not people_orm:
                raise Exception(f"people not found, people_id: {people_id}")
        return people_orm.to_people()
    
    def query(self, conds: dict = {}, limit: int = 10, offset: int = 0) -> list[People]:
        """
        根据查询条件查询人物
        
        :param conds: 查询条件字典
        :param limit: 分页大小
        :param offset: 分页偏移量
        :return: 人物对象列表
        """
        if conds is None:
            conds = {}
        with self.session_maker() as session:
            people_orms = session.query(PeopleORM).filter_by(**conds).filter(
                PeopleORM.deleted_at.is_(None)
            ).limit(limit).offset(offset).all()
            people_orms.sort(key=lambda orm: orm.created_at, reverse=True)
            return [people_orm.to_people() for people_orm in people_orms]
    
    def search(self, search: str, metadatas: dict, ids: list[str] = None, top_k: int = 5) -> list[People]:
        """
        根据搜索内容和查询条件查询人物
        
        :param search: 搜索内容
        :param metadatas: 查询条件字典
        :param ids: 可选的人物ID列表，用于过滤结果
        :param top_k: 返回结果数量
        :return: 人物对象列表
        """
        peoples = []
        results = self.vsdb.search(document=search, metadatas=metadatas, ids=ids, top_k=top_k)
        logging.info(f"results: {results}")
        people_id_list = []
        for result in results:
            people_id = result.get('id', '')
            if not people_id:
                continue
            people_id_list.append(people_id)
        logging.info(f"people_id_list: {people_id_list}")
        with self.session_maker() as session:
            people_orms = session.query(PeopleORM).filter(PeopleORM.id.in_(people_id_list)).filter(
                PeopleORM.deleted_at.is_(None)
            ).all()
            people_orms.sort(key=lambda orm: orm.created_at, reverse=True)
        
        # 根据 people_id_list 的顺序对查询结果进行排序
        order_map = {pid: idx for idx, pid in enumerate(people_id_list)}
        people_orms.sort(key=lambda orm: order_map.get(orm.id, len(order_map)))
        for people_orm in people_orms:
            people = people_orm.to_people()
            peoples.append(people)
        return peoples
    
    def delete(self, people_id: str) -> None:
        """
        删除人物从数据库和向量数据库
        
        :param people_id: 人物ID
        """
        # 1. 从 SQL 数据库软删除人物
        with self.session_maker() as session:
            session.query(PeopleORM).filter(
                PeopleORM.id == people_id,
                PeopleORM.deleted_at.is_(None)
            ).update({PeopleORM.deleted_at: func.now()}, synchronize_session=False)
            session.commit()
            logging.info(f"人物 {people_id} 标记删除 SQL 成功")
            
        # 2. 删除向量数据库中的记录
        self.vsdb.delete(ids=[people_id])
        logging.info(f"人物 {people_id} 删除向量数据库成功")
        
        # 3. 删除 OBS 存储中的文件
        keys = self.obs.List(f"peoples/{people_id}/")
        for key in keys:
            self.obs.Del(key)
            logging.info(f"文件 {key} 删除 OBS 成功")

def init():
    global people_store
    people_store = PeopleStore()


def get_instance() -> PeopleStore:
    return people_store

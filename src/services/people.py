


import uuid
from models.people import People, PeopleRLDBModel
from utils.error import error
from utils import rldb


class PeopleService:
    def __init__(self):
        self.rldb = rldb.get_instance()

    def save(self, people: People) -> (str, error):
        """
        保存人物到数据库和向量数据库
        
        :param people: 人物对象
        :return: 人物ID
        """
        # 0. 生成 people id
        people.id = people.id if people.id else uuid.uuid4().hex
        
        # 1. 转换模型，并保存到 SQL 数据库
        people_orm = people.to_rldb_model()
        self.rldb.upsert(people_orm)
        
        return people.id, error(0, "")
    
    def delete(self, people_id: str) -> error:
        """
        删除人物从数据库和向量数据库
        
        :param people_id: 人物ID
        :return: 错误对象
        """
        people_orm = self.rldb.get(PeopleRLDBModel, people_id)
        if not people_orm:
            return error(1, f"people {people_id} not found")
        self.rldb.delete(people_orm)
        return error(0, "")
    
    def list(self, conds: dict = {}, limit: int = 10, offset: int = 0) -> (list[People], error):
        """
        从数据库列出人物
        
        :param conds: 查询条件字典
        :param limit: 分页大小
        :param offset: 分页偏移量
        :return: 人物对象列表
        """
        people_orms = self.rldb.query(PeopleRLDBModel, **conds)
        peoples = [People.from_rldb_model(people_orm) for people_orm in people_orms]
        
        return peoples, error(0, "")

people_service = None

def init():
    global people_service
    people_service = PeopleService()

def get_instance() -> PeopleService:
    return people_service
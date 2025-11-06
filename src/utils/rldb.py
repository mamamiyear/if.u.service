
from typing import Protocol
import uuid
from sqlalchemy import Column, DateTime, String, create_engine, func, or_
from sqlalchemy.orm import declarative_base, sessionmaker

SQLAlchemyBase = declarative_base()


class RLDBBaseModel(SQLAlchemyBase):
    __abstract__ = True
    id = Column(String(36), primary_key=True, default=lambda: uuid.uuid4().hex)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    def __str__(self) -> str:
        # 遍历所有的field，打印出所有的field和value, id 永远排在第一, 三个时间戳排在最后, 其余字段按定义顺序排序
        fields = [field for field in self.__dict__ if not field.startswith('_')]
        fields.remove("id") if "id" in fields else None
        fields.remove("created_at") if "created_at" in fields else None
        fields.remove("updated_at") if "updated_at" in fields else None
        fields.remove("deleted_at") if "deleted_at" in fields else None
        fields = ["id"] + fields + ["created_at", "updated_at", "deleted_at"]
        field_values = [f"{field}={getattr(self, field)}" for field in fields]
        return f"{self.__class__.__name__}({', '.join(field_values)})"


class RelationalDB(Protocol):
    def insert(self, data: RLDBBaseModel) -> str:
        ...

    def update(self, data: RLDBBaseModel) -> str:
        ...

    def upsert(self, data: RLDBBaseModel) -> str:
        ...

    def delete(self, data: RLDBBaseModel) -> str:
        ...

    def get(self,
            model:  type[RLDBBaseModel],
            id: str,
            include_deleted: bool = False
            ) -> RLDBBaseModel:
        ...

    def query(self,
             model: type[RLDBBaseModel],
             include_deleted: bool = False,
             limit: int = 10,
             offset: int = 0,
             **filters
             ) -> list[RLDBBaseModel]:
        ...


class SqlAlchemyDB():
    def __init__(self, dsn: str = None) -> None:
        dsn = dsn if dsn else config.get("sqlalchemy", "database_dsn")
        self.sqldb_engine = create_engine(dsn)
        SQLAlchemyBase.metadata.create_all(self.sqldb_engine)
        self.session_maker = sessionmaker(bind=self.sqldb_engine)

    def insert(self, data: RLDBBaseModel) -> str:
        with self.session_maker() as session:
            session.add(data)
            session.commit()
            return data.id

    def update(self, data: RLDBBaseModel) -> str:
        with self.session_maker() as session:
            session.merge(data)
            session.commit()
            return data.id

    def upsert(self, data: RLDBBaseModel) -> str:
        existed = data.id and data.id != "" and self.get(data.__class__, data.id) is not None
        with self.session_maker() as session:
            session.merge(data) if existed else session.add(data)
            session.commit()
            return data.id

    def delete(self, data: RLDBBaseModel) -> str:
        with self.session_maker() as session:
            session.delete(data)
            session.commit()
            return data.id

    def get(self,
            model: type[RLDBBaseModel],
            id: str,
            ) -> RLDBBaseModel:
        with self.session_maker() as session:
            sel = session.query(model)
            sel = sel.filter(model.id == id)
            sel = sel.filter(model.deleted_at.is_(None))
            result = sel.first()
        return result

    def query(self,
             model: type[RLDBBaseModel],
             limit: int = 10,
             offset: int = 0,
             **filters
             ) -> list[RLDBBaseModel]:
        results: list[RLDBBaseModel] = []
        with self.session_maker() as session:
            sel = session.query(model)
            sel = sel.filter(model.deleted_at.is_(None))
            if filters:
                sel = sel.filter_by(**filters)
            if limit:
                sel = sel.limit(limit)
            if offset:
                sel = sel.offset(offset)
            results = sel.all()
            results.sort(key=lambda x: x.created_at, reverse=True)
        return results

_rldb_instance: RelationalDB = None

def init(type: str = "sqlalchemy", dsn: str = None):
    global _rldb_instance
    if type == "sqlalchemy":
        _rldb_instance = SqlAlchemyDB(dsn)
    else:
        raise ValueError(f"RelationalDB type {type} not supported")

def get_instance() -> RelationalDB:
    global _rldb_instance
    return _rldb_instance

if __name__ == "__main__":
    class TestModel(RLDBBaseModel):
        __tablename__ = "test_model"
        name = Column(String(36), nullable=True)
        conf = Column(String(96), nullable=True)
    init("sqlalchemy", dsn="sqlite:///./localstorage/test.db")
    db = get_instance()
    
    test_data = TestModel(name="test", conf="test.config")
    print(f"before insert: {test_data}")
    ret = db.insert(test_data)
    print(f"after insert: {test_data}")
    
    print(f"before update: {test_data}")
    test_data.conf = "test.config.new"
    ret = db.update(test_data)
    print(f"after update: {test_data}")
    
    test2_data = TestModel(name="test", conf="test2.config")
    print(f"before upsert: {test2_data}")
    ret = db.upsert(test2_data)
    print(f"after upsert: {test2_data}")
    
    get_data = db.get(TestModel, test_data.id)
    print(f"get data: {get_data}")

    query_data = db.query(TestModel, name="test")
    for data in query_data:
        print(data.id, data.name, data.conf)
        print(f"query data: {data}")
        ret = db.delete(data)
        print(f"delete data.id: {ret}")

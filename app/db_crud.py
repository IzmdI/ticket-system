from typing import Optional, Union

from redis import Redis
from sqlalchemy.orm import Session

from app.db_models import Comment, Ticket


Model = Union[Ticket, Comment]


class CRUDBase:
    def __init__(self, model: Model):
        self.model = model

    def create(self, db: Session, **kwargs) -> Model:
        obj = self.model(**kwargs)  # noqa
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def get(self, db: Session, obj_id: int) -> Optional[Model]:
        return db.query(self.model).filter(self.model.id == obj_id).first()

    @staticmethod
    def update(db: Session, obj: Model, **kwargs) -> Model:
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj

    def remove(
        self, db: Session, obj_id: int, redis_client: Redis, match_str: str
    ) -> int:
        obj = self.get(obj_id=obj_id)
        db.delete(obj)
        db.commit()
        redis_client.delete(*redis_client.scan(match=match_str)[-1])
        return obj.id


crud_ticket = CRUDBase(Ticket)  # noqa
crud_comment = CRUDBase(Comment)  # noqa
